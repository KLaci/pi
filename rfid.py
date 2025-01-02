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
        
        # Set GPIO mode
        GPIO.setmode(GPIO.BCM)
        
        # Create an object of the class RFID with explicit pin configuration
        rdr = RFID(pin_rst=25,    # RST pin
                   pin_ce=8,      # SDA (CE0) pin
                   pin_irq=None)  # IRQ pin not connected
        
        # Set antenna gain to maximum
        rdr.dev_write(0x26, 0x60)  # RF Level: maximum power (7) << 4
        
        # Additional initialization
        rdr.dev_write(0x11, 0x5A)  # Define automatic reception
        rdr.dev_write(0x2D, 0x00)  # TModeReg
        rdr.dev_write(0x2C, 0x00)  # TPrescalerReg
        rdr.dev_write(0x2B, 0x4D)  # TReloadReg high
        rdr.dev_write(0x2A, 0x00)  # TReloadReg low
        
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
            else:
                print("\nTag detected!")
                print(f"Request data: {data}")
                
                # Get anti-collision
                (error, uid) = rdr.anticoll()
                if error:
                    print(f"Error during anticoll: {error}")
                else:
                    # Convert UID to string
                    card_id = ''.join(str(x) for x in uid)
                    print(f"Card ID: {card_id}")
                    print(f"Raw UID: {uid}")
                    
                    # Try to select the card
                    error = rdr.select_tag(uid)
                    if error:
                        print(f"Error selecting card: {error}")
                    else:
                        print("Card selected successfully!")
                    
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
