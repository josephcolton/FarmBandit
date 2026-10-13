"""Check every farm map for mistakes.

Run from the game folder:  python tools/check_levels.py
"""
import os
import sys
from collections import deque

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from globals import map_width, map_height
from crops import cropLetters, cropTypes
import levels

blocked = "TC=^B"
known = set(".:TCH=^B,DFR") | set(cropLetters)


def reachable(layout, start, dog=False):
    seen = {start}
    queue = deque([start])
    while queue:
        (x, y) = queue.popleft()
        for (dx, dy) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            (nx, ny) = (x + dx, y + dy)
            if not (0 <= nx < map_width and 0 <= ny < map_height) or (nx, ny) in seen: continue
            tile = layout[ny][nx]
            if tile in blocked or (dog and tile == "H"): continue
            seen.add((nx, ny))
            queue.append((nx, ny))
    return seen


def checkLevel(number, level):
    problems = []
    layout = level.layout
    if len(layout) != map_height:
        return ["has %d rows, needs %d" % (len(layout), map_height)]
    for y, row in enumerate(layout):
        if len(row) != map_width:
            problems.append("row %d is %d wide, needs %d" % (y, len(row), map_width))
        for x, char in enumerate(row):
            if char not in known:
                problems.append("unknown map letter %r at (%d, %d)" % (char, x, y))
    if problems: return problems

    tiles = {(x, y): layout[y][x] for y in range(map_height) for x in range(map_width)}
    burrows = [p for p, t in tiles.items() if t == "H"]
    if len(burrows) != 1:
        return ["needs exactly one burrow H, found %d" % len(burrows)]
    burrow = burrows[0]
    (bx, by) = burrow
    if by + 1 >= map_height or layout[by + 1][bx] in blocked:
        problems.append("the tile below the burrow is blocked")
    if layout[by - 1][bx] not in "TC" if by > 0 else False:
        problems.append("the burrow should be in a cliff face")

    canReach = reachable(layout, burrow)
    for (pos, tile) in tiles.items():
        if tile in cropLetters and pos not in canReach:
            problems.append("%s at %s can't be reached from the burrow" % (cropLetters[tile], pos))
        if tile in "DFR" and pos not in reachable(layout, burrow):
            problems.append("%s at %s is walled off" % ({"D": "dog", "F": "farmer", "R": "rooster"}[tile], pos))
        if tile == "B" and pos[1] == 0:
            problems.append("hay bale at %s is on the top row (it's drawn two tiles tall)" % (pos,))

    # Enough of each crop, unless the level says it's scarce on purpose
    counts = {}
    for tile in tiles.values():
        if tile in cropLetters: counts[cropLetters[tile]] = counts.get(cropLetters[tile], 0) + 1
    for kind, need in level.order.items():
        if kind not in cropTypes:
            problems.append("order asks for unknown crop %r" % kind)
            continue
        have = counts.get(kind, 0)
        if have == 0:
            problems.append("order needs %s but none are planted" % kind)
        elif have < need and kind not in level.scarce:
            problems.append("order needs %d %s but only %d are planted (add it to scarce= if on purpose)" % (need, kind, have))
        elif have >= need and kind in level.scarce:
            problems.append("%s is marked scarce but there are %d spots for %d" % (kind, have, need))

    # Tall grass looks best in patches at least 2x2
    for (x, y), tile in tiles.items():
        if tile != ",": continue
        def grass(gx, gy): return tiles.get((gx, gy)) == ","
        if not (grass(x - 1, y) or grass(x + 1, y)) or not (grass(x, y - 1) or grass(x, y + 1)):
            problems.append("tall grass at (%d, %d) isn't part of a 2x2 patch" % (x, y))
    return problems


def main():
    bad = 0
    for number, level in enumerate(levels.levels, 1):
        problems = checkLevel(number, level)
        scarce = ", ".join(level.scarce)
        status = "OK" if not problems else "PROBLEMS"
        print("%2d. %-26s %s%s" % (number, level.name, status, ("  (scarce: %s)" % scarce) if scarce else ""))
        for problem in problems:
            print("      - " + problem)
        bad += len(problems)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
