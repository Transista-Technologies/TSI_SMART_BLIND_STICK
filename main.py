# main.py
from machine import I2C, Pin, UART, SPI
from time import sleep
from PiicoDev_VL53L1X import PiicoDev_VL53L1X  # Ensure this library is installed
from nrfmaster import radio_setup, transmit
import struct
import time

# ---------------------------------------------------------
# Setup I2C buses for the two ToF sensors (adjust pins as needed)
# ---------------------------------------------------------
# Left sensor: SDA on Pin(3), SCL on Pin(4)
left_i2c = I2C(0, sda=Pin(3), scl=Pin(4), freq=400000)
# Right sensor: SDA on Pin(7), SCL on Pin(8)
right_i2c = I2C(1, sda=Pin(7), scl=Pin(8), freq=400000)

try:
    left_sensor = PiicoDev_VL53L1X(bus=left_i2c)
    right_sensor = PiicoDev_VL53L1X(bus=right_i2c)
    sensors_available = True
except Exception as e:
    print("Error initializing ToF sensors:", e)
    sensors_available = False


# ---------------------------------------------------------
# Setup the NRF module (for sending alerts)
# ---------------------------------------------------------
nrf = radio_setup()

# ==================================================
# GSM Module Setup
# ==================================================
# Initialize UART for the EC200U GSM module (adjust TX/RX pins as needed)
gsm_uart = UART(0, baudrate=115200, tx=Pin(0), rx=Pin(1))
PHONE_NUMBER = "+919367952877"  # Replace with your recipient number
MESSAGE = "ALERT: Emergency situation detected!"

def send_at_command(command, delay=1):
    """Send an AT command to the GSM module and return its response."""
    gsm_uart.write(command.encode() + b'\r\n')
    time.sleep(delay)
    response = gsm_uart.read()
    return response if response else b""

def send_sms():
    """Send an SOS SMS using AT commands."""
    print("Setting SMS to text mode...")
    response = send_at_command("AT+CMGF=1")
    print("Response:", response)

    print("Setting recipient number:", PHONE_NUMBER)
    response = send_at_command(f'AT+CMGS="{PHONE_NUMBER}"', 2)
    print("Response:", response)

    if b'>' not in response:
        print("Error: No '>' prompt received. SMS not sent.")
        return False

    print("Sending message...")
    gsm_uart.write(MESSAGE.encode() + b"\x1A")  # CTRL+Z to send
    time.sleep(5)
    response = gsm_uart.read()
    print("Final response:", response)
    if response and b"+CMGS:" in response:
        print("SMS sent successfully!")
        return True
    else:
        print("Failed to send SMS.")
        return False
    
# ==================================================
# Button Setup
# ==================================================
# Assumption: Buttons are active low with internal pull-ups.
# Adjust these pin numbers as needed, ensuring they don’t conflict with other peripherals.
sos_button   = Pin(9,  Pin.IN, Pin.PULL_UP)  # SOS button
power_button = Pin(22,  Pin.IN, Pin.PULL_UP)  # Power button
mode_button  = Pin(13,  Pin.IN, Pin.PULL_UP)  # Mode button

# Global variables for button handling
sos_press_count = 0
sos_last_press_time = 0  # in milliseconds

# Mode settings:
#   Mode 0: Normal (ToF threshold = 2000 mm)
#   Mode 1: Crowd  (ToF threshold = 2500 mm)
#   Mode 2: Train  (Alerts disabled; threshold set extremely high)
mode = 0
tof_threshold = 2000  # Default threshold (in mm)

def update_mode():
    """Cycle through modes and update the ToF detection threshold accordingly."""
    global mode, tof_threshold
    mode = (mode + 1) % 2  # Cycle through 0, 1
    if mode == 0:
        tof_threshold = 2000
        print("Mode: NORMAL. ToF threshold =", tof_threshold, "mm")
    elif mode == 1:
        tof_threshold = 800
        print("Mode: CROWD. ToF threshold =", tof_threshold, "mm")

def check_buttons():
    """
    Check the states of the SOS, Power, and Mode buttons.
    - SOS: Count presses; if 3 valid presses are detected, trigger an SMS.
    - Power: If held for 3 seconds, signal a shutdown.
    - Mode: On each press, cycle the detection mode.
    Returns "shutdown" if the power button is held long enough.
    """
    global sos_press_count, sos_last_press_time
    current_time = time.ticks_ms()

    # --- SOS Button ---
    if sos_button.value() == 0:  # Button pressed (active low)
        time.sleep_ms(50)  # Simple debounce
        if sos_button.value() == 0:
            # Only count if sufficient time has passed since the last press
            if time.ticks_diff(current_time, sos_last_press_time) > 500:
                sos_press_count += 1
                sos_last_press_time = current_time
                print("SOS button pressed. Count =", sos_press_count)
            # Wait until the button is released to avoid multiple counts
            while sos_button.value() == 0:
                time.sleep_ms(10)
    if sos_press_count >= 3:
        print("SOS triggered! Sending SMS...")
        send_sms()
        sos_press_count = 0  # Reset the counter after triggering

    # --- Power Button ---
    if power_button.value() == 0:
        press_start = time.ticks_ms()
        while power_button.value() == 0:
            time.sleep_ms(10)
            if time.ticks_diff(time.ticks_ms(), press_start) > 3000:
                print("Power button held for 3 seconds. Shutting down...")
                return "shutdown"
            sleep(0.1) #Reduce CPU usage while checking

    # --- Mode Button ---
    if mode_button.value() == 0:
        time.sleep_ms(50)  # Debounce
        if mode_button.value() == 0:
            update_mode()
            while mode_button.value() == 0:
                time.sleep_ms(10)
    return None

def main():
    print("System started.")
    print("Press the SOS button 3 times to send an emergency SMS.")
    print("Hold the POWER button for 3 seconds to shut down the system.")
    print("Press the MODE button to cycle through detection modes.")
    

    while True:
        # Read distances (in mm) from both ToF sensors
        left_distance = left_sensor.read()
        right_distance = right_sensor.read()
        print("Left sensor: {} mm, Right sensor: {} mm".format(left_distance, right_distance))
        
        # If an obstacle is detected on the left side, send an alert to left slave
        if left_distance <= tof_threshold:
            print("Obstacle detected on LEFT side!")
            transmit(nrf, "left")
        
        # If an obstacle is detected on the right side, send an alert to right slave
        if right_distance <= tof_threshold:
            print("Obstacle detected on RIGHT side!")
            transmit(nrf, "right")
        
        sleep(0.1)  # Short delay before the next sensor reading

if __name__ == "__main__":
    main()
