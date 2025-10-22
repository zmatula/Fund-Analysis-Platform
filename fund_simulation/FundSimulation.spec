# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Monte Carlo Fund Simulation
Creates a standalone Windows executable with all dependencies bundled
NO Python installation required on target machine!
"""

import sys
from pathlib import Path

block_cipher = None

# Collect Streamlit and other package data
def get_package_data():
    """Collect all necessary package data files"""
    import streamlit
    import plotly

    streamlit_path = Path(streamlit.__file__).parent
    plotly_path = Path(plotly.__file__).parent

    datas = []

    # Streamlit files
    datas.append((str(streamlit_path / 'static'), 'streamlit/static'))
    datas.append((str(streamlit_path / 'runtime'), 'streamlit/runtime'))

    # Plotly files
    if (plotly_path / 'package_data').exists():
        datas.append((str(plotly_path / 'package_data'), 'plotly/package_data'))

    # Application files
    datas.append(('app.py', '.'))
    datas.append(('fund_simulation', 'fund_simulation'))

    return datas

a = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=[],
    datas=get_package_data(),
    hiddenimports=[
        # Streamlit core
        'streamlit',
        'streamlit.web.cli',
        'streamlit.web.bootstrap',
        'streamlit.runtime.scriptrunner.magic_funcs',
        'streamlit.runtime.scriptrunner.script_runner',
        'streamlit.runtime.state',
        'streamlit.runtime.caching',
        'streamlit.logger',
        'streamlit.file_util',

        # Data packages
        'pandas',
        'pandas._libs.tslibs.timedeltas',
        'pandas._libs.tslibs.np_datetime',
        'pandas._libs.tslibs.nattype',
        'pandas._libs.skiplist',
        'numpy',
        'numpy.core._methods',
        'numpy.lib.format',

        # Visualization
        'plotly',
        'plotly.graph_objs',
        'plotly.graph_objects',
        'plotly.io',

        # Excel export
        'openpyxl',
        'openpyxl.styles',
        'openpyxl.drawing',
        'openpyxl.drawing.image',
        'openpyxl.utils',
        'openpyxl.utils.dataframe',
        'kaleido',
        'choreographer',
        'logistro',

        # Date handling
        'dateutil',
        'dateutil.parser',

        # Web server
        'tornado',
        'tornado.web',
        'tornado.ioloop',
        'tornado.websocket',

        # Utilities
        'click',
        'blinker',
        'cachetools',
        'validators',
        'watchdog',
        'altair',
        'PIL',
        'PIL.Image',

        # Application modules
        'fund_simulation',
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
    excludes=[
        'matplotlib',
        'scipy',
        'IPython',
        'jupyter',
        'notebook',
        'pytest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Create single-file executable
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='MonteCarloFundSimulation',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Show console for server output
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if Path('icon.ico').exists() else None,
)
