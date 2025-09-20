# YOLO Experiment - local instructions

This folder contains the Python-based object/person detection scripts.

Prerequisites
- Python 3.8+
- A webcam accessible as device 0
- Install dependencies: `pip install -r requirements.txt`

Quick start

1. Create `.env` from `.env.example` and fill in values:

```
copy .env.example .env
```

2. Create a virtualenv, activate it and install deps:

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

3. Run the main detector:

```powershell
python yolo.py
```

Notes
- If running on Windows, ensure the `SERIAL_PORT` in `.env` matches the COM port of your ESP device.
- If you don't want to use serial/ESP, leave `SERIAL_PORT` empty in `.env` or unplug the device — the script will continue but skip serial writes.
