"""
Windows部署配置检查和设置工具
"""

import sys
import subprocess
from pathlib import Path
import yaml
import shutil

def check_python_version():
    """检查Python版本"""
    print("\n检查Python版本...")
    version = sys.version_info
    if version < (3, 10):
        print(f"❌ Python版本过低: {version.major}.{version.minor}.{version.micro}")
        print("   需要Python 3.10或更高版本")
        return False
    print(f"✅ Python版本: {version.major}.{version.minor}.{version.micro}")
    return True

def check_tesseract():
    """检查Tesseract OCR是否安装"""
    print("\n检查Tesseract OCR...")
    
    common_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        r"D:\Program Files\Tesseract-OCR\tesseract.exe",
    ]
    
    # 尝试从PATH中查找
    try:
        result = subprocess.run(
            ['tesseract', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print("✅ Tesseract OCR已安装(在PATH中)")
            return 'tesseract'
    except:
        pass
    
    # 检查常见安装路径
    for path in common_paths:
        if Path(path).exists():
            print(f"✅ Tesseract OCR已安装: {path}")
            return path
    
    print("⚠️  未检测到Tesseract OCR")
    print("   请从以下地址下载并安装:")
    print("   https://github.com/UB-Mannheim/tesseract/wiki")
    return None

def update_config(tesseract_path):
    """更新配置文件"""
    print("\n更新配置文件...")
    
    config_dir = Path('config')
    if not config_dir.exists():
        print("❌ config目录不存在")
        return False
    
    # 更新system.yaml
    system_config_path = config_dir / 'system.yaml'
    if not system_config_path.exists():
        print("⚠️  system.yaml不存在，创建默认配置")
        system_config = {}
    else:
        with open(system_config_path, 'r', encoding='utf-8') as f:
            system_config = yaml.safe_load(f) or {}
    
    # 设置Tesseract路径
    if tesseract_path:
        if 'ocr' not in system_config:
            system_config['ocr'] = {}
        if 'local' not in system_config['ocr']:
            system_config['ocr']['local'] = {}
        
        # Windows路径需要转义反斜杠
        escaped_path = str(tesseract_path).replace('\\', '\\\\')
        system_config['ocr']['local']['tesseract_cmd'] = escaped_path
        
        with open(system_config_path, 'w', encoding='utf-8') as f:
            yaml.dump(system_config, f, allow_unicode=True, default_flow_style=False)
        
        print(f"✅ 已配置Tesseract路径: {tesseract_path}")
    
    return True

def check_dependencies():
    """检查Python依赖"""
    print("\n检查Python依赖...")
    
    required = [
        'fastapi',
        'uvicorn',
        'opencv-python',
        'pyzbar',
        'pytesseract',
        'Pillow',
        'numpy',
        'pydantic',
        'pyyaml',
        'loguru'
    ]
    
    missing = []
    for package in required:
        try:
            __import__(package.replace('-', '_'))
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package}")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  缺少以下依赖: {', '.join(missing)}")
        print("   运行以下命令安装:")
        print(f"   pip install {' '.join(missing)}")
        return False
    
    print("✅ 所有依赖已安装")
    return True

def create_directories():
    """创建必要的目录"""
    print("\n创建必要目录...")
    
    dirs = ['logs', 'temp', 'uploads']
    for dir_name in dirs:
        dir_path = Path(dir_name)
        dir_path.mkdir(exist_ok=True)
        print(f"  ✓ {dir_name}")
    
    print("✅ 目录创建完成")
    return True

def main():
    print("""
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║        电子标签多条码识别系统 - Windows配置工具            ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    # 检查步骤
    checks = [
        ("检查Python版本", check_python_version, True),
        ("检查Tesseract OCR", check_tesseract, False),
        ("检查Python依赖", check_dependencies, False),
        ("创建必要目录", create_directories, True),
    ]
    
    tesseract_path = None
    
    for name, func, required in checks:
        result = func()
        
        if name == "检查Tesseract OCR":
            tesseract_path = result
        
        if required and not result:
            print(f"\n❌ 配置失败: {name}")
            return False
    
    # 更新配置
    if tesseract_path:
        update_config(tesseract_path)
    
    print(f"\n{'='*60}")
    print("🎉 配置完成!")
    print(f"{'='*60}\n")
    
    if tesseract_path:
        print("✅ 系统已就绪，可以启动服务")
        print("\n启动方法:")
        print("  开发模式: python -m uvicorn backend.main:app --reload")
        print("  生产模式: python backend/main.py")
    else:
        print("⚠️  请先安装Tesseract OCR后再启动系统")
        print("\n安装步骤:")
        print("  1. 访问: https://github.com/UB-Mannheim/tesseract/wiki")
        print("  2. 下载Windows安装包")
        print("  3. 安装时选择中文语言包(chi_sim)")
        print("  4. 重新运行此配置工具")
    
    print()
    return True

if __name__ == '__main__':
    try:
        success = main()
        input("\n按任意键退出...")
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n用户取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        input("\n按任意键退出...")
        sys.exit(1)
