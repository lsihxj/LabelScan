"""
构建验证测试脚本
用于检查构建后的程序是否正常工作
"""

import sys
import time
from pathlib import Path
import subprocess
import requests
from threading import Thread

def start_server(dist_dir):
    """启动服务器进程"""
    exe_path = dist_dir / 'LabelScan.exe'
    if not exe_path.exists():
        print(f"❌ 找不到可执行文件: {exe_path}")
        return None
    
    print(f"启动服务器: {exe_path}")
    proc = subprocess.Popen(
        [str(exe_path)],
        cwd=str(dist_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    return proc

def wait_for_server(url, timeout=30):
    """等待服务器启动"""
    print(f"等待服务器启动 ({url})...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                print("✅ 服务器已启动")
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(1)
        print(".", end="", flush=True)
    
    print("\n❌ 服务器启动超时")
    return False

def test_api_endpoints(base_url):
    """测试API端点"""
    print("\n测试API端点...")
    
    tests = [
        ("根路径", "/"),
        ("健康检查", "/api/v1/health"),
        ("获取配置", "/api/v1/config"),
        ("AI配置", "/api/v1/ai/config"),
    ]
    
    results = []
    for name, endpoint in tests:
        url = f"{base_url}{endpoint}"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"  ✓ {name}: {endpoint}")
                results.append(True)
            else:
                print(f"  ✗ {name}: {endpoint} (状态码: {response.status_code})")
                results.append(False)
        except Exception as e:
            print(f"  ✗ {name}: {endpoint} (错误: {e})")
            results.append(False)
    
    return all(results)

def check_static_files(dist_dir):
    """检查静态文件"""
    print("\n检查静态文件...")
    
    required_files = [
        'config/system.yaml',
        'config/processing.yaml',
        'config/ai.yaml',
        'config/logging.yaml',
        'frontend/dist/index.html',
        'README_部署说明.txt',
        'start.bat',
    ]
    
    results = []
    for file_path in required_files:
        full_path = dist_dir / file_path
        if full_path.exists():
            print(f"  ✓ {file_path}")
            results.append(True)
        else:
            print(f"  ✗ {file_path} (不存在)")
            results.append(False)
    
    return all(results)

def main():
    print("""
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║        电子标签多条码识别系统 - 构建验证测试                ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    # 检查dist目录
    dist_dir = Path('dist/LabelScan')
    if not dist_dir.exists():
        print("❌ dist/LabelScan 目录不存在")
        print("   请先运行构建脚本: python build_windows.py")
        return False
    
    print(f"✅ 找到构建目录: {dist_dir.absolute()}\n")
    
    # 检查静态文件
    if not check_static_files(dist_dir):
        print("\n❌ 静态文件检查失败")
        return False
    
    # 启动服务器
    print("\n" + "="*60)
    proc = start_server(dist_dir)
    if not proc:
        return False
    
    try:
        # 等待启动
        base_url = "http://localhost:8000"
        if not wait_for_server(base_url):
            return False
        
        # 测试API
        if not test_api_endpoints(base_url):
            print("\n❌ API测试失败")
            return False
        
        print("\n" + "="*60)
        print("✅ 所有测试通过!")
        print("="*60)
        print(f"\n可以访问: {base_url}")
        print("\n按Ctrl+C停止测试...")
        
        # 保持运行
        try:
            proc.wait()
        except KeyboardInterrupt:
            print("\n\n停止服务器...")
        
        return True
    
    finally:
        # 清理
        if proc and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
            print("服务器已停止")

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n用户取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
