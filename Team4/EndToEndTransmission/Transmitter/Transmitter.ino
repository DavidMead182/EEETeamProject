#include <SPI.h>
#include <RH_RF95.h>

#define RFM95_CS 10
#define RFM95_RST 9
#define RFM95_INT 2

#define RF95_FREQ 868.0

// Singleton instance of the radio driver
RH_RF95 rf95(RFM95_CS, RFM95_INT);

// Constants for the simulation
#define UPDATE_INTERVAL 100  // ms between sensor readings

// Structure to hold our sensor data
struct SensorData {
  float pitch;
  float roll;
  float yaw;
  float radarDistance;
  unsigned long timestamp;
};

void setup() {
  pinMode(RFM95_RST, OUTPUT);
  digitalWrite(RFM95_RST, HIGH);

  while (!Serial);
  Serial.begin(9600);
  delay(100);

  // manual reset
  digitalWrite(RFM95_RST, LOW);
  delay(10);
  digitalWrite(RFM95_RST, HIGH);
  delay(10);

  while (!rf95.init()) {
    Serial.println("LoRa radio init failed");
    while (1);
  }
  Serial.println("LoRa radio init OK!");

  // Set frequency
  if (!rf95.setFrequency(RF95_FREQ)) {
    Serial.println("setFrequency failed");
    while (1);
  }
  Serial.print("Set Freq to: "); Serial.println(RF95_FREQ);
  
  // Set transmitter power
  rf95.setTxPower(23, false);
  
  // Initialize random seed for simulation (lets us have a little bit of consistency)
  randomSeed(analogRead(0));
}

// Simulates IMU data randomly
void getIMUData(SensorData *data) {
  static float basePitch = 0.0;
  static float baseRoll = 0.0;
  static float baseYaw = 0.0;
  
  basePitch += random(-5, 6) / 10.0;
  baseRoll += random(-5, 6) / 10.0;
  baseYaw += random(-10, 11) / 10.0;
  
  // Keep within bounds (I'm assuming our firefighter is probably not upside down) 
  if (basePitch > 45.0) basePitch = 45.0;
  if (basePitch < -45.0) basePitch = -45.0;
  if (baseRoll > 45.0) baseRoll = 45.0;
  if (baseRoll < -45.0) baseRoll = -45.0;
  // Yaw can be 0-360
  if (baseYaw >= 360.0) baseYaw -= 360.0;
  if (baseYaw < 0.0) baseYaw += 360.0;
  
  data->pitch = basePitch;
  data->roll = baseRoll;
  data->yaw = baseYaw;
}

// Simulates radar distance reading
void getRadarData(SensorData *data) {
  // Simulate distance based on facing direction (yaw)
  // For this I'll make the distance vary based on yaw
  float baseDistance = 100.0 + 50.0 * sin(data->yaw * PI / 180.0);
  float randomVariation = random(-10, 11);
  
  data->radarDistance = baseDistance + randomVariation;
}

void sendData(SensorData data) {
  char pitchStr[8], rollStr[8], yawStr[8], distanceStr[8];
  char dataPacket[128];
  // Convert floats to strings manually
  dtostrf(data.pitch, 6, 2, pitchStr);
  dtostrf(data.roll, 6, 2, rollStr);
  dtostrf(data.yaw, 6, 2, yawStr);
  dtostrf(data.radarDistance, 6, 2, distanceStr);

  // Format data as a simple string
  // Format: "P:{pitch},R:{roll},Y:{yaw},D:{distance},T:{timestamp}"
  sprintf(dataPacket, "P:%s,R:%s,Y:%s,D:%s,T:%lu", 
          pitchStr, rollStr, yawStr, distanceStr, data.timestamp);
  
  int packetLength = strlen(dataPacket);
  
  Serial.print("Sending data: "); 
  Serial.println(dataPacket);
  
  // Send the packet
  rf95.send((uint8_t *)dataPacket, packetLength);
  rf95.waitPacketSent();
  
  // Wait for a reply (acknowledgment)
  uint8_t buf[RH_RF95_MAX_MESSAGE_LEN];
  uint8_t len = sizeof(buf);
  
  if (rf95.waitAvailableTimeout(500)) {
    if (rf95.recv(buf, &len)) {
      Serial.print("Got reply: ");
      Serial.println((char*)buf);
      Serial.print("RSSI: ");
      Serial.println(rf95.lastRssi(), DEC);
    } else {
      Serial.println("Receive failed");
    }
  } else {
    Serial.println("No reply from receiver");
  }
}

void loop() {
  SensorData currentData;
  
  // Get the current time
  currentData.timestamp = millis();
  
  // Get simulated sensor readings
  getIMUData(&currentData);
  getRadarData(&currentData);
  
  // Send the data
  sendData(currentData);
  
  // Wait before the next reading
  delay(UPDATE_INTERVAL);
}
