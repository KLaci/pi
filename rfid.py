#!/usr/bin/python3

import RPi.GPIO as GPIO
from pirc522 import RFID
import time

def main():
    # Disable GPIO warnings
    GPIO.setwarnings(False)
    # Switch from BOARD to BCM numbering
    GPIO.setmode(GPIO.BCM)
    
    # Create an RFID reader object with pins using BCM numbering
    rdr = RFID(pin_rst=22, pin_ce=24, pin_irq=None)
    
    # Quickly check if RFID reader is responsive by writing and reading a known register
    try:
        test_register = 0x2A
        test_value = 0x8D
        rdr.dev_write(test_register, test_value)
        connection_status = rdr.dev_read(test_register)
        if connection_status != test_value:
            print("Error: RFID Reader not responding correctly")
            return
        print("RFID Reader is connected and working properly!")
    except Exception as e:
        print(f"Error connecting to RFID Reader: {e}")
        print("Please check your wiring connections")
        return
    
    print("Place your card near the reader... (Ctrl+C to exit)")
    
    try:
        while True:
            # Wait for a card to appear
            rdr.wait_for_tag()
            (error, data) = rdr.request()
            if not error:
                (error, uid) = rdr.anticoll()
                if not error:
                    # Convert UID to a readable string
                    card_id = ''.join(str(x) for x in uid)
                    print(f"Card detected! Card ID: {card_id}")
                    time.sleep(1)  # Give some delay before the next loop
            time.sleep(0.1)  # Slight pause to avoid excessive polling
    except KeyboardInterrupt:
        print("\nProgram terminated by user")
    finally:
        # Clean up after the loop
        GPIO.cleanup()
        rdr.cleanup()

if __name__ == "__main__":
    main()
