"""Build Farm Bandit for release (Windows).

    python build.py

Creates a private build environment (.venv-build) with pinned pygame and
PyInstaller, then builds dist/FarmBandit/FarmBandit.exe. That whole
dist/FarmBandit folder is the release; zip it up to share.

If Inno Setup 6 is installed, it also builds dist/FarmBandit-Setup.exe, an
installer that puts the game in Program Files with Start menu and desktop
shortcuts and an uninstaller. Without Inno Setup that step is skipped.

Only files the game actually uses are packaged: sheets named in sprites.data,
sounds named in sound.py, the music, fonts, and every credits/license file.
"""
import os
import re
import shutil
import subprocess
import sys

here = os.path.dirname(os.path.abspath(__file__))
venv = os.path.join(here, ".venv-build")
dist = os.path.join(here, "dist")
app_name = "FarmBandit"


def run(cmd):
    print(">", " ".join(cmd[:6]), "..." if len(cmd) > 6 else "")
    subprocess.check_call(cmd, cwd=here)


def venvPython():
    return os.path.join(venv, "Scripts" if os.name == "nt" else "bin", "python")


def setupEnvironment():
    if not os.path.exists(venvPython()):
        run([sys.executable, "-m", "venv", venv])
    run([venvPython(), "-m", "pip", "install", "--quiet", "--upgrade", "pip"])
    run([venvPython(), "-m", "pip", "install", "--quiet", "-r", "requirements-build.txt"])


def dataFiles():
    # Every file the game loads, plus all credit and license files
    files = ["sprites.data", "sprites/icon.png", "CREDITS.txt"]
    for line in open(os.path.join(here, "sprites.data")):
        parts = line.strip().split(":")
        if len(parts) >= 3 and parts[0] == "sheet":
            files.append("sprites/" + parts[2])
    sys.path.insert(0, here)
    import sound
    for (names, loudness) in sound.sound_list.values():
        files += ["sounds/" + name for name in names]
    files += ["music/" + name for name in sound.music_list.values()]
    files += ["fonts/" + name for name in os.listdir(os.path.join(here, "fonts"))]
    for folder, _, names in os.walk(os.path.join(here, "sprites")):
        for name in names:
            if re.match(r"CREDITS.*\.txt$", name) or name == "readme.txt":
                files.append(os.path.relpath(os.path.join(folder, name), here).replace(os.sep, "/"))
    files += ["sounds/CREDITS-sounds.txt", "music/CREDITS-music.txt"]
    missing = [f for f in files if not os.path.exists(os.path.join(here, f))]
    if missing:
        sys.exit("Missing files: %s" % missing)
    return sorted(set(files))


def build():
    setupEnvironment()
    files = dataFiles()
    args = [venvPython(), "-m", "PyInstaller", "farmgame.py",
            "--name", app_name, "--onedir", "--windowed", "--noconfirm", "--clean",
            "--icon", os.path.join(here, "sprites", "icon.ico"),
            "--distpath", dist, "--workpath", os.path.join(here, "build"),
            "--specpath", os.path.join(here, "build")]
    sep = ";" if os.name == "nt" else ":"
    for f in files:
        args += ["--add-data", "%s%s%s" % (os.path.join(here, f), sep, os.path.dirname(f) or ".")]
    run(args)
    # Credits and licenses where players can find them, next to the .exe
    out = os.path.join(dist, app_name)
    shutil.copy(os.path.join(here, "CREDITS.txt"), out)
    shutil.copy(os.path.join(here, "LICENSE"), os.path.join(out, "LICENSE.txt"))
    shutil.copytree(os.path.join(here, "licenses"), os.path.join(out, "licenses"), dirs_exist_ok=True)
    size = sum(os.path.getsize(os.path.join(d, f)) for d, _, fs in os.walk(out) for f in fs)
    print("\nBuilt %s (%d files packaged, %.1f MB)" % (os.path.join(out, app_name + ".exe"), len(files), size / 1e6))


def findInnoSetup():
    # ISCC.exe is the Inno Setup compiler; winget may install it machine-wide or per-user
    found = shutil.which("iscc")
    if found:
        return found
    for base in ("ProgramFiles(x86)", "ProgramFiles", "LOCALAPPDATA"):
        root = os.environ.get(base)
        if not root:
            continue
        for sub in ("Inno Setup 6", os.path.join("Programs", "Inno Setup 6")):
            path = os.path.join(root, sub, "ISCC.exe")
            if os.path.exists(path):
                return path
    return None


def gameVersion():
    match = re.search(r'^version = "(.+)"', open(os.path.join(here, "farmgame.py")).read(), re.M)
    return match.group(1)


def buildInstaller():
    iscc = findInnoSetup()
    if not iscc:
        print("\nInno Setup 6 not found, so no installer was built (the dist/%s folder is still usable)." % app_name)
        print("Install it with: winget install JRSoftware.InnoSetup")
        return
    script = os.path.join(here, "build", app_name + ".iss")
    with open(script, "w") as fh:
        fh.write(installer_script % {
            "name": app_name,
            "version": gameVersion(),
            "source": os.path.join(dist, app_name),
            "icon": os.path.join(here, "sprites", "icon.ico"),
            "output": dist,
        })
    run([iscc, "/Q", script])
    print("Built %s" % os.path.join(dist, app_name + "-Setup.exe"))


# Inno Setup script: installs to Program Files, with Start menu and optional desktop shortcuts.
# AppId identifies the game to Windows across versions; never change it.
installer_script = r"""
[Setup]
AppId={{C243FDF9-FBA7-4698-ADA4-D9C342891E95}
AppName=Farm Bandit
AppVersion=%(version)s
AppPublisher=Joseph Colton
DefaultDirName={autopf}\%(name)s
DefaultGroupName=Farm Bandit
DisableProgramGroupPage=yes
SetupIconFile=%(icon)s
UninstallDisplayIcon={app}\%(name)s.exe
OutputDir=%(output)s
OutputBaseFilename=%(name)s-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "%(source)s\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\Farm Bandit"; Filename: "{app}\%(name)s.exe"
Name: "{autodesktop}\Farm Bandit"; Filename: "{app}\%(name)s.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\%(name)s.exe"; Description: "{cm:LaunchProgram,Farm Bandit}"; Flags: nowait postinstall skipifsilent
"""


if __name__ == "__main__":
    build()
    buildInstaller()
