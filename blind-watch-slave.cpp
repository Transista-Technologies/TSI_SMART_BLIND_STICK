#include <SPI.h>
#include <RF24.h>

// Pin Definitions
#define CE_PIN 3
#define CSN_PIN 1
#define SCK_PIN 7
#define MOSI_PIN 9
#define MISO_PIN 8
#define LED_PIN 2
#define VIBRATION_PIN 6
#define BUZZER_PIN 4
#define WAKE_PIN 5

// Constants
#define VIBRATION_DURATION 200        // ms
#define LONG_VIBRATION_DURATION 1000  // ms for crowd detection
#define PAIRING_TIMEOUT 5000         // ms
#define SLEEP_TIMEOUT 600000         // 10 minutes
#define RADIO_CHANNEL 108            // 2.508 GHz
#define RADIO_PAYLOAD_SIZE 1

// Battery saving configurations
#define LED_BLINK_DURATION 100
#define ERROR_BLINK_DURATION 300
#define RADIO_RETRY_DELAY 15
#define RADIO_RETRY_COUNT 3

// Radio pipe addresses for the nodes to communicate
const uint64_t pipe = 0xE8E8F0F0E1LL;

RF24 radio(CE_PIN, CSN_PIN);

// Global variables
volatile bool isPaired = false;
volatile bool isSleeping = false;
unsigned long lastActivityTime = 0;

// Function declarations
void setLEDColor(const char* color);
void buzzerAlert(const char* pattern);
void vibrationAlert(bool isCrowd);
void enterSleep();
void initializeRadio();

void setup() {
  // Initialize pins with explicit states
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  
  pinMode(VIBRATION_PIN, OUTPUT);
  digitalWrite(VIBRATION_PIN, LOW);
  
  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);
  
  pinMode(WAKE_PIN, INPUT_PULLUP);
  
  // Configure SPI pins explicitly
  SPI.begin(SCK_PIN, MISO_PIN, MOSI_PIN, CSN_PIN);
  
  initializeRadio();

  // Setup wake button interrupt with debouncing
  attachInterrupt(digitalPinToInterrupt(WAKE_PIN), handleWakeButton, FALLING);
  
  // Initial LED state - Red (not paired)
  setLEDColor("red");
  
  // Configure deep sleep wakeup source
  esp_sleep_enable_ext0_wakeup(GPIO_NUM_5, 0); // WAKE_PIN must be GPIO_NUM_X
}

void initializeRadio() {
  // Initialize NRF24L01 with retry mechanism
  bool radioInitialized = false;
  for (int i = 0; i < RADIO_RETRY_COUNT && !radioInitialized; i++) {
    radioInitialized = radio.begin();
    if (!radioInitialized) {
      delay(RADIO_RETRY_DELAY);
    }
  }

  if (!radioInitialized) {
    // Error indication - rapid LED blinking
    while (1) {
      digitalWrite(LED_PIN, HIGH);
      delay(ERROR_BLINK_DURATION);
      digitalWrite(LED_PIN, LOW);
      delay(ERROR_BLINK_DURATION);
    }
  }

  // Enhanced radio configuration for reliability
  radio.setPALevel(RF24_PA_MAX);  // Maximum range for better connectivity
  radio.setDataRate(RF24_250KBPS);
  radio.setChannel(RADIO_CHANNEL);
  radio.setPayloadSize(RADIO_PAYLOAD_SIZE);
  radio.setRetries(3, 5);  // 3 retries, 5*250us delay between retries
  radio.openReadingPipe(1, pipe);
  radio.startListening();
}

void setLEDColor(const char* color) {
  if (strcmp(color, "blue") == 0) {
    digitalWrite(LED_PIN, HIGH);
    delay(LED_BLINK_DURATION);
    digitalWrite(LED_PIN, LOW);
    delay(LED_BLINK_DURATION);
    digitalWrite(LED_PIN, HIGH);
  } else if (strcmp(color, "green") == 0) {
    digitalWrite(LED_PIN, HIGH);
  } else if (strcmp(color, "red") == 0) {
    digitalWrite(LED_PIN, HIGH);
    delay(LED_BLINK_DURATION * 5);
    digitalWrite(LED_PIN, LOW);
  }
}

void buzzerAlert(const char* pattern) {
  noTone(BUZZER_PIN);  // Ensure buzzer is off before starting
  
  if (strcmp(pattern, "long") == 0) {
    tone(BUZZER_PIN, 2000, LONG_VIBRATION_DURATION);  // 2kHz tone
  } else if (strcmp(pattern, "single") == 0) {
    tone(BUZZER_PIN, 3000, VIBRATION_DURATION);  // 3kHz tone
  }
}

void vibrationAlert(bool isCrowd) {
  digitalWrite(VIBRATION_PIN, HIGH);
  delay(isCrowd ? LONG_VIBRATION_DURATION : VIBRATION_DURATION);
  digitalWrite(VIBRATION_PIN, LOW);
}

void enterSleep() {
  // Ensure all outputs are off before sleep
  noTone(BUZZER_PIN);
  digitalWrite(LED_PIN, LOW);
  digitalWrite(VIBRATION_PIN, LOW);
  digitalWrite(BUZZER_PIN, LOW);
  
  radio.powerDown();
  isSleeping = true;
  
  // Give a brief indication that device is going to sleep
  digitalWrite(LED_PIN, HIGH);
  delay(50);
  digitalWrite(LED_PIN, LOW);
  
  esp_deep_sleep_start();
}

void IRAM_ATTR handleWakeButton() {
  static unsigned long lastDebounceTime = 0;
  unsigned long currentTime = millis();
  
  // Simple debouncing
  if (currentTime - lastDebounceTime > 200) {
    if (isSleeping) {
      esp_sleep_wakeup_cause_t wakeup_reason = esp_sleep_get_wakeup_cause();
      if (wakeup_reason == ESP_SLEEP_WAKEUP_EXT0) {
        isSleeping = false;
        radio.powerUp();
        lastActivityTime = currentTime;
      }
    }
    lastDebounceTime = currentTime;
  }
}

void processCommand(char command) {
  switch (command) {
    case 'P':  // Pairing request
      if (!isPaired) {
        isPaired = true;
        setLEDColor("green");
        buzzerAlert("single");
        radio.stopListening();
        // Send acknowledgment with retry
        bool ackSent = false;
        for (int i = 0; i < RADIO_RETRY_COUNT && !ackSent; i++) {
          ackSent = radio.write("A", 1);
          if (!ackSent) delay(RADIO_RETRY_DELAY);
        }
        radio.startListening();
      }
      break;
      
    case 'H':  // High alert (obstacle detected)
      buzzerAlert("single");
      vibrationAlert(false);
      break;
      
    case 'C':  // Crowd detected
      buzzerAlert("long");
      vibrationAlert(true);
      break;
      
    case 'S':  // Sleep command
      enterSleep();
      break;
  }
  lastActivityTime = millis();
}

void loop() {
  if (!isSleeping) {
    if (radio.available()) {
      char command;
      radio.read(&command, 1);
      processCommand(command);
    }
    
    if (millis() - lastActivityTime > SLEEP_TIMEOUT) {
      enterSleep();
    }
  }
  delay(10);
}