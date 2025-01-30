from mfrc522 import SimpleMFRC522
import RPi.GPIO as GPIO

try:
    reader = SimpleMFRC522()
    print("RC522 initialized successfully")
    print("Please place a tag on the reader")
    id, text = reader.read()
    print(f"ID: {id}")
    print(f"Text: {text}")
finally:
    GPIO.cleanup()
