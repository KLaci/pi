#!/usr/bin/python3

import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import time
import signal

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Card read timed out!")

def main():
    # Create an object of the class MFRC522
    reader = SimpleMFRC522()
    
    # Set up the timeout signal
    signal.signal(signal.SIGALRM, timeout_handler)

    try:
        print("RFID Reader is ready!")
        print("Please place your card near the reader...")
        
        while True:
            try:
                print("\nWaiting for card...")
                # Set 5 second timeout for read operation
                signal.alarm(5)
                
                # Reading the card
                id, text = reader.read()
                
                # Disable the alarm after successful read
                signal.alarm(0)
                
                # Print the card ID
                print(f"Success! Card ID: {id}")
                
                # Wait a bit before the next read
                time.sleep(2)
                
            except TimeoutError:
                print("No card detected. Please try again.")
                continue
            except Exception as e:
                print(f"Error reading card: {str(e)}")
                continue
            
    except KeyboardInterrupt:
        print("\nProgram terminated by user")
        
    finally:
        # Clean up GPIO on program exit
        GPIO.cleanup()

if __name__ == "__main__":
    main()
