from mfrc522 import SimpleMFRC522
import RPi.GPIO as GPIO
import spidev

def check_reader_connection():
    try:
        spi = spidev.SpiDev()
        spi.open(0, 0)  # Open SPI port 0, device 0
        spi.max_speed_hz = 1000000  # 1MHz
        
        # Try to read the version register of MFRC522
        # Write command: [address, value]
        # 0x37 is the version register address
        response = spi.xfer2([0x37, 0x00])[1]
        spi.close()
        
        if response == 0x91 or response == 0x92:  # Known version numbers of MFRC522
            return True
        else:
            print(f"Unknown version: 0x{response:02x}")
            return False
            
    except Exception as e:
        print(f"Error checking RFID reader: {str(e)}")
        return False

try:
    reader = SimpleMFRC522()
    
    if check_reader_connection():
        print("RC522 initialized successfully and connection verified")
        print("Please place a tag on the reader")
        id, text = reader.read()
        print(f"ID: {id}")
        print(f"Text: {text}")
    else:
        print("Failed to verify RC522 connection. Please check your wiring:")
        print("- Make sure SPI is enabled in raspi-config")
        print("- Check that the RC522 is properly connected to the correct GPIO pins")
        print("- Verify power connections (3.3V and GND)")
except Exception as e:
    print(f"Error: {str(e)}")
finally:
    GPIO.cleanup()
