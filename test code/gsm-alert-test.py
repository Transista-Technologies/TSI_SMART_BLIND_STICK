from machine import UART, Pin
import time

# Initialize UART for GSM module
gsm_uart = UART(0, baudrate=115200, tx=Pin(0), rx=Pin(1))

# GSM power key pin
PWRKEY = Pin(28, Pin.OUT)

# Phone number to send SMS to (replace with actual number)
PHONE_NUMBER = "+1234567890"  # Replace with your number
MESSAGE = "ALERT: Emergency situation detected!"

def initialize_gsm():
    """Power cycle and initialize the GSM module"""
    # Power cycle the GSM module
    PWRKEY.value(1)
    time.sleep(0.5)
    PWRKEY.value(0)
    time.sleep(2)
    
    # Wait for module to stabilize
    time.sleep(5)
    
    # Send AT commands to configure text mode
    commands = [
        'AT\r\n',                    # Test AT command
        'AT+CMGF=1\r\n',            # Set SMS text mode
        'AT+CNMI=2,1,0,0,0\r\n'     # Configure new message indications
    ]
    
    for cmd in commands:
        gsm_uart.write(cmd)
        time.sleep(1)
        while gsm_uart.any():
            response = gsm_uart.read()
            print(response)

def send_sms(number, message):
    """Send SMS to specified number"""
    # Set message destination
    gsm_uart.write(f'AT+CMGS="{number}"\r\n')
    time.sleep(1)
    
    # Send message content
    gsm_uart.write(message + chr(26))  # chr(26) is Ctrl+Z
    time.sleep(2)
    
    # Print response
    while gsm_uart.any():
        response = gsm_uart.read()
        print(response)

def main():
    print("Initializing GSM module...")
    initialize_gsm()
    print("GSM module initialized")
    
    print(f"Will send SMS to {PHONE_NUMBER} every 3 seconds")
    
    while True:
        try:
            print("Sending SMS...")
            send_sms(PHONE_NUMBER, MESSAGE)
            print("SMS sent")
            time.sleep(3)  # Wait 3 seconds before next message
            
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()