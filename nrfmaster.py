from machine import Pin, SPI
import struct
from nrf24l01 import NRF24L01
import time

# Initialize onboard LED for transmission indication
led = Pin(2, Pin.OUT)

# Configure SPI and CE/CSN pins for NRF24L01
csn = Pin(27, mode=Pin.OUT, value=1)
ce = Pin(26, mode=Pin.OUT, value=0)
spi = SPI(1, polarity=0, phase=0, sck=Pin(10), mosi=Pin(11), miso=Pin(12), baudrate=115200)

# Define communication pipes (TX address, RX address)
LEFT_PIPE  = b"\xe1\xf0\xf0\xf0\x01"  # Left slave address
RIGHT_PIPE = b"\xe1\xf0\xf0\xf0\x02"  # Right slave address

def radio_setup():
    nrf = NRF24L01(spi, csn, ce, payload_size=4)
    nrf.open_tx_pipe(LEFT_PIPE)
    
    # Set channel to 76
    nrf.reg_write(0x05, 108)
    
    # Set power level to 0 dBm and data rate to 1 Mbps
    nrf.reg_write(0x06, 0x06)
    
    # Power up the device
    config = nrf.reg_read(0x00)
    config |= 0x02  # Set PWR_UP bit (bit 1)
    nrf.reg_write(0x00, config)
    
    # Debug registers
    print("CONFIG:", bin(nrf.reg_read(0x00)))  # Should be 0b1110 (0x0E)
    print("RF_SETUP:", bin(nrf.reg_read(0x06)))  # Should be 0b110 (0x06)
    print("Channel:", nrf.reg_read(0x05))  # Should be 76
    return nrf

def transmit(nrf, target):
    if target == 'left':
        pipe = LEFT_PIPE
        trigger = 1  # For example, trigger value for left
    elif target == 'right':
        pipe = RIGHT_PIPE
        trigger = 2  # For example, trigger value for right
    else:
        print("Invalid target specified. Use 'left' or 'right'.")
        return
    nrf.open_tx_pipe(pipe)
    
    try:
        led.value(1)  # Indicate transmission start
        # Pack the trigger value into 4-byte format and send it
        nrf.send(struct.pack("i", trigger))
        print("Sent trigger {} to {} slave".format(trigger, target))
    except OSError:
        print("Transmission failed for {} slave".format(target))
    finally:
        led.value(0)  # Turn off LED after transmission
        time.sleep(0.5)  # A short delay before the next transmission

def main():
    nrf = radio_setup()
    while True:
        # For demonstration, send a trigger to left and then to right.
        transmit(nrf, "left")
        time.sleep(1)
        transmit(nrf, "right")
        time.sleep(1)

# Main execution flow
if __name__ == "__main__":
        main()
