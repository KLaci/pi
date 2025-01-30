from mfrc522 import SimpleMFRC522
import RPi.GPIO as GPIO
import spidev
import time

def reset_reader():
    """Reset the RFID reader"""
    GPIO.setmode(GPIO.BOARD)
    reset_pin = 22  # GPIO25, Pin 22
    GPIO.setup(reset_pin, GPIO.OUT)
    GPIO.output(reset_pin, GPIO.LOW)
    time.sleep(0.1)
    GPIO.output(reset_pin, GPIO.HIGH)
    time.sleep(0.1)

def check_reader_connection():
    try:
        spi = spidev.SpiDev()
        spi.open(0, 0)  # Open SPI port 0, device 0
        spi.max_speed_hz = 1000000  # 1MHz
        spi.mode = 0
        
        # Try to read the version register of MFRC522
        response = spi.xfer2([0x37 << 1 | 0x80, 0x00])[1]
        spi.close()
        
        print(f"Version register response: 0x{response:02x}")
        
        if response == 0x91 or response == 0x92:  # Known version numbers of MFRC522
            return True
        else:
            print(f"Unknown version: 0x{response:02x}")
            return False
            
    except Exception as e:
        print(f"Error checking RFID reader: {str(e)}")
        return False

try:
    # Clean up any existing GPIO settings
    GPIO.cleanup()
    
    # Reset the reader first
    reset_reader()
    
    # Initialize the reader
    reader = SimpleMFRC522()
    
    if check_reader_connection():
        print("RC522 initialized successfully and connection verified")
        print("Please place a tag on the reader")
        while True:
            try:
                id, text = reader.read()
                print(f"ID: {id}")
                print(f"Text: {text}")
                time.sleep(1)  # Add delay between reads
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Read error: {str(e)}")
                time.sleep(1)
    else:
        print("\nTroubleshooting steps:")
        print("1. Check your wiring connections:")
        print("   - SDA  -> GPIO8  (Pin 24)")
        print("   - SCK  -> GPIO11 (Pin 23)")
        print("   - MOSI -> GPIO10 (Pin 19)")
        print("   - MISO -> GPIO9  (Pin 21)")
        print("   - RST  -> GPIO25 (Pin 22)")
        print("   - 3.3V -> 3.3V")
        print("   - GND  -> GND")
        print("2. Make sure SPI is enabled: 'sudo raspi-config'")
        print("3. Check if SPI module is loaded: 'lsmod | grep spi'")
        print("4. Verify permissions: 'ls -l /dev/spidev0.*'")
except Exception as e:
    print(f"Error: {str(e)}")
finally:
    GPIO.cleanup()
