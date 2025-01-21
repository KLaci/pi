#!/usr/bin/env python3

from pirc522 import RFID
import signal
import sys
import RPi.GPIO as GPIO

run = True

# GPIO.setwarnings(False) # optionally ignore GPIO warnings

def end_read(signal, frame):
    global run
    print("\nCtrl+C captured, ending read.")
    run = False
    rfid.cleanup()
    sys.exit()

signal.signal(signal.SIGINT, end_read)

# Initialize the RFID reader
# If you used GPIO25 for RST, configure it here
rfid = RFID(pin_rst=25, pin_ce=0, bus=0, device=0)

print("Starting MFRC522 RFID Reader")

while run:
    rfid.wait_for_tag()
    (error, tag_type) = rfid.request()
    if not error:
        print("Tag detected!")
        (error, uid) = rfid.anticoll()
        if not error:
            # Print UID
            print("Card read UID: {}".format(uid))
            # Select the scanned tag
            rfid.select_tag(uid)
            # Stop reading
            rfid.stop_crypto()
