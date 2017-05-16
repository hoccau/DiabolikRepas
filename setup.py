import sys, os
from cx_Freeze import setup, Executable

VERSION = "0.0.2"

if sys.platform == "win32":
	base = "Win32GUI"
else:
        base = None
		
shortcut_table = [
    ("DesktopShortcut",        # Shortcut
     "DesktopFolder",          # Directory_
     "Diabolik Repas",           # Name
     "TARGETDIR",              # Component_
     "[TARGETDIR]main.exe",# Target
     None,                     # Arguments
     None,                     # Description
     None,                     # Hotkey
     None,                     # Icon
     None,                     # IconIndex
     None,                     # ShowCmd
     'TARGETDIR'               # WkDir
     )
    ]
msi_data = {'Shortcut':shortcut_table}

options = {'build_exe': {
        "excludes": [],
        "includes": [],
        "include_files": ['design', 'create_db.sql', 'repas_previsionnels', 'repas.xsd'],
        "optimize": 2},
		'bdist_msi':{'data': msi_data}
         }

setup(  name = "DiabolikRepas",
        version = VERSION,
        description = "Diabolik Repas",
        options = options,
        executables = [Executable("main.py",
                                  base=base,
                                  icon="icon.ico",
                                  shortcutName="Diabolik Repas",
                                  shortcutDir="DesktopFolder",
                                  copyright="Kidivid")])
