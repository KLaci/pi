#!/usr/bin/python3

import RPi.GPIO as GPIO
from pirc522 import RFID
import time

def main():
    try:
        # Clean up any previous GPIO settings
        GPIO.cleanup()
        
        # Disable GPIO warnings
        GPIO.setwarnings(False)
        
        # Create an object of the class RFID
        rdr = RFID()
        
        # Test if RFID reader is connected properly
        try:
            rdr.dev_write(0x2A, 0x8D) # Try writing to a register
            connection_status = rdr.dev_read(0x2A) # Read it back
            print(f"Connection status: {connection_status}")
            if connection_status == 0x8D:
                print("RFID Reader is connected and working properly!")
            else:
                print("Error: RFID Reader not responding correctly")
                return
        except Exception as e:
            print(f"Error connecting to RFID Reader: {str(e)}")
            print("Please check your wiring connections")
            return
            
        print("Please place your card near the reader...")
        
        while True:
            print("\nWaiting for card...")
            
            # Wait for tag
            rdr.wait_for_tag()
            
            # Request tag
            (error, data) = rdr.request()
            if error:
                print(f"Error during request: {error}")
            if not error:
                print("\nTag detected!")
                
                # Get anti-collision
                (error, uid) = rdr.anticoll()
                if error:
                    print(f"Error during anticoll: {error}")
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
        if 'rdr' in locals():
            rdr.cleanup()

if __name__ == "__main__":
    main()
