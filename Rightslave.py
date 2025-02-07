from machine import Pin, SPI
import struct
from nrf24l01 import NRF24L01
import time

# Initialize onboard LED for reception indication
led = Pin(2, Pin.OUT)

# Configure SPI and CE/CSN pins for NRF24L01
csn = Pin(1, mode=Pin.OUT, value=1)
ce = Pin(3, mode=Pin.OUT, value=0)

spi = SPI(1, polarity=0, phase=0, sck=Pin(7), mosi=Pin(9), miso=Pin(8), baudrate=115200)

# Define communication pipes (RX address must match TX pipe of sender)
pipes = b"\xe1\xf0\xf0\xf0\x02"
EXPECTED_TRIGGER = 2

def radio_setup():
    # Initialize and configure NRF24L01
    nrf = NRF24L01(spi, csn, ce, payload_size=4)
    nrf.set_channel(108)
    nrf.set_power_speed(0, 1)
    print("Status:", nrf.reg_read(0x07))
    nrf.open_rx_pipe(1, pipes)  # Listen to sender's address
    nrf.start_listening()  # Begin listening for messages
    print("RF_SETUP:", bin(nrf.reg_read(0x06)))
    print("Channel:", nrf.reg_read(0x05))
    print("CONFIG:", bin(nrf.reg_read(0x00)))
    print("FIFO_STATUS:", bin(nrf.reg_read(0x17)))
    return nrf
# ------------------------------
# Output Devices (Right Slave)
# ------------------------------
# Buzzer on GPIO5 and Vibrating Motor on GPIO6.
buzzer   = Pin(5, Pin.OUT)
vib_motor = Pin(6, Pin.OUT)

def activate_alarm(duration_ms=500):
    buzzer.value(1)
    vib_motor.value(1)
    time.sleep_ms(duration_ms)
    buzzer.value(0)
    vib_motor.value(0)

# ------------------------------
# Wake Button Setup (common)
# ------------------------------
# Wake button on GPIO4 (active low with pull-up).
wake_button = Pin(4, Pin.IN, Pin.PULL_UP)
module_on = True  # Global flag for module power state

def check_wake_button():
    global module_on
    if wake_button.value() == 0:
        press_start = time.ticks_ms()
        while wake_button.value() == 0:
            time.sleep_ms(10)
            if time.ticks_diff(time.ticks_ms(), press_start) > 3000:
                module_on = not module_on
                if module_on:
                    print("Module Woken Up.")
                else:
                    print("Module Turned Off.")
                # Wait for button release to avoid multiple toggles.
                while wake_button.value() == 0:
                    time.sleep_ms(10)
                break

def receive(nrf):
    while True:
        check_wake_button()
        if not module_on:
            print("Module is off. Waiting to be woken up...")
            time.sleep(0.5)
            continue

        if nrf.any():
            led.value(1)
            recv_buffer = nrf.recv()  # Receive 4-byte payload
            try:
                received_trigger = struct.unpack("i", recv_buffer)[0]
            except Exception as e:
                print("Error unpacking data:", e)
                received_trigger = None

            if received_trigger is not None:
                print(f"Received trigger: {received_trigger}")
                if received_trigger == EXPECTED_TRIGGER:
                    print("Valid trigger received. Activating alarm.")
                    activate_alarm()
                else:
                    print("Trigger does not match expected value.")
            led.value(0)
        time.sleep(0.1)
# Main execution flow
if __name__ == "__main__":
    radio = radio_setup()
    print("Receiver Ready!")
    receive(radio)