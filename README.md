Virtual Eye and Hand Controlled Mouse

This repository contains a Python prototype that provides four functions via a simple Tkinter GUI:

- Volume Control (hand distance)
- Virtual Mouse Control (hand index finger moves pointer + thumb pinch to click)
- Eye-Controlled Mouse (gaze-based pointer using Face Mesh)
- Capture Photo (captures an image after a short delay)

Files
- `virtual_mouse.py`: Main script with the GUI and three control modes.
- `requirements.txt`: Python dependencies.

Setup (Windows)
1. Create and activate a Python virtual environment (optional but recommended):

SURYA


```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

Run

```powershell
python virtual_mouse.py
```

Notes
- The script uses your webcam. Close the OpenCV windows or press ESC to stop a mode.
- On Windows, `pyautogui` may require disabling the fail-safe or adjusting permissions for controlling the mouse.
- If `mediapipe` installation fails on your Python version, install a compatible version (Python 3.8-3.11 recommended).

If you want, I can run the install and launch the app now and report back any errors. Tell me to proceed and I'll run the commands in the integrated terminal.