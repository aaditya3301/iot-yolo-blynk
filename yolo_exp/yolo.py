
import cv2
import numpy as np
import requests
from datetime import datetime
import serial
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import threading
import pyttsx3
import speech_recognition as sr

from dotenv import load_dotenv
import os

# Load environment variables from .env if present
load_dotenv()

# Blynk configuration
BLYNK_TOKEN = os.getenv('BLYNK_TOKEN', "Zaq0dkSF5TSxdJTFoizjkllaDV3Z3S5V")
BLYNK_API_URL = os.getenv('BLYNK_API_URL', "http://blynk.cloud/external/api")

# Email (SMTP) configuration
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS', 'onlystudyaadi987@gmail.com')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', 'eeyyndmexryincyy')
OWNER_EMAIL = os.getenv('OWNER_EMAIL', 'aadityasinghal77@gmail.com')

# Serial / ESP configuration
SERIAL_PORT = os.getenv('SERIAL_PORT', 'COM4')
SERIAL_BAUD = int(os.getenv('SERIAL_BAUD', 9600))

try:
    esp = serial.Serial(SERIAL_PORT, SERIAL_BAUD, timeout=2)
except Exception as e:
    print(f"Warning: could not open serial port {SERIAL_PORT} at {SERIAL_BAUD} baud: {e}")
    esp = None

net = cv2.dnn.readNet("yolov3.weights", "yolov3.cfg")
classes = []
with open("coco.names", "r") as f:
    classes = [line.strip() for line in f.readlines()]
layer_names = net.getLayerNames()
output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]
colors = np.random.uniform(0, 255, size=(len(classes), 3))

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Camera not found.")
    exit()

start_time = None
last_elapsed_time = 0
detection_active = True

def send_to_esp(data):
    if esp is None:
        # Serial not available; skip
        return
    try:
        esp.write((data + "\n").encode())
    except Exception as e:
        print(f"Error writing to serial port: {e}")

def send_data_to_blynk(status, timestamp, log_entry):
    try:
        requests.get(f"{BLYNK_API_URL}/update?token={BLYNK_TOKEN}&V1={status}")
        requests.get(f"{BLYNK_API_URL}/update?token={BLYNK_TOKEN}&V2={timestamp}")
        requests.get(f"{BLYNK_API_URL}/update?token={BLYNK_TOKEN}&V0={log_entry}")
        send_to_esp(f"STATUS:{status}")
        send_to_esp(f"TIME:{timestamp}")
        send_to_esp(f"LOG:{log_entry}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending data to Blynk: {e}")

def send_email_with_attachment(subject, message, attachment_path):
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)

        msg = MIMEMultipart()
        msg["Subject"] = subject
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = OWNER_EMAIL

        msg.attach(MIMEText(message, "plain"))

        with open(attachment_path, "rb") as attachment_file:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment_file.read())
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename={attachment_path.split('/')[-1]}"
        )
        msg.attach(part)

        server.sendmail(EMAIL_ADDRESS, OWNER_EMAIL, msg.as_string())
        print("Email with attachment sent successfully!")
        server.quit()
    except Exception as e:
        print(f"Failed to send email: {e}")

def generate_heatmap(frame):
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    heatmap = cv2.applyColorMap(gray_frame, cv2.COLORMAP_JET)
    heatmap_path = "heatmap.png"
    cv2.imwrite(heatmap_path, heatmap)
    return heatmap_path

def process_frame(frame):
    global start_time, last_elapsed_time, detection_active

    if not detection_active:
        return frame

    height, width, channels = frame.shape

    blob = cv2.dnn.blobFromImage(frame, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
    net.setInput(blob)
    outs = net.forward(output_layers)

    class_ids = []
    confidences = []
    boxes = []
    person_detected = False

    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > 0.3:
                center_x = int(detection[0] * width)
                center_y = int(detection[1] * height)
                w = int(detection[2] * width)
                h = int(detection[3] * height)

                x = int(center_x - w / 2)
                y = int(center_y - h / 2)

                boxes.append([x, y, w, h])
                confidences.append(float(confidence))
                class_ids.append(class_id)

    indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)

    font = cv2.FONT_HERSHEY_PLAIN
    for i in range(len(boxes)):
        if i in indexes:
            x, y, w, h = boxes[i]
            label = str(classes[class_ids[i]])
            color = colors[class_ids[i]]
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            cv2.putText(frame, label, (x, y + 30), font, 2, color, 2)

            if label == "person":
                person_detected = True

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if person_detected:
        if start_time is None:
            start_time = time.time()
            status = "Person Detected!"
            last_elapsed_time = 0
            log_entry = f"{current_time}: {status}"
            send_data_to_blynk(status, current_time, log_entry)

            image_path = "person_detected.jpg"
            cv2.imwrite(image_path, frame)

            send_email_with_attachment(
                "Person Detected Alert",
                f"A person was detected at {current_time}.",
                image_path
            )

            heatmap_path = generate_heatmap(frame)
            send_email_with_attachment(
                "Heatmap Alert",
                f"Here is the heatmap generated from the frame where a person was detected at {current_time}.",
                heatmap_path
            )

            print(f"Person Detected! Timer Started", flush=True)
        else:
            elapsed_time = time.time() - start_time
            status = "Person Detected!"
            log_entry = f"{current_time}: {status} - {elapsed_time:.2f}s"
            send_data_to_blynk(status, current_time, log_entry)
            print(f"Person Detected! Elapsed Time: {elapsed_time:.2f}s", flush=True)

    else:
        if start_time is not None:
            elapsed_time = time.time() - start_time
            status = "No Person Detected"
            log_entry = f"{current_time}: {status} - Timer stopped at {elapsed_time:.2f}s"
            send_data_to_blynk(status, current_time, log_entry)
            print(f"No Person Detected. Timer Stopped at {elapsed_time:.2f}s", flush=True)
            last_elapsed_time = elapsed_time
            start_time = None

    return frame

# def listen_for_commands():
#     global detection_active
#     recognizer = sr.Recognizer()
#
#     while True:
#         with sr.Microphone() as source:
#             print("Listening for commands...")
#             recognizer.adjust_for_ambient_noise(source)
#             audio = recognizer.listen(source)
#
#         try:
#             command = recognizer.recognize_google(audio).lower()
#             print(f"Command received: {command}")
#
#             if "start detection" in command:
#                 detection_active = True
#                 print("Detection started.")
#                 pyttsx3.speak("Detection started.")
#
#             elif "stop detection" in command:
#                 detection_active = False
#                 print("Detection stopped.")
#                 pyttsx3.speak("Detection stopped.")
#
#             elif "turn on led" in command or "turn on buzzer" in command:
#                 send_to_esp("LED BUZZER ON")
#                 print("LED and Buzzer turned on.")
#                 pyttsx3.speak("LED and Buzzer turned on.")
#
#             elif "turn off led" in command or "turn off buzzer" in command:
#                 send_to_esp("LED BUZZER OFF")
#                 print("LED and Buzzer turned off.")
#                 pyttsx3.speak("LED and Buzzer turned off.")
#
#         except sr.UnknownValueError:
#             print("Sorry, I did not understand the command.")
#         except sr.RequestError as e:
#             print(f"Error with the speech recognition service: {e}")
#
# voice_thread = threading.Thread(target=listen_for_commands, daemon=True)
# voice_thread.start()

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to capture image.")
        break

    processed_frame = process_frame(frame)
    cv2.imshow("Object Detection - Camera", processed_frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()

