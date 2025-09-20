
# iot-yolo-blynk — ESP8266 + YOLOv3 person detection with Blynk logging & email alerts

This repository (iot-yolo-blynk) contains two related projects used in a compact IoT object/person detection system:

- `Blink/` - an ESP8266 (NodeMCU/WeMos) sketch that receives serial messages and updates a Blynk app.
- `yolo_exp/` - Python scripts that run YOLOv3 using OpenCV DNN, send notifications (Blynk + email), generate heatmaps, and forward status/logs to the ESP via serial.

This repo has been prepared for publishing to GitHub. Sensitive credentials are removed from the main sources and an example `.env` and `Blink/secrets.h.example` are provided.

## Quick structure

- Blink/
  - `Blink.ino` - ESP8266 code (uses `secrets.h` for Wi-Fi/Blynk tokens)
  - `secrets.h.example` - example secrets header (do not commit the real one)
- yolo_exp/
  - `yolo.py` - main detector, Blynk + email + serial integration
  - `yolov3.weights`, `yolov3.cfg`, `coco.names` - model files and classes
  - `requirements.txt` - Python dependencies
  - `.env.example` - environment variables example

## Security note
- Do NOT commit your real Wi-Fi credentials, Blynk token, or email password. Use environment variables or a secrets header for the ESP and add those files to `.gitignore`.

## How to run the Python detector (basic)

1. Create and activate a Python virtual environment in `yolo_exp`:

```powershell
cd yolo_exp
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and fill the values (BLYNK_TOKEN, EMAIL_ADDRESS, EMAIL_PASSWORD, OWNER_EMAIL, SERIAL_PORT, SERIAL_BAUD).

3. Run the detector:

```powershell
python yolo.py
```

4. On the ESP side, add your real `secrets.h` (based on `secrets.h.example`) and upload `Blink.ino` to your board.

## Recommended immediate changes before pushing
- Move real credentials to environment variables and never commit them.
- Verify serial port and baud rate match between `Blink.ino` and `yolo.py`.
- Consider removing `yolov3.weights` from the repository and using Git LFS if keeping large files in Git.

## Next improvements
- Add a CI lint step (optional), tests for the Python scripts, and a small integration test that runs a single frame detection.
- Add instructions for using a GPU (if you plan to accelerate inference).

If you want, I can now add or update the `.env` values, write the `requirements.txt`, and finalize small code changes (baud fix and env loading). Tell me which items you want me to apply next.
