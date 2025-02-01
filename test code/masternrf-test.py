from machine import Pin
from nrf24l01 import NRF24L01
import time

# NRF24L01 Pins
CE = Pin(26, Pin.OUT)
CSN = Pin(27, Pin.OUT)
SCK = Pin(10, Pin.OUT)
MOSI = Pin(11, Pin.OUT)
MISO = Pin(12, Pin.IN)

# Test addresses
LEFT_ADDR = b'\x00\xf0\xf0\xf0\xf0'   # Address for left slave
RIGHT_ADDR = b'\x00\xf1\xf1\xf1\xf1'  # Address for right slave

def test_nrf():
    # Initialize NRF24L01
    nrf = NRF24L01(spi_id=0, csn_pin=CSN, ce_pin=CE)
    
    # Configure radio
    nrf.config()
    nrf.set_channel(108)
    nrf.set_power_level('LOW')
    nrf.set_data_rate('250KBPS')
    
    print("Starting alternating signal test...")
    
    while True:
        try:
            # Send to left slave
            print("Sending to LEFT...")
            nrf.send(b'L', LEFT_ADDR)
            time.sleep(2)  # Wait 2 seconds
            
            # Send to right slave
            print("Sending to RIGHT...")
            nrf.send(b'R', RIGHT_ADDR)
            time.sleep(2)  # Wait 2 seconds
            
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    test_nrf()