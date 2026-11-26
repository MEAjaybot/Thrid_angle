import subprocess
import os

# full path to FreeCAD.exe (the GUI one, NOT FreeCADCmd.exe)
FREECAD_EXE = r"C:\Program Files\FreeCAD 1.1\bin\FreeCADCmd.exe\bin\FreeCADCmd.exe"
MAIN_SCRIPT = r"D:\AUTO\Projection\main.py"

if not os.path.isfile(FREECAD_EXE):
    raise SystemExit("FreeCAD.exe not found: " + FREECAD_EXE)

print("Starting FreeCAD, please wait...")
subprocess.run([FREECAD_EXE, MAIN_SCRIPT], check=False)
print("Finished. See D:\\AUTO\\Projection\\log.txt")