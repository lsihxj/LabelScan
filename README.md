# 电子标签多条码识别系统

一个高性能的电子标签识别系统,能够自动识别图像中的多个条码和相关文字信息,并按视觉阅读顺序智能输出结构化结果。

## 核心功能

- ✅ **多条码识别**: 同时识别图像中的多个条码(CODE128, CODE39, QR Code等)
- ✅ **文字识别**: 识别条码相关文字信息(P/N, QTY等结构化字段)
- ✅ **智能排序**: 按阅读顺序(从上到下、从左到右)输出结果
- ✅ **关联分析**: 自动关联条码与周围文字信息
- ✅ **三种处理模式**: 极速/均衡/完整模式,平衡速度与准确率
- ✅ **双OCR模式**: 支持本地Tesseract和云端OCR API
- ✅ **Web界面**: 完整的前端界面,支持可视化标注

## 快速开始

### 环境要求

- Python 3.10+
- Tesseract OCR 5.3+
- Node.js 18+ (前端开发)

### 安装依赖

```bash
# 后端依赖
pip install -r requirements.txt

# 前端依赖
cd frontend
npm install
```

### 启动服务

```bash
# 启动后端API服务
python -m uvicorn backend.main:app --reload --port 8000

# 启动前端开发服务器
cd frontend
npm run dev
```

访问 http://localhost:5173 使用系统

## 项目结构

```
LabelScan/
├── backend/                # 后端代码
│   ├── core/              # 核心处理引擎
│   ├── api/               # REST API接口
│   ├── utils/             # 工具模块
│   └── main.py            # 应用入口
├── frontend/              # 前端代码
│   ├── src/               # 源代码
│   └── public/            # 静态资源
├── config/                # 配置文件
├── tests/                 # 测试代码
└── docs/                  # 文档

```

## 性能指标

- 极速模式: < 30ms/图像
- 均衡模式: < 150ms/图像
- 完整模式: < 500ms/图像
- 批量处理: 100张/15秒

## 开发计划

详见设计文档: `.qoder/quests/electronic-label-multi-barcode-identification-system.md`
