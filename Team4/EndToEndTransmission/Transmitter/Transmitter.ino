#include <SPI.h>
#include <RH_RF95.h>
#include <RHHardwareSPI1.h>

#define RFM95_CS 38
#define RFM95_RST 29
#define RFM95_INT 28
#define RF95_FREQ 868.0

RH_RF95 rf95(RFM95_CS, RFM95_INT, hardware_spi1);

#define UPDATE_INTERVAL 100
#define MAX_SEQUENCE 0xFF  // Reduced to 8-bit (0-255)

uint8_t sequenceNumber = 0;

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

// Packed binary structure - 27 bytes total
struct __attribute__((packed)) PackedData {
  uint8_t seq;           // 1 byte
  int16_t pitch;         // 2 bytes (scaled by 100)
  int16_t roll;          // 2 bytes (scaled by 100)
  uint16_t yaw;          // 2 bytes (scaled by 100)
  uint32_t distance;     // 4 bytes (scaled by 100)
  int16_t accelX;        // 2 bytes (scaled by 1000)
  int16_t accelY;        // 2 bytes (scaled by 1000)
  int16_t accelZ;        // 2 bytes (scaled by 1000)
  uint32_t timestamp;    // 4 bytes
  uint16_t checksum;     // 2 bytes (simple checksum)
};

void setup() {
  pinMode(RFM95_RST, OUTPUT);
  digitalWrite(RFM95_RST, HIGH);

  while (!Serial);
  Serial.begin(9600);
  delay(100);

  digitalWrite(RFM95_RST, LOW);
  delay(10);
  digitalWrite(RFM95_RST, HIGH);
  delay(10);

  while (!rf95.init()) {
    Serial.println("LoRa radio init failed");
    while (1);
  }
  Serial.println("LoRa radio init OK!");

  if (!rf95.setFrequency(RF95_FREQ)) {
    Serial.println("setFrequency failed");
    while (1);
  }
  Serial.print("Set Freq to: "); Serial.println(RF95_FREQ);

  rf95.spiWrite(0x01, 0x81);

  RH_RF95::ModemConfig config = {
    0x92, // RegModemConfig1: Bw = 250 kHz, Cr = 4/5
    0x74, // RegModemConfig2: SF = 7, TxContinuousMode = 0
    0x04  // RegModemConfig3: LowDataRateOptimize off, AgcAutoOn on
  };

  rf95.setModemRegisters(&config);
  rf95.setSpreadingFactor(10);
  rf95.setTxPower(23, false);

  randomSeed(analogRead(0));
}

void getIMUData(SensorData *data) {
  static float basePitch = 0.0;
  static float baseRoll = 0.0;
  static float baseYaw = 0.0;
  static float baseAccelX = 0.0;
  static float baseAccelY = 0.0;
  static float baseAccelZ = 9.8;

  basePitch += random(-5, 6) / 10.0;
  baseRoll += random(-5, 6) / 10.0;
  baseYaw += random(-10, 11) / 10.0;

  baseAccelX = 0.7 * baseAccelX + random(-20, 21) / 100.0;
  baseAccelY = 0.7 * baseAccelY + random(-20, 21) / 100.0;
  baseAccelZ = 0.95 * baseAccelZ + 0.05 * 9.8 + random(-10, 11) / 100.0;

  if (basePitch > 45.0) basePitch = 45.0;
  if (basePitch < -45.0) basePitch = -45.0;
  if (baseRoll > 45.0) baseRoll = 45.0;
  if (baseRoll < -45.0) baseRoll = -45.0;
  if (baseYaw >= 360.0) baseYaw -= 360.0;
  if (baseYaw < 0.0) baseYaw += 360.0;

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

void getRadarData(SensorData *data) {
  float baseDistance = 100.0 + 50.0 * sin(data->yaw * PI / 180.0);
  float randomVariation = random(-10, 11);
  data->radarDistance = baseDistance + randomVariation;
}

uint16_t calculateChecksum(PackedData* data) {
  uint16_t checksum = 0;
  uint8_t* bytes = (uint8_t*)data;
  for (int i = 0; i < sizeof(PackedData) - 2; i++) { // Exclude checksum itself
    checksum += bytes[i];
  }
  return checksum;
}

void sendData(SensorData data) {
  PackedData packet;
  
  sequenceNumber = (sequenceNumber + 1) & 0xFF;
  
  packet.seq = sequenceNumber;
  packet.pitch = (int16_t)(data.pitch * 100);      // ±327.67 degrees, 0.01 precision
  packet.roll = (int16_t)(data.roll * 100);        // ±327.67 degrees, 0.01 precision
  packet.yaw = (uint16_t)(data.yaw * 100);         // 0-655.35 degrees, 0.01 precision
  packet.distance = (uint32_t)(data.radarDistance * 100); // 0-42949672.95 cm, 0.01 precision
  packet.accelX = (int16_t)(data.accelX * 1000);   // ±32.767 m/s², 0.001 precision
  packet.accelY = (int16_t)(data.accelY * 1000);   // ±32.767 m/s², 0.001 precision
  packet.accelZ = (int16_t)(data.accelZ * 1000);   // ±32.767 m/s², 0.001 precision
  packet.timestamp = data.timestamp;
  packet.checksum = calculateChecksum(&packet);

  // Send binary packet - only 27 bytes vs ~80+ in string format
  rf95.send((uint8_t*)&packet, sizeof(PackedData));
  rf95.waitPacketSent();

  // Wait for acknowledgment
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
  currentData.timestamp = millis();
  
  getIMUData(&currentData);
  getRadarData(&currentData);
  sendData(currentData);
  
  delay(UPDATE_INTERVAL);
}