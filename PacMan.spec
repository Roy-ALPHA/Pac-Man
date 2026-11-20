import sys

# ============================================================
# 1. ANALYZE THE APPLICATION
# ============================================================

# Analysis collects Python scripts, module dependencies, binary libraries,
# and static data files required to run the game.
a = Analysis(
    ['pac_man.py'],  # Main entry-point Python script of the game.
    datas=[
        ('assets', 'assets'),  # Bundle the 'assets' directory into 'assets/' in the package.
    ],
)


# ============================================================
# 2. CREATE THE PYTHON MODULE ARCHIVE
# ============================================================

# PYZ packages all pure Python bytecode modules discovered during Analysis
# into a compressed zip archive.
pyz = PYZ(
    a.pure,  # Pure Python modules (bytecode) discovered by Analysis.
)


# ============================================================
# 3. SELECT THE PLATFORM ICON
# ============================================================

if sys.platform == "win32":
    app_icon = "assets/icons/win.ico"   # Windows icon file (.ico).
elif sys.platform == "darwin":
    app_icon = "assets/icons/ios.icns"  # macOS icon file (.icns).
else:
    app_icon = None                     # Linux binaries do not embed icon files directly.


# ============================================================
# 4. BUILD THE APPLICATION
# ============================================================

if sys.platform == "darwin":

    # --------------------------------------------------------
    # MACOS: ONEDIR APPLICATION BUNDLE (.app)
    # --------------------------------------------------------

    # EXE compiles the bootloader and packages the startup scripts.
    exe = EXE(
        pyz,                    # Python bytecode archive.
        a.scripts,              # Entry-point scripts executed at launch.
        exclude_binaries=True,  # Leave dynamic binaries out so COLLECT places them into the bundle.
        name='PacMan',          # Name of the executable file inside the bundle.
    )

    # COLLECT gathers the executable, shared libraries, and assets into a folder.
    coll = COLLECT(
        exe,                    # The compiled executable from the EXE step.
        a.binaries,             # Dynamic libraries and C extensions required by dependencies.
        a.datas,                # Game static assets (sprites, sounds, maps, fonts).
        name='PacMan',          # Output directory name containing the collected files.
    )

    # BUNDLE packages the collected directory into a standard macOS .app application bundle.
    app = BUNDLE(
        coll,                                       # The collected directory structure from the COLLECT step.
        name='PacMan.app',                          # Final application bundle folder name.
        icon=app_icon,                              # App bundle icon (.icns).
        bundle_identifier='com.Roy-ALPHA.pacman',  # Unique reverse-DNS identifier for macOS.
    )

else:

    # --------------------------------------------------------
    # LINUX / WINDOWS: ONEFILE STANDALONE EXECUTABLE
    # --------------------------------------------------------

    # EXE bundles the bootloader, bytecode, libraries, and assets into a single executable file.
    exe = EXE(
        pyz,            # Python bytecode archive.
        a.scripts,      # Entry-point scripts executed at launch.
        a.binaries,     # Native shared libraries packed directly into the single executable.
        a.datas,        # Game static assets packed directly into the single executable.
        name='PacMan',  # Output executable filename (PyInstaller appends .exe on Windows).
        icon=app_icon,  # Embedded executable icon (.ico on Windows, ignored on Linux).
    )
