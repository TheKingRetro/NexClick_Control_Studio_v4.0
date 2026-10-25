NEXCLICK CONTROL STUDIO v4.0
=============================

This version includes a redesigned dark interface and a custom NexClick icon.

Reliability improvements:
- Snapshots click settings before the worker starts, instead of reading Tkinter controls from a background thread.
- Debounces keyboard hotkeys so OS key-repeat does not repeatedly toggle Start/Stop.
- Uses a stop event and a single worker completion path.
- Validates timing, random offset, repeat count, and fixed coordinates before starting.
- Handles worker exceptions and reports them in the UI.
- Records and replays the actual recorded mouse button when supported.

Install and run:
1. Extract the ZIP to a normal folder.
2. Run INSTALL_AND_LAUNCH.bat.
3. Use Hotkey settings and press a keyboard key or X1/X2.

Build a standalone EXE:
1. Run BUILD_EXE_WITH_ICON.bat.
2. The executable will be created in the dist folder with the NexClick icon.

Notes:
- X1/X2 hotkey detection depends on the mouse driver and whether Windows exposes those side buttons to pynput.
- Sending X1/X2 clicks is supported only if the installed pynput backend exposes those buttons.
- Record & playback is a basic mouse-click recorder; it does not record keyboard input or pointer movement between clicks.
- This project has been syntax-checked, but cannot be hardware-tested against your specific mouse from here.
