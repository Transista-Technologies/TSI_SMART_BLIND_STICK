#include <Wire.h>
#include <SparkFun_VL53L5CX_Library.h>

// Define Pins
#define I2C_0 Wire
#define I2C_1 Wire1
#define buzzer 3
#define vib_mot 19
#define led 2
#define buttonPin 7  // Tactile switch pin

// Sensor Objects
SparkFun_VL53L5CX myImager;
SparkFun_VL53L5CX myImager2;
VL53L5CX_ResultsData measurementData;
VL53L5CX_ResultsData measurementData2;

// Mode Variables
int mode = 0;  // 0 = Normal, 1 = Sensitive
int buttonState;
int pressCount = 0;  // Tracks button presses

// Function to get threshold based on mode
int getThreshold() {
    return (mode == 1) ? 600 : 300;  // 600mm for Sensitive, 300mm for Normal
}

// Function to vibrate motor on mode change
void vibrateMotor() {
    digitalWrite(vib_mot, HIGH);
    delay(200);
    digitalWrite(vib_mot, LOW);
}

// Function to beep buzzer on mode change
void beepBuzzer() {
    digitalWrite(buzzer, HIGH);
    delay(200);
    digitalWrite(buzzer, LOW);
}

void setup() {
    Serial.begin(115200);
    delay(2000);
    Serial.println("Initializing VL53L5CX...");

    pinMode(buzzer, OUTPUT);
    pinMode(vib_mot, OUTPUT);
    pinMode(led, OUTPUT);
    pinMode(buttonPin, INPUT_PULLUP);  // Tactile switch with internal pull-up

    // Configure I2C buses
    I2C_0.setSDA(4);
    I2C_0.setSCL(5);
    I2C_0.begin();

    I2C_1.setSDA(14);
    I2C_1.setSCL(15);
    I2C_1.begin();

    // Initialize Sensor 1
    while (!myImager.begin(VL53L5CX_DEFAULT_I2C_ADDRESS >> 1, I2C_0)) {
        Serial.println(F("Sensor 1 not found - check wiring."));
        delay(1000);
    }
    myImager.setResolution(4 * 4);
    myImager.startRanging();

    // Initialize Sensor 2
    while (!myImager2.begin(VL53L5CX_DEFAULT_I2C_ADDRESS >> 1, I2C_1)) {
        Serial.println(F("Sensor 2 not found - check wiring."));
        delay(1000);
    }
    myImager2.setResolution(4 * 4);
    myImager2.startRanging();
}

void loop() {
    // Read button state
    buttonState = digitalRead(buttonPin);

    // Detect press (tactile button only registers a brief LOW)
    if (buttonState == LOW) {
        pressCount++;  // Increment on each press
        mode = pressCount % 2;  // Cycles between 0 (Normal) and 1 (Sensitive)

        Serial.print("Switched to Mode: ");
        Serial.println(mode ? "Sensitive (600mm)" : "Normal (300mm)");

        // Provide feedback with vibration and beep
        vibrateMotor();
        beepBuzzer();

        // Wait until button is released before counting again
        while (digitalRead(buttonPin) == LOW); // Ensures a single count per press
        delay(10);  // Small delay to avoid accidental double count
    }

    // Get threshold based on mode
    int threshold = getThreshold();

    // Read Sensor 1
    if (myImager.isDataReady()) {
        if (myImager.getRangingData(&measurementData)) {  
            Serial.print("Mode: ");
            Serial.print(mode ? "Sensitive" : "Normal");
            Serial.print(" | Threshold: ");
            Serial.print(threshold);
            Serial.print(" | Distance 1 (mm): ");
            Serial.println(measurementData.distance_mm[0]); 

            if (measurementData.distance_mm[0] <= threshold) {
                digitalWrite(led, HIGH);
            } else {
                digitalWrite(led, LOW);
            }
        }
    } else {
        digitalWrite(led, LOW);
    }

    // Read Sensor 2
    if (myImager2.isDataReady()) {
        if (myImager2.getRangingData(&measurementData2)) {  
            Serial.print("Mode: ");
            Serial.print(mode ? "Sensitive" : "Normal");
            Serial.print(" | Threshold: ");
            Serial.print(threshold);
            Serial.print(" | Distance 2 (mm): ");
            Serial.println(measurementData2.distance_mm[0]); 

            if (measurementData2.distance_mm[0] <= threshold) {
                digitalWrite(buzzer, HIGH);
            } else {
                digitalWrite(buzzer, LOW);
            }
        }
    } else {
        digitalWrite(buzzer, LOW);
    }

    delay(100);  // Short delay to stabilize readings
}
