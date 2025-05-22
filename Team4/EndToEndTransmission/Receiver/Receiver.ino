#include <SPI.h>
#include <RH_RF95.h>
#include <RHHardwareSPI1.h>

#define RFM95_CS 38
#define RFM95_RST 29
#define RFM95_INT 28
#define RF95_FREQ 868.0

RH_RF95 rf95(RFM95_CS, RFM95_INT, hardware_spi1);


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
  uint16_t checksum;     // 2 bytes
};

// Variables for tracking packets
uint8_t lastSequence = 0;
uint16_t packetsLost = 0;
bool firstPacket = true;
unsigned long lastPacketTime = 0;
float packetRate = 0.0;
unsigned long rateUpdateTime = 0;
uint16_t packetCount = 0;

void setup() {
  pinMode(RFM95_RST, OUTPUT);
  digitalWrite(RFM95_RST, HIGH);

  while (!Serial);
  Serial.begin(9600);
  delay(100);

  Serial.println("Arduino LoRa Receiver");

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

  rateUpdateTime = millis();
}

uint16_t calculateChecksum(PackedData* data) {
  uint16_t checksum = 0;
  uint8_t* bytes = (uint8_t*)data;
  for (int i = 0; i < sizeof(PackedData) - 2; i++) { // Exclude checksum itself
    checksum += bytes[i];
  }
  return checksum;
}

void convertBinaryToJson(PackedData* packet, char* jsonOutput, size_t maxSize) {
  // Calculate packet rate every second
  unsigned long currentTime = millis();
  if (currentTime - rateUpdateTime >= 1000) {
    packetRate = (float)packetCount * 1000.0 / (float)(currentTime - rateUpdateTime);
    packetCount = 0;
    rateUpdateTime = currentTime;
  }
  packetCount++;

  // Verify checksum
  uint16_t calculatedChecksum = calculateChecksum(packet);
  bool checksumValid = (calculatedChecksum == packet->checksum);

  // Calculate packet loss
  if (!firstPacket) {
    uint8_t expectedSeq = (lastSequence + 1) & 0xFF;
    if (packet->seq != expectedSeq) {
      uint8_t lost;
      if (packet->seq > expectedSeq) {
        lost = packet->seq - expectedSeq;
      } else {
        // Handle wrap-around
        lost = (0xFF - expectedSeq) + packet->seq + 1;
      }
      packetsLost += lost;
    }
  } else {
    firstPacket = false;
  }
  lastSequence = packet->seq;

  // Convert scaled integers back to floats and create JSON
  float pitch = packet->pitch / 100.0;
  float roll = packet->roll / 100.0;
  float yaw = packet->yaw / 100.0;
  float distance = packet->distance / 100.0;
  float accelX = packet->accelX / 1000.0;
  float accelY = packet->accelY / 1000.0;
  float accelZ = packet->accelZ / 1000.0;

  // Build JSON string
  snprintf(jsonOutput, maxSize,
    "{\"sequence\":%d,\"packets_lost\":%d,\"packet_rate\":%.2f,\"rssi\":%d,"
    "\"pitch\":%.2f,\"roll\":%.2f,\"yaw\":%.2f,\"distance\":%.2f,"
    "\"accel_x\":%.3f,\"accel_y\":%.3f,\"accel_z\":%.3f,"
    "\"timestamp\":%lu,\"checksum_valid\":%s}",
    packet->seq, packetsLost, packetRate, rf95.lastRssi(),
    pitch, roll, yaw, distance,
    accelX, accelY, accelZ,
    packet->timestamp, checksumValid ? "true" : "false");
}

void loop() {
  if (rf95.available()) {
    uint8_t buf[RH_RF95_MAX_MESSAGE_LEN];
    uint8_t len = sizeof(buf);

    if (rf95.recv(buf, &len)) {
      // Check if we received the correct packet size
      if (len == sizeof(PackedData)) {
        PackedData* packet = (PackedData*)buf;
        
        // Print diagnostics
        Serial.print("RSSI: ");
        Serial.println(rf95.lastRssi(), DEC);

        // Convert binary data to JSON
        char jsonBuffer[512];
        convertBinaryToJson(packet, jsonBuffer, sizeof(jsonBuffer));

        // Send JSON data to Python via serial
        Serial.println(jsonBuffer);
      } else {
        Serial.print("Wrong packet size: ");
        Serial.print(len);
        Serial.print(" expected: ");
        Serial.println(sizeof(PackedData));
      }

      // Send acknowledgment
      const char* responseMsg = "ACK";
      rf95.send((uint8_t*)responseMsg, strlen(responseMsg));
      rf95.waitPacketSent();
    } else {
      Serial.println("Receive failed");
    }
  }
}