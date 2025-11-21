# API使用说明

## 概述

电子标签多条码识别系统提供RESTful API接口，支持图像上传、条码识别、OCR文字识别和AI智能识别等功能。

**基础信息:**
- 基础URL: `http://localhost:8000/api/v1`
- 内容类型: `multipart/form-data` (图像上传)
- 响应格式: `application/json`

**在线API文档:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 目录

1. [图像处理接口](#图像处理接口)
2. [配置管理接口](#配置管理接口)
3. [AI配置接口](#ai配置接口)
4. [健康检查接口](#健康检查接口)
5. [调用示例](#调用示例)
6. [错误处理](#错误处理)

---

## 图像处理接口

### 1. 处理单张图像

**接口地址:** `POST /api/v1/process/single`

**功能说明:** 上传图像进行识别，支持纯条码、纯OCR、条码+OCR、AI识别四种模式。

**请求参数:**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| image | File | 是 | - | 图像文件（jpg/jpeg/png/bmp） |
| sort_order | String | 是 | - | 排序方式：reading_order(阅读顺序)/top_to_bottom(从上到下)/left_to_right(从左到右) |
| mode | String | 否 | balanced | 处理模式：fast(极速)/balanced(均衡)/full(完整) |
| recognition_mode | String | 否 | barcode_only | 识别模式：barcode_only/ocr_only/barcode_and_ocr/ai |
| ocr_mode | String | 否 | local | OCR模式：local(本地)/cloud(云端) |
| return_image | Boolean | 否 | false | 是否返回标注图像 |

**响应格式:**

```json
{
  "success": true,
  "data": {
    "process_time": 1250,
    "mode_used": "balanced",
    "recognition_mode": "barcode_only",
    "sort_order": "reading_order",
    "results": [
      {
        "order": 1,
        "type": "barcode",
        "data": {
          "barcode_data": "1234567890",
          "barcode_type": "CODE128"
        },
        "position": {
          "x": 100,
          "y": 150,
          "width": 200,
          "height": 80
        }
      }
    ],
    "structured_fields": {},
    "full_text": ""
  },
  "message": "Processing completed successfully",
  "timestamp": 1700000000000,
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**识别模式说明:**

- **barcode_only**: 仅识别条码/二维码（最快）
- **ocr_only**: 仅进行OCR文字识别
- **barcode_and_ocr**: 同时识别条码和文字，并进行关联分析
- **ai**: 使用AI模型智能识别（需配置AI服务）

**处理模式说明:**

- **fast**: 极速模式，快速处理，适合批量扫描
- **balanced**: 均衡模式，平衡速度和准确度（推荐）
- **full**: 完整模式，最高准确度，处理速度较慢

---

### 2. 流式处理单张图像（AI模式）

**接口地址:** `POST /api/v1/process/single/stream`

**功能说明:** 使用AI进行流式识别，实时返回识别进度。

**请求参数:**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| image | File | 是 | - | 图像文件 |
| sort_order | String | 是 | - | 排序方式：reading_order(阅读顺序)/top_to_bottom(从上到下)/left_to_right(从左到右) |
| mode | String | 否 | balanced | 处理模式 |
| recognition_mode | String | 是 | ai | 必须为ai |
| ocr_mode | String | 否 | local | OCR模式 |

**响应格式:** Server-Sent Events (SSE)

```
data: {"content": "识别"}
data: {"content": "到条码"}
data: {"content": "..."}
data: [DONE]
```

**注意事项:**
- 此接口仅支持AI识别模式
- 使用Server-Sent Events流式返回数据
- 适合需要实时反馈的场景

---

### 3. 批量处理图像

**接口地址:** `POST /api/v1/process/batch`

**功能说明:** 一次上传多张图像进行批量识别。

**请求参数:**

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| images | File[] | 是 | - | 图像文件数组 |
| sort_order | String | 是 | - | 排序方式：reading_order(阅读顺序)/top_to_bottom(从上到下)/left_to_right(从左到右) |
| mode | String | 否 | balanced | 处理模式 |

**响应格式:**

```json
{
  "success": true,
  "data": {
    "batch_id": "batch-uuid",
    "total_images": 3,
    "results": [
      {
        "image_name": "label1.jpg",
        "success": true,
        "data": {
          "process_time": 1200,
          "results": [...]
        }
      },
      {
        "image_name": "label2.jpg",
        "success": false,
        "error": "Invalid file format"
      }
    ],
    "total_time": 3500
  },
  "message": "Batch processing completed",
  "timestamp": 1700000000000,
  "request_id": "batch-request-id"
}
```

---

## 配置管理接口

### 1. 获取配置

**接口地址:** `GET /api/v1/config`

**功能说明:** 获取当前系统配置。

**响应格式:**

```json
{
  "default_mode": "balanced",
  "default_ocr_mode": "local",
  "max_image_size": 2000,
  "position_tolerance": 30,
  "enable_cache": true,
  "cache_ttl": 3600
}
```

---

### 2. 更新配置

**接口地址:** `PUT /api/v1/config`

**功能说明:** 更新系统配置（内存中，重启后失效）。

**请求参数:**

```json
{
  "default_mode": "balanced",
  "default_ocr_mode": "local",
  "position_tolerance": 30
}
```

**响应格式:**

```json
{
  "success": true,
  "message": "Config updated (in-memory only)",
  "updated_fields": {
    "default_mode": "balanced"
  }
}
```

---

## AI配置接口

### 1. 获取AI配置

**接口地址:** `GET /api/v1/ai/config`

**功能说明:** 获取AI服务配置信息。

**响应格式:**

```json
{
  "success": true,
  "data": {
    "enabled": true,
    "providers": [
      {
        "id": "openai",
        "name": "OpenAI",
        "api_base": "https://api.openai.com/v1",
        "api_key": "sk-***"
      }
    ],
    "models": [
      {
        "id": "gpt-4-vision",
        "name": "GPT-4 Vision",
        "provider_id": "openai",
        "model_name": "gpt-4-vision-preview"
      }
    ],
    "active_model_id": "gpt-4-vision"
  }
}
```

---

### 2. 更新AI配置

**接口地址:** `PUT /api/v1/ai/config`

**功能说明:** 更新AI服务配置。

**请求参数:**

```json
{
  "enabled": true,
  "providers": [
    {
      "id": "moonshot",
      "name": "Moonshot AI",
      "api_base": "https://api.moonshot.cn/v1",
      "api_key": "sk-your-key"
    }
  ],
  "models": [
    {
      "id": "moonshot-v1",
      "name": "Moonshot V1",
      "provider_id": "moonshot",
      "model_name": "moonshot-v1-128k"
    }
  ],
  "active_model_id": "moonshot-v1"
}
```

**响应格式:**

```json
{
  "success": true,
  "message": "AI配置已更新"
}
```

---

## 健康检查接口

**接口地址:** `GET /api/v1/health`

**功能说明:** 检查系统健康状态。

**响应格式:**

```json
{
  "status": "healthy",
  "components": {
    "barcode_engine": "ok",
    "ocr_local": "ok",
    "ocr_cloud": "not_configured"
  },
  "version": "1.0.0"
}
```

---

## 调用示例

### cURL 示例

#### 1. 纯条码识别

```bash
curl -X POST http://localhost:8000/api/v1/process/single \
  -F "image=@/path/to/label.jpg" \
  -F "sort_order=reading_order" \
  -F "recognition_mode=barcode_only" \
  -F "mode=fast"
```

#### 2. AI识别

```bash
curl -X POST http://localhost:8000/api/v1/process/single \
  -F "image=@/path/to/label.jpg" \
  -F "sort_order=top_to_bottom" \
  -F "recognition_mode=ai" \
  -F "mode=balanced"
```

#### 3. 条码+OCR识别

```bash
curl -X POST http://localhost:8000/api/v1/process/single \
  -F "image=@/path/to/label.jpg" \
  -F "sort_order=reading_order" \
  -F "recognition_mode=barcode_and_ocr" \
  -F "mode=full" \
  -F "ocr_mode=local"
```

#### 4. 批量处理

```bash
curl -X POST http://localhost:8000/api/v1/process/batch \
  -F "images=@label1.jpg" \
  -F "images=@label2.jpg" \
  -F "images=@label3.jpg" \
  -F "sort_order=reading_order" \
  -F "mode=balanced"
```

---

### Python 示例

```python
import requests

# 1. 单图像识别
def process_image(image_path, sort_order='reading_order', recognition_mode='barcode_only'):
    url = 'http://localhost:8000/api/v1/process/single'
    
    with open(image_path, 'rb') as f:
        files = {'image': f}
        data = {
            'sort_order': sort_order,
            'mode': 'balanced',
            'recognition_mode': recognition_mode,
            'ocr_mode': 'local'
        }
        
        response = requests.post(url, files=files, data=data)
        return response.json()

# 调用示例
result = process_image('label.jpg', sort_order='reading_order', recognition_mode='barcode_only')
if result['success']:
    for item in result['data']['results']:
        print(f"#{item['order']}: {item['data']}")
else:
    print(f"Error: {result.get('message')}")


# 2. AI流式识别
def process_image_stream(image_path, sort_order='reading_order'):
    url = 'http://localhost:8000/api/v1/process/single/stream'
    
    with open(image_path, 'rb') as f:
        files = {'image': f}
        data = {
            'sort_order': sort_order,
            'mode': 'balanced',
            'recognition_mode': 'ai'
        }
        
        response = requests.post(url, files=files, data=data, stream=True)
        
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data = line[6:]
                    if data == '[DONE]':
                        break
                    print(data, end='', flush=True)

# 调用示例
process_image_stream('label.jpg', sort_order='top_to_bottom')


# 3. 批量处理
def process_batch(image_paths, sort_order='reading_order'):
    url = 'http://localhost:8000/api/v1/process/batch'
    
    files = [('images', open(path, 'rb')) for path in image_paths]
    data = {
        'sort_order': sort_order,
        'mode': 'balanced'
    }
    
    response = requests.post(url, files=files, data=data)
    
    # 关闭文件
    for _, f in files:
        f.close()
    
    return response.json()

# 调用示例
results = process_batch(['label1.jpg', 'label2.jpg', 'label3.jpg'], sort_order='reading_order')
print(f"处理了 {results['data']['total_images']} 张图像")
```

---

### JavaScript 示例

```javascript
// 1. 单图像识别
async function processImage(file, sortOrder = 'reading_order', recognitionMode = 'barcode_only') {
  const formData = new FormData();
  formData.append('image', file);
  formData.append('sort_order', sortOrder);
  formData.append('mode', 'balanced');
  formData.append('recognition_mode', recognitionMode);
  formData.append('ocr_mode', 'local');

  const response = await fetch('/api/v1/process/single', {
    method: 'POST',
    body: formData
  });

  return await response.json();
}

// 调用示例
const fileInput = document.querySelector('input[type="file"]');
const result = await processImage(fileInput.files[0], 'reading_order', 'barcode_only');
if (result.success) {
  result.data.results.forEach(item => {
    console.log(`#${item.order}:`, item.data);
  });
}


// 2. AI流式识别
async function processImageStream(file, sortOrder = 'reading_order', onChunk) {
  const formData = new FormData();
  formData.append('image', file);
  formData.append('sort_order', sortOrder);
  formData.append('recognition_mode', 'ai');

  const response = await fetch('/api/v1/process/single/stream', {
    method: 'POST',
    body: formData
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value, { stream: true });
    const lines = chunk.split('\n');

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.slice(6);
        if (data === '[DONE]') return;
        
        try {
          const parsed = JSON.parse(data);
          if (parsed.content) {
            onChunk(parsed.content);
          }
        } catch (e) {
          console.warn('Failed to parse:', data);
        }
      }
    }
  }
}

// 调用示例
await processImageStream(file, 'top_to_bottom', (chunk) => {
  console.log('收到数据:', chunk);
});


// 3. 批量处理
async function processBatch(files, sortOrder = 'reading_order') {
  const formData = new FormData();
  files.forEach(file => {
    formData.append('images', file);
  });
  formData.append('sort_order', sortOrder);
  formData.append('mode', 'balanced');

  const response = await fetch('/api/v1/process/batch', {
    method: 'POST',
    body: formData
  });

  return await response.json();
}

// 调用示例
const files = document.querySelector('input[type="file"]').files;
const result = await processBatch(Array.from(files), 'reading_order');
console.log(`处理了 ${result.data.total_images} 张图像`);
```

---

## 错误处理

### 错误响应格式

```json
{
  "detail": "错误描述信息"
}
```

### 常见错误码

| HTTP状态码 | 说明 | 常见原因 |
|-----------|------|---------|
| 400 | 请求参数错误 | 文件格式不支持、参数缺失或无效 |
| 500 | 服务器内部错误 | 处理失败、配置错误、依赖服务不可用 |

### 错误处理示例

```python
try:
    response = requests.post(url, files=files, data=data)
    response.raise_for_status()  # 检查HTTP状态
    
    result = response.json()
    if result.get('success'):
        # 处理成功结果
        pass
    else:
        # 处理业务错误
        print(f"处理失败: {result.get('message')}")
        
except requests.exceptions.HTTPError as e:
    print(f"HTTP错误: {e}")
except requests.exceptions.RequestException as e:
    print(f"请求失败: {e}")
except Exception as e:
    print(f"未知错误: {e}")
```

---

## 最佳实践

### 1. 选择合适的识别模式

- **拍照识别条码**: 使用 `barcode_only` + `fast` 模式
- **识别带文字的标签**: 使用 `barcode_and_ocr` + `balanced` 模式
- **高精度场景**: 使用 `full` 模式
- **智能识别**: 使用 `ai` 模式（需配置AI服务）

### 2. 图像优化建议

- 确保图像清晰，分辨率适中（推荐1000-2000px）
- 避免图像过大（系统会自动调整到最大2000px）
- 确保光线充足，避免反光和阴影
- 条码完整无遮挡

### 3. 性能优化

- 批量处理时使用 `/process/batch` 接口
- 简单场景使用 `fast` 模式
- 合理设置超时时间（建议30秒）
- 考虑使用异步处理机制

### 4. 安全建议

- 生产环境建议配置HTTPS
- 限制上传文件大小
- 添加API认证机制
- 记录和监控API调用

---

## 技术支持

### 获取帮助

- 在线API文档: http://localhost:8000/docs
- 查看日志文件: `logs/app.log` 和 `logs/error.log`
- 检查配置文件: `config/*.yaml`

### 常见问题

**Q: 识别失败怎么办？**
- 检查图像格式是否支持（jpg/jpeg/png/bmp）
- 查看错误日志了解详细原因
- 尝试使用更高的处理模式

**Q: AI识别不可用？**
- 确认已配置AI服务商和API密钥
- 检查网络连接和API额度
- 查看 `config/ai.yaml` 配置

**Q: OCR识别效果差？**
- 使用 `balanced` 或 `full` 模式
- 确保Tesseract正确安装
- 检查图像质量和清晰度

---

**文档版本:** 1.0.0  
**最后更新:** 2024-11  
**系统版本:** LabelScan v1.0.0
