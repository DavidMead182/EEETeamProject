#include <SPI.h>
#include <RH_RF95.h>
#include <Wire.h>                                  // Qwiic I2C bus
#include "SparkFun_Qwiic_XM125_Arduino_Library.h"   // Radar library

#define RFM95_CS 10
#define RFM95_RST 9
#define RFM95_INT 2

#define RF95_FREQ 868.0

// Radar sensing range (in mm)
#define RANGE_START_MM 100
#define RANGE_END_MM   5000

// Constants for the simulation
#define UPDATE_INTERVAL 100  // ms between sensor readings (10Hz)
#define MAX_SEQUENCE 0xFFF   // 12-bit sequence number (0 to 4095)

// Singleton instances
RH_RF95 rf95(RFM95_CS, RFM95_INT);
SparkFunXM125Distance radar;                       // Radar sensor

// Global sequence number for tracking packets
uint16_t sequenceNumber = 0;

// Structure to hold our sensor data
struct SensorData {
  float pitch;
  float roll;
  float yaw;
  float radarDistance;
  float accelX;
  float accelY;
  float accelZ;
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
  
  // trying to force LoRa mode:
  rf95.spiWrite(0x01, 0x81);

  // Manually configure modem settings for 250 kHz bandwidth
  RH_RF95::ModemConfig config = {
    0x92, // RegModemConfig1: Bw = 250 kHz, Cr = 4/5
    0x74, // RegModemConfig2: SF = 7, TxContinuousMode = 0
    0x04  // RegModemConfig3: LowDataRateOptimize off, AgcAutoOn on
  };

  rf95.setModemRegisters(&config);
  rf95.setSpreadingFactor(10);
  // Set transmitter power
  rf95.setTxPower(23, false);
  
  // Initialize random seed for simulation
  randomSeed(analogRead(0));

  // Initialize radar
  Wire.begin();  // start I²C for Qwiic bus
  if (radar.distanceSetup(RANGE_START_MM, RANGE_END_MM)) {
    Serial.println("Radar setup failed!");
    while (1); // halt if radar won't initialize
  }
  Serial.println("Radar initialized OK");
}

// Simulates IMU data randomly
void getIMUData(SensorData *data) {
  static float basePitch = 0.0;
  static float baseRoll = 0.0;
  static float baseYaw = 0.0;
  static float baseAccelX = 0.0;
  static float baseAccelY = 0.0;
  static float baseAccelZ = 9.8; // Starting with approximate gravity
  
  basePitch += random(-5, 6) / 10.0;
  baseRoll += random(-5, 6) / 10.0;
  baseYaw += random(-10, 11) / 10.0;
  
  // Simulate acceleration with some random drift
  baseAccelX = 0.7 * baseAccelX + random(-20, 21) / 100.0;
  baseAccelY = 0.7 * baseAccelY + random(-20, 21) / 100.0;
  baseAccelZ = 0.95 * baseAccelZ + 0.05 * 9.8 + random(-10, 11) / 100.0;
  
  // Keep within bounds (I'm assuming our firefighter is probably not upside down) 
  if (basePitch > 45.0) basePitch = 45.0;
  if (basePitch < -45.0) basePitch = -45.0;
  if (baseRoll > 45.0) baseRoll = 45.0;
  if (baseRoll < -45.0) baseRoll = -45.0;
  // Yaw can be 0-360
  if (baseYaw >= 360.0) baseYaw -= 360.0;
  if (baseYaw < 0.0) baseYaw += 360.0;
  
  // Keep accelerations within reasonable bounds
  if (baseAccelX > 3.0) baseAccelX = 3.0;
  if (baseAccelX < -3.0) baseAccelX = -3.0;
  if (baseAccelY > 3.0) baseAccelY = 3.0;
  if (baseAccelY < -3.0) baseAccelY = -3.0;
  if (baseAccelZ > 12.0) baseAccelZ = 12.0;
  if (baseAccelZ < 7.0) baseAccelZ = 7.0;
  
  data->pitch = basePitch;
  data->roll = baseRoll;
  data->yaw = baseYaw;
  data->accelX = baseAccelX;
  data->accelY = baseAccelY;
  data->accelZ = baseAccelZ;
}

// Get real radar reading
void getRadarData(SensorData *data) {
  // Arm for a single distance read
  radar.detectorReadingSetup();

  // How many peaks do we see?
  uint32_t nPeaks = 0;
  radar.getNumberDistances(nPeaks);
  if (nPeaks == 0) {
    data->radarDistance = 0; // no returns
    return;
  }

  // Find the peak with the highest raw strength
  bool found = false;
  int32_t bestStrength = 0;
  uint32_t bestDistance = 0;

  for (uint32_t i = 0; i < nPeaks; ++i) {
    uint32_t d = 0;
    int32_t  s = 0;
    if (radar.getPeakDistance(i, d) != ksfTkErrOk ||
        radar.getPeakStrength(i, s) != ksfTkErrOk) {
      continue;
    }
    if (!found || s > bestStrength) {
      found = true;
      bestStrength = s;
      bestDistance = d;
    }
  }

  // NOTE: bestDistance is returned in raw millimetres as reported by the sensor.
  // The code given scaled from 0-1, more like
  //   float scaled = float(bestDistance - RANGE_START_MM)
  //                / float(RANGE_END_MM   - RANGE_START_MM);
  data->radarDistance = bestDistance;
}

void sendData(SensorData data) {
  char pitchStr[8], rollStr[8], yawStr[8], distanceStr[8];
  char accelXStr[8], accelYStr[8], accelZStr[8];
  char seqHex[4]; // 3 hex chars + null terminator
  char dataPacket[256]; // Increased size for additional data
  
  // Increment sequence number and wrap around
  sequenceNumber = (sequenceNumber + 1) & MAX_SEQUENCE;
  
  // Convert sequence number to 3-digit hex
  sprintf(seqHex, "%03X", sequenceNumber);
  
  // Convert floats to strings manually
  dtostrf(data.pitch, 6, 2, pitchStr);
  dtostrf(data.roll, 6, 2, rollStr);
  dtostrf(data.yaw, 6, 2, yawStr);
  dtostrf(data.radarDistance, 6, 2, distanceStr);
  dtostrf(data.accelX, 6, 2, accelXStr);
  dtostrf(data.accelY, 6, 2, accelYStr);
  dtostrf(data.accelZ, 6, 2, accelZStr);

  // Format data as a simple string
  // Format: "SEQ:{seq},P:{pitch},R:{roll},Y:{yaw},D:{distance},AX:{accelX},AY:{accelY},AZ:{accelZ},T:{timestamp}"
  sprintf(dataPacket, "SEQ:%s,P:%s,R:%s,Y:%s,D:%s,AX:%s,AY:%s,AZ:%s,T:%lu", 
          seqHex, pitchStr, rollStr, yawStr, distanceStr, 
          accelXStr, accelYStr, accelZStr, data.timestamp);
  
  int packetLength = strlen(dataPacket);
  
  // Send the packet
  rf95.send((uint8_t *)dataPacket, packetLength);
  rf95.waitPacketSent();
  
  // Wait for a reply (acknowledgment)
  uint8_t buf[RH_RF95_MAX_MESSAGE_LEN];
  uint8_t len = sizeof(buf);
  
  if (rf95.waitAvailableTimeout(500)) {
    if (rf95.recv(buf, &len)) {
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
  
  // Get simulated IMU readings
  getIMUData(&currentData);
  
  // Get real radar reading
  getRadarData(&currentData);
  
  // Send the data
  sendData(currentData);
  
  // Wait before the next reading
  delay(UPDATE_INTERVAL);
}
