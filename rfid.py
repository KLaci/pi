#!/usr/bin/python3

import RPi.GPIO as GPIO
import spidev
import time

def test_spi():
    try:
        # Initialize SPI
        spi = spidev.SpiDev()
        spi.open(0, 0)  # Bus 0, Device 0
        spi.max_speed_hz = 1000000  # 1MHz
        print("SPI initialized successfully!")
        return True
    except Exception as e:
        print(f"SPI Error: {str(e)}")
        return False

def test_gpio():
    try:
        # Test RST pin (GPIO25)
        RST_PIN = 25
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(RST_PIN, GPIO.OUT)
        
        # Toggle RST pin
        print("Testing RST pin...")
        GPIO.output(RST_PIN, GPIO.HIGH)
        time.sleep(0.1)
        GPIO.output(RST_PIN, GPIO.LOW)
        time.sleep(0.1)
        GPIO.output(RST_PIN, GPIO.HIGH)
        print("RST pin test completed!")
        return True
    except Exception as e:
        print(f"GPIO Error: {str(e)}")
        return False

def main():
    print("Starting RC522 connection test...")
    print("\nChecking connections...")
    print("------------------------")
    
    # Test SPI
    print("\n1. Testing SPI connection:")
    spi_ok = test_spi()
    
    # Test GPIO
    print("\n2. Testing GPIO connection:")
    gpio_ok = test_gpio()
    
    print("\nTest Results:")
    print("------------------------")
    print(f"SPI Connection: {'✓ OK' if spi_ok else '✗ FAILED'}")
    print(f"GPIO Connection: {'✓ OK' if gpio_ok else '✗ FAILED'}")
    
    if spi_ok and gpio_ok:
        print("\nAll connections appear to be working!")
        print("\nWiring Reference:")
        print("------------------------")
        print("RC522 Pin  ->  Raspberry Pi Pin")
        print("SDA        ->  Pin 24 (GPIO8)")
        print("SCK        ->  Pin 23 (GPIO11)")
        print("MOSI       ->  Pin 19 (GPIO10)")
        print("MISO       ->  Pin 21 (GPIO9)")
        print("GND        ->  Any GND pin")
        print("RST        ->  Pin 22 (GPIO25)")
        print("3.3V       ->  3.3V")
    else:
        print("\nSome connections failed! Please check your wiring.")

    GPIO.cleanup()

if __name__ == "__main__":
    main()
