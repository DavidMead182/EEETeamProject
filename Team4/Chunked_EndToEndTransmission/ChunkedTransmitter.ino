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
#define MAX_PACKET_SIZE 32    // Maximum size of each packet
#define MAX_MESSAGE_SIZE 128  // Maximum size of the entire message before chunking

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
  
  // Initialize random seed for simulation
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
  float baseDistance = 100.0 + 50.0 * sin(data->yaw * PI / 180.0);
  float randomVariation = random(-10, 11);
  
  data->radarDistance = baseDistance + randomVariation;
}

// Send data in chunks
void sendChunkedData(SensorData data) {
  char fullMessage[MAX_MESSAGE_SIZE];
  
  // Format the full message
  sprintf(fullMessage, "P:%.2f,R:%.2f,Y:%.2f,D:%.2f,T:%lu", 
          data.pitch, data.roll, data.yaw, 
          data.radarDistance, data.timestamp);
  
  int messageLength = strlen(fullMessage);
  int numChunks = (messageLength + MAX_PACKET_SIZE - 1) / MAX_PACKET_SIZE;
  
  Serial.print("Full message: ");
  Serial.println(fullMessage);
  Serial.print("Message length: ");
  Serial.print(messageLength);
  Serial.print(" bytes, split into ");
  Serial.print(numChunks);
  Serial.println(" chunks");
  
  // Break message into chunks and send each one
  for (int i = 0; i < numChunks; i++) {
    char chunkBuffer[MAX_PACKET_SIZE + 2]; // +2 for header bytes
    
    // First byte: Chunk ID (0-F hex)
    // Format: 0x<chunk_id><sequence_number>
    // Using half-byte (4 bits) for chunk ID, and half-byte (4 bits) for sequence number
    uint8_t chunkHeader = (i & 0x0F) << 4 | (i & 0x0F);
    
    // Copy this chunk's portion of the message
    int chunkSize = min(MAX_PACKET_SIZE - 2, messageLength - i * (MAX_PACKET_SIZE - 2));
    
    // Add the header bytes to the chunk
    chunkBuffer[0] = chunkHeader;
    chunkBuffer[1] = numChunks; // Total number of chunks for continuity check
    
    // Copy the data for this chunk
    strncpy(chunkBuffer + 2, fullMessage + i * (MAX_PACKET_SIZE - 2), chunkSize);
    
    // Send the chunk
    Serial.print("Sending chunk ");
    Serial.print(i + 1);
    Serial.print("/");
    Serial.print(numChunks);
    Serial.print(": ");
    
    // Print the chunk header in hex
    Serial.print("Header: 0x");
    Serial.print(chunkHeader, HEX);
    Serial.print(", Data: ");
    
    // Print truncated chunk data for debugging
    char tempBuf[17]; // 16 chars + null terminator
    strncpy(tempBuf, chunkBuffer + 2, min(16, chunkSize));
    tempBuf[min(16, chunkSize)] = '\0';
    Serial.println(tempBuf);
    
    // Send the chunk
    rf95.send((uint8_t *)chunkBuffer, chunkSize + 2); // +2 for header bytes
    rf95.waitPacketSent();
    
    // Wait for acknowledgment
    uint8_t buf[RH_RF95_MAX_MESSAGE_LEN];
    uint8_t len = sizeof(buf);
    
    if (rf95.waitAvailableTimeout(500)) {
      if (rf95.recv(buf, &len)) {
        Serial.print("Got ACK for chunk ");
        Serial.print(i + 1);
        Serial.print(": ");
        Serial.println((char*)buf);
      } else {
        Serial.print("Failed to get ACK for chunk ");
        Serial.println(i + 1);
      }
    } else {
      Serial.print("No ACK received for chunk ");
      Serial.println(i + 1);
    }
    
    // Small delay between chunks
    delay(50);
  }
}

void loop() {
  SensorData currentData;
  
  // Get the current time
  currentData.timestamp = millis();
  
  // Get simulated sensor readings
  getIMUData(&currentData);
  getRadarData(&currentData);
  
  // Send the data in chunks
  sendChunkedData(currentData);
  
  // Wait before the next reading
  delay(UPDATE_INTERVAL);
}
