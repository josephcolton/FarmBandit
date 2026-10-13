import json
import os
import shutil
import sys


def userDataDir():
    # Saves go in the player's own folder, never the game folder (a new release may replace that).
    # On Windows it's %APPDATA%/FarmBandit.
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    path = os.path.join(base, "FarmBandit")
    try:
        os.makedirs(path, exist_ok=True)
    except OSError:
        path = "."
    return path


data_dir = userDataDir()
settings_file = os.path.join(data_dir, "settings.json")
highscores_file = os.path.join(data_dir, "highscores.json")
max_high_scores = 10


def migrateOldSaves():
    # Earlier versions saved next to the game; move those files to the new folder once
    for name, new in (("settings.json", settings_file), ("highscores.json", highscores_file)):
        if os.path.exists(name) and not os.path.exists(new) and os.path.abspath(name) != os.path.abspath(new):
            try:
                shutil.copyfile(name, new)
            except OSError:
                pass

display_modes = ["windowed", "borderless", "fullscreen"]
display_labels = {"windowed": "Windowed", "borderless": "Windowed Full", "fullscreen": "Fullscreen"}

###############
# Difficulty  #
###############
# step:   dog and farmer step time multiplier (bigger is slower)
# sight:  tiles added to dog and farmer sight
# hunger: hunger rate multiplier
# night:  night length multiplier
difficulties = ["easy", "normal", "hard"]
difficulty_settings = {
    "easy":   {"label": "Easy",   "step": 1.15, "sight": -1, "hunger": 0.75, "night": 1.25, "lives": 4},
    "normal": {"label": "Normal", "step": 1.0,  "sight": 0,  "hunger": 1.0,  "night": 1.0,  "lives": 3},
    "hard":   {"label": "Hard",   "step": 0.88, "sight": 1,  "hunger": 1.25, "night": 0.85, "lives": 3},
}

default_settings = {
    "sound": 4,          # 0 to 5
    "music": 3,          # 0 to 5
    "display": "windowed",
    "difficulty": "normal",
    "name": "Bunny",     # last name typed for a high score
    "unlocked": 1,       # farms reached so far (farm select)
}


def loadJson(filename, default):
    try:
        with open(filename, "r") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


def saveJson(filename, data):
    try:
        with open(filename, "w") as fh:
            json.dump(data, fh, indent=2)
    except OSError:
        pass  # Not being able to save shouldn't stop the game


def loadSettings():
    settings = dict(default_settings)
    saved = loadJson(settings_file, {})
    if isinstance(saved, dict):
        settings.update({k: v for k, v in saved.items() if k in default_settings})
    # Guard against hand-edited files
    settings["sound"] = max(0, min(5, int(settings["sound"])))
    settings["music"] = max(0, min(5, int(settings["music"])))
    if settings["display"] not in display_modes: settings["display"] = "windowed"
    if settings["difficulty"] not in difficulties: settings["difficulty"] = "normal"
    try:
        settings["unlocked"] = max(1, int(settings["unlocked"]))
    except (TypeError, ValueError):
        settings["unlocked"] = 1
    return settings


def saveSettings(settings):
    saveJson(settings_file, settings)


################
# High Scores  #
################
def loadHighScores():
    scores = loadJson(highscores_file, [])
    if not isinstance(scores, list): return []
    scores = [s for s in scores if isinstance(s, dict) and "name" in s and "score" in s]
    return sorted(scores, key=lambda s: -s["score"])[:max_high_scores]


def isHighScore(score):
    if score <= 0: return False
    scores = loadHighScores()
    return len(scores) < max_high_scores or score > scores[-1]["score"]


def addHighScore(name, score, farm, difficulty):
    # Returns the new entry's rank (0 is first place)
    scores = loadHighScores()
    entry = {"name": name, "score": score, "farm": farm, "difficulty": difficulty}
    scores.append(entry)
    scores.sort(key=lambda s: -s["score"])
    scores = scores[:max_high_scores]
    saveJson(highscores_file, scores)
    return scores.index(entry) if entry in scores else None
