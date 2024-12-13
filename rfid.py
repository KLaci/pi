#!/usr/bin/python3

import RPi.GPIO as GPIO
from pirc522 import RFID
import time

def main():
    # Create an object of the class RFID
    rdr = RFID()
    
    try:
        print("RFID Reader is ready!")
        print("Please place your card near the reader...")
        
        while True:
            print("\nWaiting for card...")
            
            # Wait for tag
            rdr.wait_for_tag()
            
            # Request tag
            (error, data) = rdr.request()
            if not error:
                print("\nTag detected!")
                
                # Get anti-collision
                (error, uid) = rdr.anticoll()
                if not error:
                    # Convert UID to string
                    card_id = ''.join(str(x) for x in uid)
                    print(f"Card ID: {card_id}")
                    
                    time.sleep(1)
            
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\nProgram terminated by user")
        
    finally:
        # Clean up
        GPIO.cleanup()
        rdr.cleanup()

if __name__ == "__main__":
    main()
