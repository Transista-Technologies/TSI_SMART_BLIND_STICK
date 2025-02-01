#include <SPI.h>
#include <RF24.h>

// Pin definitions
#define CE_PIN 3
#define CSN_PIN 1
#define BUZZER_PIN 4
#define VIBRATION_PIN 6
#define LED_PIN 2

// Radio pipe address for right slave
const uint64_t RIGHT_PIPE = 0x00F1F1F1F1LL;

// Initialize RF24 object
RF24 radio(CE_PIN, CSN_PIN);

void setup() {
  // Initialize pins
  pinMode(LED_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(VIBRATION_PIN, OUTPUT);
  
  // Initialize radio
  SPI.begin();
  radio.begin();
  radio.setPALevel(RF24_PA_MAX);
  radio.setDataRate(RF24_250KBPS);
  radio.setChannel(108);
  radio.setPayloadSize(1);
  radio.openReadingPipe(1, RIGHT_PIPE);
  radio.startListening();
  
  // Initial LED flash to show it's working
  digitalWrite(LED_PIN, HIGH);
  delay(500);
  digitalWrite(LED_PIN, LOW);
}

void indicate_signal() {
  // Flash LED
  digitalWrite(LED_PIN, HIGH);
  
  // Short beep
  tone(BUZZER_PIN, 2000, 100);
  
  // Short vibration
  digitalWrite(VIBRATION_PIN, HIGH);
  delay(100);
  
  // Turn everything off
  digitalWrite(LED_PIN, LOW);
  digitalWrite(VIBRATION_PIN, LOW);
}

void loop() {
  if (radio.available()) {
    char received;
    radio.read(&received, 1);
    
    // Only respond to 'R' signal
    if (received == 'R') {
      indicate_signal();
    }
  }
  delay(10);
}