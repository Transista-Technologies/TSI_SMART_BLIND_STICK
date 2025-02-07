#include <Wire.h>
#include <SparkFun_VL53L5CX_Library.h>

SparkFun_VL53L5CX myImager;
VL53L5CX_ResultsData measurementData;

void setup() {
  Serial.begin(115200);
  Wire.begin();
  Wire.setClock(400000);

  Serial.println("Initializing VL53L5CX...");

  if (!myImager.begin()) {
    Serial.println("Sensor not found! Check connections.");
    while (1);
  }

  myImager.setResolution(8 * 8);  // Set resolution
  myImager.startRanging();
}

void loop() {
  if (myImager.isDataReady()) {
    if (myImager.getRangingData(&measurementData)) {  
      Serial.print("Distance (mm): ");
      Serial.println(measurementData.distance_mm[0]); // Print only the first sensor reading
    }
  }
  delay(100); // Delay for stable readings
}
