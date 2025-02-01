// Pin definitions for XIAO ESP32 S3
const int LED_PIN = 2;      // LED connected to GPIO2
const int MOTOR_PIN = 6;    // Vibration motor connected to GPIO6

void setup() {
  // Configure pins as outputs
  pinMode(LED_PIN, OUTPUT);
  pinMode(MOTOR_PIN, OUTPUT);
 
  // Initial state - everything off
  digitalWrite(LED_PIN, LOW);
  digitalWrite(MOTOR_PIN, LOW);
}

void loop() {
  // Turn on LED and motor
  digitalWrite(LED_PIN, HIGH);
  digitalWrite(MOTOR_PIN, HIGH);
 
  // Keep them on for 2 seconds
  delay(2000);
 
  // Turn off LED and motor
  digitalWrite(LED_PIN, LOW);
  digitalWrite(MOTOR_PIN, LOW);
 
  // Wait for 2 seconds before next cycle
  delay(2000);
}