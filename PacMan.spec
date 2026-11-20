import sys

# ============================================================
# 1. ANALYZE THE APPLICATION
# ============================================================

a = Analysis(
    ['pac_man.py'],
    datas=[('assets', 'assets')],
)


# ============================================================
# 2. CREATE THE PYTHON MODULE ARCHIVE
# ============================================================

pyz = PYZ(a.pure)


# ============================================================
# 3. SELECT THE PLATFORM ICON
# ============================================================

if sys.platform == "win32":
    app_icon = "assets/icons/win.ico"
elif sys.platform == "darwin":
    app_icon = "assets/icons/ios.icns"
else:
    app_icon = None


# ============================================================
# 4. BUILD THE APPLICATION
# ============================================================

if sys.platform == "darwin":

    # macOS: onedir app bundle
    exe = EXE(
        pyz,
        a.scripts,
        exclude_binaries=True,
        name='PacMan',
    )

    coll = COLLECT(
        exe,
        a.binaries,
        a.datas,
        name='PacMan',
    )

    app = BUNDLE(
        coll,
        name='PacMan.app',
        icon=app_icon,
        bundle_identifier='com.Roy-ALPHA.pacman',
    )

else:

    # Linux / Windows: onefile standalone executable
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        name='PacMan',
        icon=app_icon,
    )
