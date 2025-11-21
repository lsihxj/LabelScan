"""
Windows打包构建脚本
自动化构建可独立部署的Windows版本
"""

import subprocess
import shutil
import sys
from pathlib import Path
import os

def run_command(cmd, cwd=None, shell=True):
    """执行命令并打印输出"""
    print(f"\n{'='*60}")
    print(f"执行命令: {cmd}")
    print(f"{'='*60}\n")
    
    result = subprocess.run(
        cmd,
        shell=shell,
        cwd=cwd,
        text=True,
        capture_output=False
    )
    
    if result.returncode != 0:
        print(f"❌ 命令执行失败: {cmd}")
        return False
    return True

def clean_build():
    """清理构建目录"""
    print("\n🧹 清理构建目录...")
    
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        dir_path = Path(dir_name)
        if dir_path.exists():
            try:
                shutil.rmtree(dir_path)
                print(f"  ✓ 已删除: {dir_name}")
            except Exception as e:
                print(f"  ⚠️  无法删除 {dir_name}: {e}")
                print(f"  继续构建...")
    
    print("✅ 清理完成")
    return True

def build_frontend():
    """构建前端"""
    print("\n🔨 构建前端...")
    
    frontend_dir = Path('frontend')
    if not frontend_dir.exists():
        print("❌ frontend目录不存在")
        return False
    
    # 安装依赖
    if not run_command('npm install', cwd=frontend_dir):
        return False
    
    # 构建
    if not run_command('npm run build', cwd=frontend_dir):
        return False
    
    print("✅ 前端构建完成")
    return True

def install_pyinstaller():
    """安装PyInstaller"""
    print("\n📦 检查PyInstaller...")
    
    try:
        import PyInstaller
        print("✅ PyInstaller已安装")
        return True
    except ImportError:
        print("📥 安装PyInstaller...")
        return run_command(f'{sys.executable} -m pip install pyinstaller')

def build_backend():
    """打包后端"""
    print("\n🔨 打包后端...")
    
    if not run_command(f'{sys.executable} -m PyInstaller build.spec --clean'):
        return False
    
    print("✅ 后端打包完成")
    return True

def copy_dependencies():
    """复制依赖文件"""
    print("\n📋 复制依赖文件...")
    
    dist_dir = Path('dist/LabelScan')
    if not dist_dir.exists():
        print("❌ dist/LabelScan目录不存在")
        return False
    
    # 创建必要目录
    (dist_dir / 'logs').mkdir(exist_ok=True)
    (dist_dir / 'temp').mkdir(exist_ok=True)
    (dist_dir / 'uploads').mkdir(exist_ok=True)
    
    # 复制config目录到外部（供用户编辑）
    config_src = Path('config')
    config_dst = dist_dir / 'config'
    if config_src.exists():
        if config_dst.exists():
            shutil.rmtree(config_dst)
        shutil.copytree(config_src, config_dst)
        print(f"  ✓ 已复制config目录到: {config_dst}")
    
    # 复制README
    readme_src = Path('README.md')
    if readme_src.exists():
        shutil.copy2(readme_src, dist_dir / 'README.md')
        print("  ✓ 已复制README.md")
    
    print("✅ 依赖文件复制完成")
    return True

def create_launcher():
    """创建启动脚本"""
    print("\n📝 创建启动脚本...")
    
    dist_dir = Path('dist/LabelScan')
    
    # Windows批处理启动脚本
    bat_content = """@echo off
chcp 65001 >nul
title 电子标签多条码识别系统

echo ========================================
echo   电子标签多条码识别系统
echo ========================================
echo.
echo 正在启动服务器...
echo.

LabelScan.exe

if errorlevel 1 (
    echo.
    echo ❌ 启动失败！
    echo.
    pause
) else (
    echo.
    echo 服务器已关闭
    pause
)
"""
    
    bat_file = dist_dir / 'start.bat'
    bat_file.write_text(bat_content, encoding='utf-8')
    print(f"  ✓ 已创建: {bat_file}")
    
    # 创建说明文件
    readme_content = """# 电子标签多条码识别系统 - Windows独立部署版

## 系统要求

- Windows 10/11 (64位)
- Tesseract OCR 5.3+ (用于本地OCR识别)
- 至少4GB可用内存

## 安装说明

### 1. 安装Tesseract OCR

本系统需要Tesseract OCR引擎进行文字识别。

1. 下载Tesseract安装包: https://github.com/UB-Mannheim/tesseract/wiki
2. 运行安装程序，建议安装到默认路径
3. 安装时选择中文语言包 (chi_sim)
4. 记录安装路径，如: `C:\\Program Files\\Tesseract-OCR\\tesseract.exe`

### 2. 配置Tesseract路径

编辑 `config/system.yaml` 文件，找到以下配置并修改为实际安装路径:

```yaml
ocr:
  local:
    tesseract_cmd: "C:\\\\Program Files\\\\Tesseract-OCR\\\\tesseract.exe"
```

注意: 路径中的反斜杠需要使用双反斜杠 `\\\\`

## 启动系统

双击运行 `start.bat` 启动服务器。

启动成功后，系统将在以下地址运行:
- Web界面: http://localhost:8000

## 使用说明

1. 在浏览器中打开 http://localhost:8000
2. 上传标签图像
3. 选择识别模式和处理选项
4. 查看识别结果

## 识别模式

- **仅条码**: 只识别条码
- **仅文字**: 只进行OCR文字识别
- **条码+文字**: 同时识别条码和文字
- **AI识别**: 使用AI模型进行智能识别

## 处理模式

- **极速模式**: 快速处理，适合批量扫描
- **均衡模式**: 平衡速度和准确度
- **完整模式**: 最高准确度，处理速度较慢

## AI配置

如需使用AI识别功能，请在Web界面的"AI设置"中配置:
1. 选择AI服务提供商
2. 输入API密钥
3. 选择要使用的模型
4. 激活模型

## 配置文件

所有配置文件位于 `config` 目录:
- `system.yaml`: 系统配置
- `processing.yaml`: 处理参数配置
- `ai.yaml`: AI服务配置
- `logging.yaml`: 日志配置

## 数据目录

- `logs/`: 日志文件
- `temp/`: 临时文件
- `uploads/`: 上传的图像文件

## 常见问题

### 1. 启动失败

- 检查端口8000是否被占用
- 查看logs目录下的日志文件

### 2. OCR识别失败

- 确认Tesseract已正确安装
- 检查config/system.yaml中的tesseract_cmd路径是否正确
- 确保已安装中文语言包

### 3. AI识别不可用

- 检查网络连接
- 确认API密钥配置正确
- 查看日志文件了解详细错误信息

## 技术支持

如遇问题，请查看 `logs/app.log` 和 `logs/error.log` 日志文件。
"""
    
    readme_file = dist_dir / 'README_部署说明.txt'
    readme_file.write_text(readme_content, encoding='utf-8')
    print(f"  ✓ 已创建: {readme_file}")
    
    print("✅ 启动脚本创建完成")
    return True

def create_installer():
    """创建安装包(可选)"""
    print("\n📦 准备发布包...")
    
    dist_dir = Path('dist/LabelScan')
    if not dist_dir.exists():
        print("❌ dist/LabelScan目录不存在")
        return False
    
    release_dir = Path('release')
    release_dir.mkdir(exist_ok=True)
    
    # 创建压缩包
    archive_name = 'LabelScan_Windows_v1.0.0'
    archive_path = release_dir / archive_name
    
    try:
        print(f"  正在创建压缩包: {archive_name}.zip")
        shutil.make_archive(str(archive_path), 'zip', 'dist', 'LabelScan')
        print(f"✅ 发布包已创建: {archive_path}.zip")
        return True
    except Exception as e:
        print(f"❌ 创建压缩包失败: {e}")
        return False

def main():
    """主构建流程"""
    print("""
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║        电子标签多条码识别系统 - Windows打包工具            ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    # 检查Python版本
    if sys.version_info < (3, 10):
        print("❌ 需要Python 3.10或更高版本")
        return False
    
    print(f"✓ Python版本: {sys.version}")
    
    # 构建流程
    steps = [
        ("清理构建目录", clean_build),
        ("构建前端", build_frontend),
        ("安装PyInstaller", install_pyinstaller),
        ("打包后端", build_backend),
        ("复制依赖文件", copy_dependencies),
        ("创建启动脚本", create_launcher),
        ("创建发布包", create_installer),
    ]
    
    for step_name, step_func in steps:
        print(f"\n{'='*60}")
        print(f"步骤: {step_name}")
        print(f"{'='*60}")
        
        if not step_func():
            print(f"\n❌ 构建失败于: {step_name}")
            return False
    
    print(f"\n{'='*60}")
    print("🎉 构建完成!")
    print(f"{'='*60}\n")
    print("📂 发布包位置: release/LabelScan_Windows_v1.0.0.zip")
    print("📂 程序目录: dist/LabelScan/\n")
    print("后续步骤:")
    print("  1. 解压 release/LabelScan_Windows_v1.0.0.zip 到目标机器")
    print("  2. 安装Tesseract OCR")
    print("  3. 配置 config/system.yaml 中的Tesseract路径")
    print("  4. 双击 start.bat 启动系统")
    print()
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

