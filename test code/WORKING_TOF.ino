#include <Wire.h>
#include <SparkFun_VL53L5CX_Library.h>

// Use predefined Wire objects for RP2040
#define I2C_0 Wire
#define I2C_1 Wire1
#define buzzer 3
#define vib_mot 19
#define led 2

#define dist 600

SparkFun_VL53L5CX myImager;
SparkFun_VL53L5CX myImager2;
VL53L5CX_ResultsData measurementData;
VL53L5CX_ResultsData measurementData2;

void setup() {
  Serial.begin(115200);
  delay(2000);
  Serial.println("Initializing VL53L5CX...");

  pinMode(buzzer, OUTPUT);
  pinMode(vib_mot,OUTPUT);
  pinMode(led,OUTPUT);

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
      


  if (myImager.isDataReady()) {
    if (myImager.getRangingData(&measurementData)) {  
      Serial.print("Distance 1 (mm): ");
      Serial.println(measurementData.distance_mm[0]); // Print first measurement
      if (measurementData.distance_mm[0] <= dist){
        digitalWrite(led, HIGH);
      }
      else 
        digitalWrite(led,LOW);
    }
  }
  else {
    digitalWrite(led,LOW);
  }

  if (myImager2.isDataReady()) {
    if (myImager2.getRangingData(&measurementData2)) {  
      Serial.print("Distance 2 (mm): ");
      Serial.println(measurementData2.distance_mm[0]); // Print first measurement
      if (measurementData2.distance_mm[0] <= dist){
        digitalWrite(buzzer, HIGH);
      }
      else 
        digitalWrite(buzzer,LOW);
    }
  }
  else{
      digitalWrite(buzzer,LOW);
  }
  
  

  delay(100); // Delay for stable readings
}
