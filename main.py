import os
import sys
import importlib
import FreeCAD as App

SCRIPT_DIR = r"D:\AUTO\Projection"
INPUT_DIR = r"D:\AUTO\Projection\input"
OUTPUT_DIR = r"D:\AUTO\Projection\output"
LOG_FILE = r"D:\AUTO\Projection\log.txt"
UP_OFFSET = 30
DPI = 300
QUIT_WHEN_DONE = False

TOP, FRONT, RIGHT = "TopView", "FrontView", "RightView"

if SCRIPT_DIR not in sys.path:
    sys.path.append(SCRIPT_DIR)

log = open(LOG_FILE, "w", encoding="utf-8")


def say(*a):
    msg = " ".join(str(x) for x in a)
    print(msg)
    log.write(msg + "\n")
    log.flush()


def find(doc, name):
    obj = doc.getObject(name)
    if obj is None:
        m = doc.getObjectsByLabel(name)
        obj = m[0] if m else None
    return obj


def process_all():
    import convert
    importlib.reload(convert)

    files = []
    for root, dirs, names in os.walk(INPUT_DIR):
        for n in names:
            if n.lower().endswith(".fcstd"):
                files.append(os.path.join(root, n))
    say("Found", len(files), "file(s)")

    for i, path in enumerate(files, 1):
        rel = os.path.relpath(path, INPUT_DIR)
        base = os.path.join(OUTPUT_DIR, os.path.splitext(rel)[0])
        doc = None
        try:
            doc = App.openDocument(path)
            top = find(doc, TOP)
            front = find(doc, FRONT)
            right = find(doc, RIGHT)

            if top is None or front is None:
                say(f"[{i}/{len(files)}] SKIPPED (views not found):", rel)
                continue

            locks = (top.LockPosition, front.LockPosition)
            top.LockPosition = False
            front.LockPosition = False
            top.Y, front.Y = front.Y, top.Y
            top.Y = top.Y.Value + UP_OFFSET
            front.Y = front.Y.Value + UP_OFFSET
            top.LockPosition, front.LockPosition = locks

            d = front.Direction
            front.Direction = App.Vector(-d.x, -d.y, -d.z)

            if right is not None:
                doc.removeObject(right.Name)

            doc.recompute()

            if convert.page_to_png(doc, base + ".png", DPI):
                say(f"[{i}/{len(files)}] OK:", rel)
            else:
                say(f"[{i}/{len(files)}] SKIPPED (no page):", rel)
        except Exception as e:
            say(f"[{i}/{len(files)}] ERROR in", rel, ":", e)
        finally:
            if doc is not None:
                App.closeDocument(doc.Name)

    say("Done")


try:
    process_all()
except Exception as e:
    say("FATAL:", e)
finally:
    log.close()
    if QUIT_WHEN_DONE:
        os._exit(0)   # closes FreeCAD