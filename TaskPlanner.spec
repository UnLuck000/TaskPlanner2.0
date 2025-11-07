# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_submodules

# Текущая папка проекта
project_dir = os.getcwd()

# Подключаем доп. файлы
datas = [
    (os.path.join(project_dir, 'second_window.py'), '.'),
    # tasks.db можно включить, если уже есть существующая база
    # (os.path.join(project_dir, 'tasks.db'), '.'),
]

# Иконка если есть
icon_path = os.path.join(project_dir, 'icon.ico') if os.path.exists(os.path.join(project_dir, 'icon.ico')) else None

# Скрытые модули
hiddenimports = collect_submodules('PyQt6')

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
    console=False,  # False если не нужна консоль
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