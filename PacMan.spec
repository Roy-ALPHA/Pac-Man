
import sys

# Analyze the application and collect its dependencies and data files.
a = Analysis(
    ['pac_man.py'],  # Main Python entry point of the game.

    datas=[
        ('assets', 'assets'),  # Bundle the project's assets folder into the application.
    ],
)

# Package pure Python modules into a PYZ archive.
pyz = PYZ(a.pure)

# Select the appropriate application icon for the target operating system.
if sys.platform == "win32":
    app_icon = "assets/win.ico"   # Windows icon format.
elif sys.platform == "darwin":
    app_icon = "assets/ios.icns"  # macOS icon format.
else:
    app_icon = None                # No embedded icon for Linux.


# Build the final executable.
exe = EXE(
    pyz,            # Archive containing pure Python modules.
    a.scripts,      # Application entry-point scripts.
    a.binaries,     # Collected compiled libraries and binary dependencies.
    a.datas,        # Collected data files, including game assets.
    [],             # Additional files to include (none for now).

    name='PacMan',  # Name of the generated executable.

    icon=app_icon,  # Icon selected for the target operating system.

    debug=False,    # Disable PyInstaller bootloader debugging.
    bootloader_ignore_signals=False,  # Do not ignore operating-system signals.
    strip=False,    # Keep debugging symbols in collected binaries.
    upx=False,      # Do not compress binaries with UPX.
    console=True,   # Keep a console available for logs and error messages.
    disable_windowed_traceback=False,  # Allow windowed traceback reporting.
)
