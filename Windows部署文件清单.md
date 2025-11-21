# Windows独立部署版本 - 文件清单

本文档列出了为Windows独立部署创建的所有文件。

## 📦 核心构建文件

### 1. `build.spec`
**用途**: PyInstaller打包配置文件  
**说明**: 定义了如何将Python后端打包成Windows可执行文件，包括依赖、数据文件、隐藏导入等配置。

### 2. `build_windows.py`
**用途**: 自动化构建脚本  
**说明**: 一键完成所有构建步骤的Python脚本，包括：
- 清理旧文件
- 构建前端
- 安装PyInstaller
- 打包后端
- 复制依赖文件
- 创建启动脚本
- 生成发布压缩包

### 3. `build_requirements.txt`
**用途**: 构建工具依赖清单  
**说明**: 列出构建时需要的Python包（PyInstaller等）

## 🛠️ 辅助工具文件

### 4. `setup_config.py`
**用途**: 配置检查和设置工具  
**说明**: 自动检查和配置运行环境：
- 检查Python版本
- 检测Tesseract OCR
- 更新配置文件
- 创建必要目录

### 5. `test_build.py`
**用途**: 构建验证测试脚本  
**说明**: 验证构建是否成功：
- 检查文件完整性
- 启动服务器测试
- 测试API端点
- 验证静态文件

## 🚀 启动脚本（批处理文件）

### 6. `一键构建.bat`
**用途**: Windows一键构建脚本  
**说明**: 双击即可开始构建，自动检查环境、安装依赖、执行构建

### 7. `快速启动(开发).bat`
**用途**: 开发模式启动脚本  
**说明**: 用于开发调试，启动带热重载的开发服务器

### 8. `配置检查.bat`
**用途**: 配置检查工具启动脚本  
**说明**: 快速运行setup_config.py进行环境检查

## 📚 文档文件

### 9. `快速构建指南.md`
**用途**: 详细的构建和部署文档  
**内容**:
- 前置要求
- 构建步骤（自动/手动）
- 部署说明
- 配置说明
- 常见问题
- 优化建议

### 10. `使用说明.md`
**用途**: 最终用户使用指南  
**内容**:
- 系统简介
- 快速开始
- 构建发布包
- 部署步骤
- 详细使用指南
- 常见问题解答

### 11. `打包说明.txt`
**用途**: 快速参考文档  
**内容**:
- 构建步骤概览
- 文件清单
- 部署步骤
- 常见问题

## 🔧 配置文件更新

### 12. `.gitignore`
**用途**: Git版本控制忽略文件  
**更新**: 添加了构建相关的忽略规则：
- build/, dist/, release/ 目录
- *.spec.bak 文件
- 构建临时文件

## 📝 代码修改

### 13. `backend/main.py` (修改)
**修改内容**:
- 添加静态文件服务支持
- 支持打包后环境的路径检测
- 自动服务前端构建文件
- 改进根路径处理

**关键更新**:
```python
# 检测打包环境
if getattr(sys, 'frozen', False):
    base_path = Path(sys._MEIPASS)
else:
    base_path = Path(__file__).parent.parent

# 挂载静态文件
app.mount("/assets", StaticFiles(...))

# 提供index.html
@app.get("/")
async def root():
    return FileResponse(str(static_dir / "index.html"))
```

## 🏗️ 构建产物（运行构建后生成）

### 构建后会生成的目录和文件：

```
dist/LabelScan/              # 完整应用程序
├── LabelScan.exe           # 主程序
├── start.bat               # 启动脚本
├── README_部署说明.txt      # 部署说明
├── config/                 # 配置文件
├── frontend/dist/          # Web界面
├── logs/                   # 日志目录
├── temp/                   # 临时文件
├── uploads/                # 上传目录
└── [依赖库...]

release/
└── LabelScan_Windows_v1.0.0.zip  # 可分发压缩包
```

## 📊 文件统计

| 类别 | 文件数 | 说明 |
|------|--------|------|
| 构建配置 | 3 | build.spec, build_windows.py, build_requirements.txt |
| 工具脚本 | 2 | setup_config.py, test_build.py |
| 批处理脚本 | 3 | 一键构建.bat, 快速启动(开发).bat, 配置检查.bat |
| 文档 | 3 | 快速构建指南.md, 使用说明.md, 打包说明.txt |
| 代码修改 | 1 | backend/main.py |
| **总计** | **12** | **新增11个文件，修改1个文件** |

## 🎯 使用流程

### 对于开发者（构建发布包）：

1. 双击 `一键构建.bat` 或运行 `python build_windows.py`
2. 等待构建完成
3. 在 `release/` 目录获取发布包

### 对于部署人员（部署到目标机器）：

1. 解压发布包到目标目录
2. 安装Tesseract OCR
3. 运行 `配置检查.bat`（可选）
4. 配置 `config/system.yaml`
5. 双击 `start.bat` 启动系统

### 对于开发调试：

1. 双击 `快速启动(开发).bat`
2. 浏览器访问 http://localhost:8000

## 📋 检查清单

构建前检查：
- [ ] Python 3.10+ 已安装
- [ ] Node.js 18+ 已安装
- [ ] 运行时依赖已安装 (`pip install -r requirements.txt`)
- [ ] 构建依赖已安装 (`pip install -r build_requirements.txt`)
- [ ] 前端依赖已安装 (`cd frontend && npm install`)

构建后检查：
- [ ] `dist/LabelScan/` 目录存在
- [ ] `LabelScan.exe` 可执行文件存在
- [ ] `config/` 目录及所有YAML文件存在
- [ ] `frontend/dist/` 目录及文件存在
- [ ] `start.bat` 启动脚本存在
- [ ] `release/LabelScan_Windows_v1.0.0.zip` 压缩包生成

部署后检查：
- [ ] Tesseract OCR 已安装
- [ ] `config/system.yaml` 中Tesseract路径已配置
- [ ] 运行 `start.bat` 成功启动
- [ ] 浏览器可访问 http://localhost:8000
- [ ] OCR识别功能正常
- [ ] 条码识别功能正常

## 🔍 故障排查

### 构建失败

1. 检查Python和Node.js版本
2. 确认所有依赖已安装
3. 查看构建脚本输出的错误信息
4. 清理旧文件后重试：删除 `build/`, `dist/`, `release/` 目录

### 部署失败

1. 检查Tesseract安装路径
2. 验证配置文件格式
3. 查看 `logs/error.log`
4. 确认端口未被占用

### 运行错误

1. 查看控制台错误输出
2. 检查 `logs/app.log` 和 `logs/error.log`
3. 确认所有配置文件存在且格式正确
4. 验证 `frontend/dist/` 目录完整

## 📞 技术支持

- 构建相关问题：参考 `快速构建指南.md`
- 使用相关问题：参考 `使用说明.md`
- 配置相关问题：参考配置文件注释
- 错误诊断：查看 `logs/` 目录下的日志文件

---

**创建日期**: 2024  
**版本**: 1.0.0  
**状态**: ✅ 完整
