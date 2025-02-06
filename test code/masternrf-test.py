from machine import Pin, SPI
from nrf24l01 import NRF24L01
import time

# Initialize pins
csn = Pin(27, Pin.OUT)
ce = Pin(26, Pin.OUT)

# Make sure CSN is high initially (chip disabled)
csn.value(1)
ce.value(0)

# Initialize SPI at a lower speed for reliability
spi = SPI(1, baudrate=115200)

def test_nrf():
    print("Starting NRF24L01 test...")
    print("Initializing radio...")
    
    try:
        # Initialize NRF24L01
        nrf = NRF24L01(spi, csn, ce)
        
        # Set address (5 bytes)
        tx_address = b'\x00\xf0\xf0\xf0\xf0'
        rx_address = b'\x00\xf0\xf0\xf0\xf0'
        
        nrf.open_tx_pipe(tx_address)      # Open TX pipe
        nrf.open_rx_pipe(1, rx_address)   # Open RX pipe
        
        nrf.start_listening()             # Start listening
        nrf.stop_listening()              # Stop listening to enter TX mode
        
        print("Starting transmission test...")
        count = 0
        
        while True:
            try:
                print(f"\nTest #{count + 1}")
                print("Sending test message...")
                
                # Try to send a message
                message = b'TEST'
                nrf.stop_listening()
                result = nrf.send(message)
                
                print("Message sent!" if result else "Send failed!")
                print("Check connections if no response:")
                print("- CSN -> GP27")
                print("- CE  -> GP26")
                print("- SCK -> GP10")
                print("- MOSI -> GP11")
                print("- MISO -> GP12")
                print("- VCC -> 3.3V")
                print("- GND -> GND")
                
                count += 1
                time.sleep(2)
                
            except Exception as e:
                print(f"Error during transmission: {e}")
                time.sleep(1)
    
    except Exception as e:
        print(f"Error initializing radio: {e}")
        print("\nTroubleshooting tips:")
        print("1. Check power supply - needs stable 3.3V")
        print("2. Verify all connections")
        print("3. Try with a different NRF24L01")
        print("4. Add a 10µF capacitor between VCC and GND")

if __name__ == "__main__":
    while True:
        try:
            test_nrf()
        except KeyboardInterrupt:
            print("\nTest stopped by user")
            break
        except Exception as e:
            print(f"Critical error: {e}")
            print("Retrying in 5 seconds...")
            time.sleep(5)
