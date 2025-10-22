# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Monte Carlo Fund Simulation
"""

import sys
from pathlib import Path
import streamlit as st

# Get Streamlit installation path
streamlit_path = Path(st.__file__).parent

block_cipher = None

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Include Streamlit runtime files
        (str(streamlit_path / 'static'), 'streamlit/static'),
        (str(streamlit_path / 'runtime'), 'streamlit/runtime'),
        # Include fund_simulation package
        ('fund_simulation', 'fund_simulation'),
        # Include any data files if needed
    ],
    hiddenimports=[
        'streamlit',
        'streamlit.web.cli',
        'streamlit.runtime.scriptrunner.magic_funcs',
        'pandas',
        'numpy',
        'plotly',
        'openpyxl',
        'kaleido',
        'dateutil',
        'fund_simulation.models',
        'fund_simulation.calculators',
        'fund_simulation.data_import',
        'fund_simulation.beta_import',
        'fund_simulation.simulation',
        'fund_simulation.statistics',
        'fund_simulation.beta_simulation',
        'fund_simulation.reconstruction',
        'fund_simulation.csv_export',
        'fund_simulation.excel_export',
    ],
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
    name='FundSimulation',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Hide console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if Path('icon.ico').exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='FundSimulation',
)
