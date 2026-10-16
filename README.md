# Farm Bandit

A hungry bunny raids the farm by night, carrying crops back to its burrow to
fill an order before dawn. Written in Python with pygame.

## Play

    pip install -r requirements.txt
    python farmgame.py        (or double-click start.bat)

Keyboard: arrows/WASD hop, Space picks a ripe crop, E eats, P or Esc pauses.
Gamepad (SNES letters): D-pad or stick hops, B picks, A eats, Start or L/R
pauses. While paused, B, Start or L/R resume and Select quits to the title.
Buttons go by position, so on an Xbox pad it's A to pick and B to eat.

## Make changes

- Farms: `levels.py` (map legend at the top). Run `python tools/check_levels.py` after editing.
- Crops: `crops.py`. Sprites: `sprites.data`. Sounds: `sound.py`.
- Tuning numbers: `globals.py` and `settings.py` (difficulty).
- Synthesized sound effects: `python tools/make_sounds.py` (needs numpy).

## Release

    python build.py           -> dist/FarmBandit/FarmBandit.exe
                                 dist/FarmBandit-Setup.exe (needs Inno Setup 6)

The installer puts the game in Program Files, adds Start menu and optional
desktop shortcuts, and registers an uninstaller. Install Inno Setup once with
`winget install JRSoftware.InnoSetup`; without it only the folder is built.

## License

Farm Bandit's code is free software under the GNU General Public License v3
(see `LICENSE`). The art, sound, music, and font are by other people and keep
their own licenses (CC0, CC-BY, CC-BY-SA, OGA-BY, OFL); see `CREDITS.txt` for
who made what and `licenses/` for third-party licenses.
