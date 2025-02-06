from machine import UART, Pin
import time

# Initialize UART for EC200U module
gsm_uart = UART(0, baudrate=115200, tx=Pin(0), rx=Pin(1))

PHONE_NUMBER = "+919791974658"  # Replace with actual recipient number
MESSAGE = "ALERT: Emergency situation detected!"

def send_at_command(command, delay=1):
    """Send an AT command and return the response."""
    gsm_uart.write(command.encode() + b'\r\n')
    time.sleep(delay)
    response = gsm_uart.read()
    return response if response else b""

def send_sms():
    """Manually send an SMS using AT commands."""
    print("Setting SMS to text mode...")
    response = send_at_command("AT+CMGF=1")
    print(f"Response: {response}")

    print(f"Setting recipient number: {PHONE_NUMBER}")
    response = send_at_command(f'AT+CMGS="{PHONE_NUMBER}"', 2)
    print(f"Response: {response}")

    if b'>' not in response:
        print("Error: No '>' prompt received. SMS not sent.")
        return False

    print("Sending message...")
    gsm_uart.write(MESSAGE.encode() + b"\x1A")  # CTRL+Z to send
    time.sleep(5)  # Wait for SMS to send

    response = gsm_uart.read()
    print(f"Final response: {response}")

    if b"+CMGS:" in response:
        print("SMS sent successfully!")
        return True
    else:
        print("Failed to send SMS.")
        return False

# Run the function to send SMS
send_sms()
