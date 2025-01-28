from machine import Pin, I2C, UART, Timer, deepsleep
import time
from vl53l5cx import VL53L5CX
from nrf24l01 import NRF24L01

# Pin Definitions
class Pins:
    # NRF24L01 Pins
    CE = Pin(26, Pin.OUT)
    CSN = Pin(27, Pin.OUT)
    SCK = Pin(10, Pin.OUT)
    MOSI = Pin(11, Pin.OUT)
    MISO = Pin(12, Pin.IN)
    
    # TOF Sensor 1
    SDA_0 = Pin(4)
    SCL_0 = Pin(5)
    LPN_0 = Pin(8, Pin.OUT)
    RST_0 = Pin(7, Pin.OUT)
    INT_0 = Pin(6, Pin.IN)
    
    # TOF Sensor 2
    SDA_1 = Pin(14)
    SCL_1 = Pin(15)
    LPN_1 = Pin(18, Pin.OUT)
    RST_1 = Pin(17, Pin.OUT)
    INT_1 = Pin(16, Pin.IN)
    
    # Buttons
    SOS_BUTTON = Pin(9, Pin.IN, Pin.PULL_UP)
    MODE_BUTTON = Pin(13, Pin.IN, Pin.PULL_UP)
    SLEEP_BUTTON = Pin(22, Pin.IN, Pin.PULL_UP)
    
    # Indicators
    LED = Pin(2, Pin.OUT)
    BUZZER = Pin(3, Pin.OUT)
    VIBRATION = Pin(19, Pin.OUT)
    
    # GSM Module
    PWRKEY = Pin(28, Pin.OUT)
    RI = Pin(21, Pin.IN)
    DTR = Pin(20, Pin.OUT)

# Constants
DETECTION_THRESHOLD = 2
DISTANCE_THRESHOLD = 800  # mm
SOS_PRESS_DURATION = 3000  # 3 seconds in ms
SLEEP_PRESS_DURATION = 6000  # 6 seconds in ms
INACTIVITY_TIMEOUT = 600000  # 10 minutes in ms

# Slave Addresses (to be added)
SLAVE1_ADDR = None
SLAVE2_ADDR = None

# Mode definitions
class Modes:
    NORMAL = 0
    SILENT = 1
    EXTRA_SENSITIVE = 2

class BlindStick:
    def __init__(self):
        self.current_mode = Modes.NORMAL
        self.sos_press_start = 0
        self.sleep_press_start = 0
        self.last_activity_time = time.ticks_ms()
        self.gsm_uart = UART(0, baudrate=115200, tx=Pin(0), rx=Pin(1))
        
        # Initialize I2C for TOF sensors
        self.i2c0 = I2C(0, sda=Pins.SDA_0, scl=Pins.SCL_0)
        self.i2c1 = I2C(1, sda=Pins.SDA_1, scl=Pins.SCL_1)
        
        # Initialize TOF sensors
        self.tof1 = VL53L5CX(self.i2c0, Pins.LPN_0, Pins.RST_0)
        self.tof2 = VL53L5CX(self.i2c1, Pins.LPN_1, Pins.RST_1)
        
        # Initialize NRF24L01
        self.nrf = NRF24L01(spi_id=0, csn_pin=Pins.CSN, ce_pin=Pins.CE)
        self.setup_nrf()
        self.setup_interrupts()
        
    def setup_nrf(self):
        """Initialize NRF24L01 radio module"""
        try:
            self.nrf.config()
            self.nrf.set_channel(108)  # Match with slave device
            self.nrf.set_power_level('LOW')
            self.nrf.set_data_rate('250KBPS')
        except Exception as e:
            print(f"NRF Setup Error: {e}")
            Pins.LED.value(1)  # Error indication
    
    def setup_interrupts(self):
        """Set up button interrupts"""
        Pins.SOS_BUTTON.irq(trigger=Pin.IRQ_FALLING, handler=self.sos_button_handler)
        Pins.MODE_BUTTON.irq(trigger=Pin.IRQ_FALLING, handler=self.mode_button_handler)
        Pins.SLEEP_BUTTON.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, 
                               handler=self.sleep_button_handler)
    
    def sos_button_handler(self, pin):
        """Handle SOS button press"""
        current_time = time.ticks_ms()
        duration = time.ticks_diff(current_time, self.sos_press_start)
        
        if duration >= SOS_PRESS_DURATION:
            # Activate SOS functionality (e.g., send SMS, trigger alarm)
            self.send_sos_alert()
    
    def send_sos_alert(self):
        """Send SOS alert via GSM or radio"""
        try:
            # Send SOS message via GSM
            self.gsm_uart.write("SOS ALERT")
            
            # Activate visual and audio indicators
            Pins.LED.value(1)
            Pins.BUZZER.value(1)
            Pins.VIBRATION.value(1)
            time.sleep(1)
            Pins.LED.value(0)
            Pins.BUZZER.value(0)
            Pins.VIBRATION.value(0)
        except Exception as e:
            print(f"SOS Alert Error: {e}")
    
    def sleep_button_handler(self, pin):
        """Handle sleep button press for deep sleep"""
        if pin.value() == 0:  # Button pressed
            self.sleep_press_start = time.ticks_ms()
        else:  # Button released
            duration = time.ticks_diff(time.ticks_ms(), self.sleep_press_start)
            if duration >= SLEEP_PRESS_DURATION:
                self.enter_deep_sleep()

    def enter_deep_sleep(self):
        """Enter deep sleep mode"""
        # Short beep to indicate entering sleep
        Pins.BUZZER.value(1)
        time.sleep(0.2)
        Pins.BUZZER.value(0)
        
        # Configure wake-up pin
        Pins.SLEEP_BUTTON.init(Pin.IN, Pin.PULL_UP)
        # Enter deep sleep mode
        deepsleep()

    def check_inactivity(self):
        """Check and handle device inactivity"""
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, self.last_activity_time) >= INACTIVITY_TIMEOUT:
            self.enter_deep_sleep()

    def process_tof_data(self, sensor, side):
        """Process Time of Flight sensor data"""
        detection_count = 0
        if sensor.data_ready():
            self.last_activity_time = time.ticks_ms()  # Update activity timestamp
            data = sensor.get_data()
            for zone in range(16):
                if data[zone] < DISTANCE_THRESHOLD:
                    detection_count += 1
        
        if detection_count > DETECTION_THRESHOLD:
            self.nrf.send(b'H', SLAVE1_ADDR if side == "left" else SLAVE2_ADDR)
        else:
            self.nrf.send(b'L', SLAVE1_ADDR if side == "left" else SLAVE2_ADDR)

    def mode_button_handler(self, pin):
        """Cycle through different modes"""
        self.current_mode = (self.current_mode + 1) % 3  # Cycle through 0, 1, 2
        
        # Provide mode change feedback
        for _ in range(self.current_mode + 1):
            Pins.BUZZER.value(1)
            time.sleep(0.2)
            Pins.BUZZER.value(0)
            time.sleep(0.2)

    def main_loop(self):
        """Main operational loop of the blind stick"""
        while True:
            self.process_tof_data(self.tof1, "left")
            self.process_tof_data(self.tof2, "right")
            
            # Adjust sensitivity based on mode
            global DETECTION_THRESHOLD
            DETECTION_THRESHOLD = 1 if self.current_mode == Modes.EXTRA_SENSITIVE else 2
            
            # Check for inactivity
            self.check_inactivity()
            
            time.sleep(0.1)

# Start the blind stick
if __name__ == "__main__":
    stick = BlindStick()
    stick.main_loop()