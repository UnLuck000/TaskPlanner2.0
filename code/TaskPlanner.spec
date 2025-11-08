# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_submodules

# Текущая папка проекта
project_dir = os.getcwd()

# Доп. файлы проекта
datas = [
    (os.path.join(project_dir, 'icon.ico'), '.')  # <-- DEST_DIR теперь относительный
]

# Добавляем иконку если она есть
icon_path = os.path.join(project_dir, 'icon.ico')

# Добавляем все скрытые библиотеки и модули
hiddenimports = collect_submodules('PyQt6')
hiddenimports += ['PyQt6.QtCharts']

# Анализ проекта
a = Analysis(
    ['main_window.py'],
    pathex=[project_dir],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

# Создание архива
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Создание .exe файла
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='TaskPlanner',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=icon_path,
)

# Сборка всех файлов в dist
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='TaskPlanner'
)