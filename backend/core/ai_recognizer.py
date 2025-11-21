"""
AI识别引擎
使用OpenAI兼容的API进行图像识别
"""
import base64
import json
import requests
from typing import Dict, Any, List, Optional
from loguru import logger
import cv2
import numpy as np


class AIRecognizer:
    """AI识别引擎"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化AI识别器
        
        Args:
            config: AI配置字典
        """
        self.config = config
        self.enabled = config.get('enabled', False)
        self.providers = {p['id']: p for p in config.get('providers', [])}
        self.models = {m['id']: m for m in config.get('models', [])}
        self.active_model_id = config.get('active_model_id')
        
        logger.info(f"AIRecognizer initialized, enabled={self.enabled}, active_model={self.active_model_id}")
    
    def is_available(self) -> bool:
        """检查AI识别是否可用"""
        if not self.enabled:
            return False
        
        if not self.active_model_id:
            return False
        
        model = self.models.get(self.active_model_id)
        if not model:
            return False
        
        provider = self.providers.get(model['provider_id'])
        if not provider or not provider.get('enabled'):
            return False
        
        if not provider.get('api_key'):
            return False
        
        return True
    
    def encode_image(self, image: np.ndarray) -> str:
        """
        将图像编码为base64字符串
        
        Args:
            image: OpenCV图像
            
        Returns:
            base64编码的图像字符串
        """
        # 转换为JPEG格式
        success, buffer = cv2.imencode('.jpg', image)
        if not success:
            raise Exception("Failed to encode image")
        
        # 转换为base64
        base64_str = base64.b64encode(buffer).decode('utf-8')
        return base64_str
    
    def recognize(self, image: np.ndarray, stream: bool = False):
        """
        使用AI识别图像
        
        Args:
            image: 输入图像
            stream: 是否流式返回
            
        Returns:
            识别结果字典或生成器
        """
        if not self.is_available():
            raise Exception("AI识别功能不可用,请检查配置")
        
        model = self.models[self.active_model_id]
        provider = self.providers[model['provider_id']]
        
        logger.info(f"Using AI model: {model['name']} ({model['model_name']}), stream={stream}")
        
        # 编码图像
        base64_image = self.encode_image(image)
        
        # 构建请求
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {provider['api_key']}"
        }
        
        messages = [
            {
                "role": "system",
                "content": model['system_prompt']
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": model['user_prompt']
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ]
        
        payload = {
            "model": model['model_name'],
            "messages": messages,
            "max_tokens": model.get('max_tokens', 4096),
            "temperature": model.get('temperature', 0.2),
            "stream": stream
        }
        
        logger.debug(f"Request payload (without image): model={payload['model']}, temperature={payload['temperature']}, max_tokens={payload['max_tokens']}, stream={stream}")
        
        # 发送请求
        try:
            # 如果api_base已经包含/chat/completions,直接使用;否则添加
            api_base = provider['api_base'].rstrip('/')
            if api_base.endswith('/chat/completions'):
                api_url = api_base
            else:
                api_url = f"{api_base}/chat/completions"
            logger.debug(f"Calling AI API: {api_url}")
            
            response = requests.post(
                api_url,
                headers=headers,
                json=payload,
                timeout=60,
                stream=stream
            )
            
            response.raise_for_status()
            
            if stream:
                # 返回生成器
                return self._stream_response(response)
            else:
                # 非流式，返回完整结果
                result = response.json()
                
                # 解析响应
                content = result['choices'][0]['message']['content']
                logger.debug(f"AI response: {content}")
                
                # 尝试解析JSON
                try:
                    # 提取JSON部分
                    if '```json' in content:
                        content = content.split('```json')[1].split('```')[0].strip()
                    elif '```' in content:
                        content = content.split('```')[1].split('```')[0].strip()
                    
                    parsed_result = json.loads(content)
                    return self._format_result(parsed_result)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse AI response as JSON: {e}")
                    # 返回原始文本
                    return {
                        "barcodes": [],
                        "texts": [{"text": content, "position": {"x": 0, "y": 0, "width": 0, "height": 0}}],
                        "raw_response": content
                    }
        
        except requests.exceptions.RequestException as e:
            logger.error(f"AI API request failed: {e}")
            # 尝试获取详细错误信息
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    logger.error(f"API error detail: {error_detail}")
                except:
                    logger.error(f"API response text: {e.response.text}")
            raise Exception(f"AI识别请求失败: {str(e)}")
    
    def _stream_response(self, response):
        """
        处理流式响应
        
        Args:
            response: requests响应对象
            
        Yields:
            每个数据块
        """
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data = line[6:]
                    if data == '[DONE]':
                        break
                    try:
                        chunk = json.loads(data)
                        delta = chunk['choices'][0]['delta']
                        if 'content' in delta:
                            yield delta['content']
                    except json.JSONDecodeError:
                        continue
    
    def _format_result(self, parsed_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        格式化AI识别结果
        
        Args:
            parsed_result: AI返回的解析结果
            
        Returns:
            标准格式的识别结果
        """
        formatted = {
            "barcodes": [],
            "texts": [],
            "raw_response": parsed_result
        }
        
        # 处理条码
        for idx, bc in enumerate(parsed_result.get('barcodes', [])):
            barcode = {
                "barcode_data": bc.get('data', ''),
                "barcode_type": bc.get('type', 'UNKNOWN'),
                "position": bc.get('position', {"x": 0, "y": idx * 100, "width": 100, "height": 50})
            }
            formatted["barcodes"].append(barcode)
        
        # 处理文字
        for idx, txt in enumerate(parsed_result.get('texts', [])):
            text = {
                "text": txt.get('text', ''),
                "position": txt.get('position', {"x": 0, "y": idx * 30, "width": 100, "height": 20}),
                "confidence": txt.get('confidence', 1.0)
            }
            formatted["texts"].append(text)
        
        return formatted
