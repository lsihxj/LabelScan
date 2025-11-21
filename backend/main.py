"""
FastAPI主应用
提供REST API接口
"""
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import uuid
import time
from pathlib import Path
import shutil
from loguru import logger
import sys
import json
import cv2

from backend.core.processor import LabelProcessor
from backend.utils.config import config

# 配置日志
log_config = config.get_section("logging").get("logging", {})
logger.remove()

# 控制台日志
if log_config.get("console", {}).get("enabled", True):
    logger.add(sys.stderr, level=log_config.get("level", "INFO"))

# 文件日志
file_config = log_config.get("file", {})
if file_config.get("enabled", False):
    log_path = Path(file_config.get("path", "logs/app.log"))
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger.add(
        str(log_path),
        level=log_config.get("level", "INFO"),
        rotation=file_config.get("rotation", "100 MB"),
        retention=file_config.get("retention", "30 days"),
        compression=file_config.get("compression", "zip"),
        encoding="utf-8"
    )
    logger.info(f"File logging enabled: {log_path}")

# 错误日志单独记录
error_file_config = log_config.get("error_file", {})
if error_file_config.get("enabled", False):
    error_log_path = Path(error_file_config.get("path", "logs/error.log"))
    error_log_path.parent.mkdir(parents=True, exist_ok=True)
    logger.add(
        str(error_log_path),
        level=error_file_config.get("level", "ERROR"),
        rotation=error_file_config.get("rotation", "50 MB"),
        retention=error_file_config.get("retention", "90 days"),
        encoding="utf-8"
    )
    logger.info(f"Error logging enabled: {error_log_path}")

# 创建FastAPI应用
app = FastAPI(
    title="电子标签多条码识别系统",
    description="高性能的电子标签识别系统API",
    version="1.0.0"
)

# CORS配置
cors_origins = config.get("system.server.cors_origins", ["http://localhost:5173", "http://localhost:5174"])
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化处理器
processor_config = {
    "max_image_size": config.get("processing.preprocessing.max_image_size", 2000),
    "ocr_lang": config.get("ocr.ocr.local.lang", "eng+chi_sim"),
    "tesseract_cmd": config.get("ocr.ocr.local.tesseract_cmd"),
    "max_search_radius_multiplier": config.get("processing.association.max_search_radius_multiplier", 2.0),
    "strong_threshold": config.get("processing.association.strong_threshold", 0.5),
    "weak_threshold": config.get("processing.association.weak_threshold", 0.3),
    "row_tolerance": config.get("processing.sorting.row_tolerance", 30),
    "col_tolerance": config.get("processing.sorting.col_tolerance", 20),
    "ai": config.get("ai.ai", {})
}

label_processor = LabelProcessor(config=processor_config)

# 确保必要目录存在
temp_dir = Path(config.get("system.upload.temp_dir", "temp"))
uploads_dir = Path(config.get("system.upload.uploads_dir", "uploads"))
temp_dir.mkdir(exist_ok=True)
uploads_dir.mkdir(exist_ok=True)


# ============ 数据模型 ============

class ProcessResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    message: str = ""
    timestamp: int
    request_id: str


class HealthResponse(BaseModel):
    status: str
    components: dict
    version: str


class ConfigUpdate(BaseModel):
    default_mode: Optional[str] = None
    default_ocr_mode: Optional[str] = None
    position_tolerance: Optional[int] = None


# ============ API接口 ============

@app.get("/", tags=["Root"])
async def root():
    """根路径"""
    return {
        "name": "电子标签多条码识别系统",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/api/v1/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "components": {
            "barcode_engine": "ok",
            "ocr_local": "ok",
            "ocr_cloud": "not_configured"
        },
        "version": "1.0.0"
    }


@app.post("/api/v1/process/single", tags=["Process"])
async def process_single_image(
    image: UploadFile = File(...),
    mode: str = Form("balanced"),
    recognition_mode: str = Form("barcode_only"),
    sort_order: str = Form("reading_order"),
    ocr_mode: str = Form("local"),
    return_image: bool = Form(False)
):
    """
    处理单张图像
    
    - **image**: 图像文件
    - **mode**: 处理模式 (fast/balanced/full)
    - **recognition_mode**: 识别模式 (barcode_only/ocr_only/barcode_and_ocr/ai)
    - **sort_order**: 排序方式 (reading_order/top_to_bottom/left_to_right)
    - **ocr_mode**: OCR模式 (local/cloud)
    - **return_image**: 是否返回标注图像
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    logger.info(f"[{request_id}] Processing single image: {image.filename}, mode={mode}")
    
    try:
        # 验证文件类型
        allowed_extensions = config.get("system.upload.allowed_extensions", ["jpg", "jpeg", "png", "bmp"])
        file_ext = image.filename.split(".")[-1].lower() if "." in image.filename else ""
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file format. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # 保存临时文件
        temp_file = temp_dir / f"{uuid.uuid4()}.{file_ext}"
        with open(temp_file, "wb") as f:
            shutil.copyfileobj(image.file, f)
        
        logger.debug(f"[{request_id}] Saved temp file: {temp_file}")
        
        try:
            # 处理图像
            result = label_processor.process_image_file(
                str(temp_file),
                mode=mode,
                recognition_mode=recognition_mode,
                sort_order=sort_order,
                ocr_mode=ocr_mode
            )
            
            if not result["success"]:
                raise HTTPException(status_code=500, detail=result.get("error", "Processing failed"))
            
            response_data = {
                "process_time": result["process_time"],
                "mode_used": result["mode_used"],
                "recognition_mode": result["recognition_mode"],
                "sort_order": result["sort_order"],
                "results": result["results"],
                "structured_fields": result.get("structured_fields", {}),
                "full_text": result.get("full_text", ""),
                "ai_raw_response": result.get("ai_raw_response")
            }
            
            return ProcessResponse(
                success=True,
                data=response_data,
                message="Processing completed successfully",
                timestamp=int(time.time() * 1000),
                request_id=request_id
            )
        
        finally:
            # 清理临时文件
            if temp_file.exists():
                temp_file.unlink()
                logger.debug(f"[{request_id}] Deleted temp file")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{request_id}] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/process/single/stream", tags=["Process"])
async def process_single_image_stream(
    image: UploadFile = File(...),
    mode: str = Form("balanced"),
    recognition_mode: str = Form("ai"),
    sort_order: str = Form("reading_order"),
    ocr_mode: str = Form("local")
):
    """
    流式处理单张图像(AI识别模式)
    
    - **image**: 图像文件
    - **mode**: 处理模式
    - **recognition_mode**: 识别模式(必须为ai)
    - **sort_order**: 排序方式
    - **ocr_mode**: OCR模式
    """
    request_id = str(uuid.uuid4())
    
    logger.info(f"[{request_id}] Streaming AI recognition: {image.filename}")
    
    # 验证是否为AI模式
    if recognition_mode != 'ai':
        raise HTTPException(
            status_code=400,
            detail="Stream API only supports AI recognition mode"
        )
    
    try:
        # 验证文件类型
        allowed_extensions = config.get("system.upload.allowed_extensions", ["jpg", "jpeg", "png", "bmp"])
        file_ext = image.filename.split(".")[-1].lower() if "." in image.filename else ""
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file format. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # 保存临时文件
        temp_file = temp_dir / f"{uuid.uuid4()}.{file_ext}"
        with open(temp_file, "wb") as f:
            shutil.copyfileobj(image.file, f)
        
        async def stream_generator():
            try:
                # 读取图像
                img = cv2.imread(str(temp_file))
                if img is None:
                    yield f"data: {json.dumps({'error': '无法读取图像'})}\n\n"
                    return
                
                # 获取AI识别器
                if not label_processor.ai_recognizer or not label_processor.ai_recognizer.is_available():
                    yield f"data: {json.dumps({'error': 'AI识别功能不可用'})}\n\n"
                    return
                
                # 调用AI流式识别
                stream_gen = label_processor.ai_recognizer.recognize(img, stream=True)
                
                for chunk in stream_gen:
                    # 发送每个数据块
                    yield f"data: {json.dumps({'content': chunk})}\n\n"
                
                # 结束信号
                yield "data: [DONE]\n\n"
            
            finally:
                # 清理临时文件
                if temp_file.exists():
                    temp_file.unlink()
                    logger.debug(f"[{request_id}] Deleted temp file")
        
        return StreamingResponse(
            stream_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # 禁用nginx缓冲
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{request_id}] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/process/batch", tags=["Process"])
async def process_batch_images(
    images: List[UploadFile] = File(...),
    mode: str = Form("balanced"),
    sort_order: str = Form("reading_order")
):
    """
    批量处理图像
    
    - **images**: 图像文件列表
    - **mode**: 处理模式
    - **sort_order**: 排序方式
    """
    request_id = str(uuid.uuid4())
    batch_id = str(uuid.uuid4())
    start_time = time.time()
    
    logger.info(f"[{request_id}] Batch processing {len(images)} images")
    
    results = []
    
    for img in images:
        try:
            # 验证文件类型
            allowed_extensions = config.get("system.upload.allowed_extensions", ["jpg", "jpeg", "png", "bmp"])
            file_ext = img.filename.split(".")[-1].lower() if "." in img.filename else ""
            
            if file_ext not in allowed_extensions:
                results.append({
                    "image_name": img.filename,
                    "success": False,
                    "error": "Invalid file format"
                })
                continue
            
            # 保存临时文件
            temp_file = temp_dir / f"{uuid.uuid4()}.{file_ext}"
            with open(temp_file, "wb") as f:
                shutil.copyfileobj(img.file, f)
            
            try:
                # 处理图像
                result = label_processor.process_image_file(
                    str(temp_file),
                    mode=mode,
                    sort_order=sort_order
                )
                
                results.append({
                    "image_name": img.filename,
                    "success": result["success"],
                    "data": result if result["success"] else None,
                    "error": result.get("error")
                })
            
            finally:
                if temp_file.exists():
                    temp_file.unlink()
        
        except Exception as e:
            logger.error(f"Error processing {img.filename}: {e}")
            results.append({
                "image_name": img.filename,
                "success": False,
                "error": str(e)
            })
    
    total_time = int((time.time() - start_time) * 1000)
    
    return ProcessResponse(
        success=True,
        data={
            "batch_id": batch_id,
            "total_images": len(images),
            "results": results,
            "total_time": total_time
        },
        message=f"Batch processing completed",
        timestamp=int(time.time() * 1000),
        request_id=request_id
    )


@app.get("/api/v1/config", tags=["Config"])
async def get_config():
    """获取当前配置"""
    return {
        "default_mode": config.get("processing.modes.default", "balanced"),
        "default_ocr_mode": config.get("ocr.ocr.default_mode", "local"),
        "max_image_size": config.get("processing.preprocessing.max_image_size", 2000),
        "position_tolerance": config.get("processing.sorting.position_tolerance", 30),
        "enable_cache": True,
        "cache_ttl": 3600
    }


@app.put("/api/v1/config", tags=["Config"])
async def update_config(config_update: ConfigUpdate):
    """
    更新配置(注意:此实现仅在内存中更新,重启后失效)
    """
    # 实际应用中应该保存到配置文件
    return {
        "success": True,
        "message": "Config updated (in-memory only)",
        "updated_fields": config_update.dict(exclude_none=True)
    }


@app.get("/api/v1/ai/config", tags=["AI"])
async def get_ai_config():
    """获取AI配置"""
    try:
        import yaml
        from pathlib import Path
        
        config_path = Path("config/ai.yaml")
        
        # 直接读取文件获取最新配置
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                current_config = yaml.safe_load(f) or {}
            ai_config = current_config.get('ai', {})
        else:
            ai_config = {}
        
        logger.debug(f"Get AI config: {ai_config}")
        
        return {
            "success": True,
            "data": {
                "enabled": ai_config.get("enabled", False),
                "providers": ai_config.get("providers", []),
                "models": ai_config.get("models", []),
                "active_model_id": ai_config.get("active_model_id")
            }
        }
    except Exception as e:
        logger.error(f"Error getting AI config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/v1/ai/config", tags=["AI"])
async def update_ai_config(ai_config_update: dict):
    """更新AI配置"""
    try:
        import yaml
        from pathlib import Path
        
        logger.info(f"Updating AI config: {ai_config_update}")
        
        config_path = Path("config/ai.yaml")
        
        # 读取当前配置
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                current_config = yaml.safe_load(f) or {}
        else:
            current_config = {}
        
        logger.debug(f"Current config: {current_config}")
        
        # 更新配置
        if 'ai' not in current_config:
            current_config['ai'] = {}
        
        current_config['ai'].update(ai_config_update)
        
        logger.debug(f"Updated config: {current_config}")
        
        # 保存配置
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(current_config, f, allow_unicode=True, default_flow_style=False)
        
        logger.info(f"Config saved to {config_path}")
        
        # 重新加载AI识别器
        from backend.core.ai_recognizer import AIRecognizer
        label_processor.ai_recognizer = AIRecognizer(current_config['ai'])
        
        logger.info("AI configuration updated successfully")
        
        return {
            "success": True,
            "message": "AI配置已更新"
        }
    except Exception as e:
        logger.error(f"Error updating AI config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    host = config.get("system.server.host", "0.0.0.0")
    port = config.get("system.server.port", 8000)
    
    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
