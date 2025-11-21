# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller打包配置文件
用于创建Windows独立可执行文件
"""

import sys
from pathlib import Path

block_cipher = None

# 项目根目录
project_root = Path.cwd()

# 收集所有数据文件
datas = [
    ('config', 'config'),  # 配置文件
    ('frontend/dist', 'frontend/dist'),  # 前端构建文件
]

# 收集隐藏导入
hiddenimports = [
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    'yaml',
    'pyzbar',
    'pytesseract',
    'cv2',
    'PIL',
    'loguru',
    'pydantic',
    'fastapi',
    'multipart',
]

# 二进制文件
binaries = []

# 添加pyzbar的DLL文件
import os
import sys
from pathlib import Path

# 查找pyzbar的DLL文件
try:
    import pyzbar
    pyzbar_path = Path(pyzbar.__file__).parent
    
    # 将pyzbar目录下的所有DLL文件添加到binaries
    for dll_file in pyzbar_path.glob('*.dll'):
        binaries.append((str(dll_file), 'pyzbar'))
        print(f"Adding pyzbar DLL: {dll_file.name}")
except ImportError:
    print("Warning: pyzbar not found")

a = Analysis(
    ['backend/main.py'],
    pathex=[str(project_root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='LabelScan',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # 显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 可以添加图标文件路径
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='LabelScan',
)
