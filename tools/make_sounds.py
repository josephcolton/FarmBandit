"""Generate the synthesized sound effects for Farm Bandit.

Run from the game folder:  python tools/make_sounds.py
Needs numpy (the game itself does not).
"""
import os
import wave
import numpy as np

rate = 44100
out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sounds")
rng = np.random.default_rng(7)


def save(name, samples):
    samples = np.clip(samples, -1, 1)
    data = (samples * 32767 * 0.8).astype(np.int16)
    with wave.open(os.path.join(out_dir, name), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(rate)
        f.writeframes(data.tobytes())
    print("wrote", name)


def timeline(seconds):
    return np.arange(int(rate * seconds)) / rate


def envelope(t, attack, release):
    # Quick fade in and out so sounds don't click
    env = np.ones_like(t)
    a = int(attack * rate)
    r = int(release * rate)
    if a: env[:a] = np.linspace(0, 1, a)
    if r: env[-r:] = np.linspace(1, 0, r)
    return env


def sweep(t, f0, f1):
    # Sine wave gliding from f0 to f1
    freq = np.linspace(f0, f1, len(t))
    return np.sin(2 * np.pi * np.cumsum(freq) / rate)


def lowpass(x, width):
    return np.convolve(x, np.ones(width) / width, mode="same")


# Farmer's whistle: two notes, the second sliding up, with a little breath
t1 = timeline(0.18)
t2 = timeline(0.45)
vibrato = 1 + 0.01 * np.sin(2 * np.pi * 28 * t2)
note1 = sweep(t1, 1900, 2100) * envelope(t1, 0.02, 0.04)
note2 = np.sin(2 * np.pi * np.cumsum(np.linspace(1700, 2600, len(t2)) * vibrato) / rate) * envelope(t2, 0.03, 0.12)
gap = np.zeros(int(rate * 0.05))
whistle = np.concatenate([note1, gap, note2])
whistle += lowpass(rng.normal(0, 0.08, len(whistle)), 4) * (np.abs(whistle) > 0.01)
save("whistle.wav", whistle * 0.7)

# Pop when a crop is pulled from the ground
t = timeline(0.12)
pop = sweep(t, 250, 900) * envelope(t, 0.002, 0.08)
pop[:300] += rng.normal(0, 0.4, 300) * np.linspace(1, 0, 300)
save("pick.wav", pop)

# Munching: three soft crunchy bites
bites = []
for i in range(3):
    t = timeline(0.07)
    crunch = lowpass(rng.normal(0, 0.6, len(t)), 6) * envelope(t, 0.003, 0.05)
    bites.append(crunch)
    bites.append(np.zeros(int(rate * 0.09)))
save("munch.wav", np.concatenate(bites))


def bawk(length, f0, f1):
    # A raspy chicken call: buzzy tone with a falling pitch
    t = timeline(length)
    freq = np.linspace(f0, f1, len(t))
    phase = np.cumsum(freq) / rate
    buzz = 2 * (phase % 1) - 1
    buzz = lowpass(buzz, 3) + rng.normal(0, 0.15, len(t))
    return buzz * envelope(t, 0.01, length * 0.6) * 0.6

# Rooster spots the bunny: quick "buk-buk"
cluck = np.concatenate([bawk(0.07, 700, 520), np.zeros(int(rate * 0.05)), bawk(0.08, 760, 540)])
save("cluck.wav", cluck)

# Rooster pecks the bunny: loud squawk
save("squawk.wav", np.concatenate([bawk(0.08, 600, 900), bawk(0.28, 1000, 450)]))

# Rat nibbling: two tiny high squeaks
squeak = []
for f0, f1 in ((2600, 3400), (2900, 3800)):
    t = timeline(0.06)
    squeak.append(sweep(t, f0, f1) * envelope(t, 0.005, 0.03) * 0.5)
    squeak.append(np.zeros(int(rate * 0.04)))
save("squeak.wav", np.concatenate(squeak))
