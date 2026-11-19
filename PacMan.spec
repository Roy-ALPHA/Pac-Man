
import sys

# ============================================================
# 1. ANALYZE THE APPLICATION
# ============================================================

# Collect the Python scripts, imported modules, binary
# dependencies, and data files required by the game.

a = Analysis(
    ['pac_man.py'],  # Main entry-point script.
    datas=[
        ('assets', 'assets'),
        # Include the assets directory in the packaged game.
        # Destination: assets/
    ],
)


# ============================================================
# 2. CREATE THE PYTHON MODULE ARCHIVE
# ============================================================

# Package pure Python modules discovered during Analysis.
# This contains Python bytecode, not native machine code.

pyz = PYZ(a.pure)


# ============================================================
# 3. SELECT THE PLATFORM ICON
# ============================================================

if sys.platform == "win32":

    app_icon = "assets/icons/win.ico"
    # Windows application icon (.ico).

elif sys.platform == "darwin":

    app_icon = "assets/icons/ios.icns"
    # macOS application icon (.icns).
    # Consider renaming ios.icns to macos.icns for clarity.

else:

    app_icon = None
    # No embedded application icon for Linux.


# ============================================================
# 4. BUILD THE APPLICATION
# ============================================================

if sys.platform == "darwin":

    # --------------------------------------------------------
    # MACOS: ONEDIR BUILD
    # --------------------------------------------------------

    exe = EXE(
        pyz,          # Archive containing pure Python modules.

        a.scripts,    # Application entry-point scripts.

        [],           # No binaries passed directly to EXE.
                      # They will be collected separately.

        exclude_binaries=True,
        # Keep binary dependencies outside the executable.

        name='PacMan',  # Name of the executable inside the app bundle.

        debug=False,    # Disable bootloader debugging.

        bootloader_ignore_signals=False,
        # Preserve normal operating-system signal handling.

        strip=False,    # Do not strip debugging symbols.

        upx=False,      # Do not compress binaries with UPX.

        console=True,  # No terminal window for the graphical game.

        disable_windowed_traceback=False,
        # Keep windowed traceback reporting enabled.
    )

    # Collect the executable, native libraries and data files.
    # This creates the onedir application structure.

    coll = COLLECT(
        exe,

        a.binaries,  # Native libraries and binary dependencies.

        a.datas,     # Game assets and other data files.

        strip=False, # Do not strip collected binaries.

        upx=False,   # Do not compress collected binaries.

        name='PacMan',
    )

    # Wrap the collected application in a macOS .app bundle.

    app = BUNDLE(
        coll,

        name='PacMan.app',

        icon=app_icon,

        bundle_identifier='com.Roy-ALPHA.pacman',
        # Replace this placeholder with your own unique identifier.
    )


else:

    # --------------------------------------------------------
    # LINUX / WINDOWS: ONEFILE BUILD
    # --------------------------------------------------------

    exe = EXE(
        pyz,          # Archive containing pure Python modules.

        a.scripts,    # Application entry-point scripts.

        a.binaries,   # Native libraries and binary dependencies.

        a.datas,      # Game assets and other data files.

        [],           # Additional files to include manually.

        name='PacMan',  # Output executable name.

        icon=app_icon,  # Platform-specific icon.

        debug=False,    # Disable bootloader debugging.

        bootloader_ignore_signals=False,
        # Preserve normal operating-system signal handling.

        strip=False,    # Keep debugging symbols.

        upx=False,      # Disable UPX compression.

        console=True,   # Keep terminal output for debugging.

        disable_windowed_traceback=False,
        # Allow windowed traceback reporting.
    )
