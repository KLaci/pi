#!/usr/bin/python3

import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import time

def main():
    # Create an object of the class MFRC522
    reader = SimpleMFRC522()

    try:
        print("RFID Reader is ready!")
        print("Please place your card near the reader...")
        
        while True:
            # Reading the card
            print("Reading card...")
            id, text = reader.read()
            
            # Print the card ID
            print(f"\nCard ID: {id}")
            
            # Wait a bit before the next read
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\nProgram terminated by user")
        
    finally:
        # Clean up GPIO on program exit
        GPIO.cleanup()

if __name__ == "__main__":
    main()
