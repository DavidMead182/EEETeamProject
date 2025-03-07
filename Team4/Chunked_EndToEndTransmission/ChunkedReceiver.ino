#include <SPI.h>
#include <RH_RF95.h>

#define RFM95_CS 10
#define RFM95_RST 9
#define RFM95_INT 2

#define RF95_FREQ 868.0

// Singleton instance of the radio driver
RH_RF95 rf95(RFM95_CS, RFM95_INT);

// Constants for handling chunked messages
#define MAX_MESSAGE_SIZE 256  // Maximum size of reassembled message
#define MAX_CHUNKS 16        // Maximum number of chunks we can handle
#define CHUNK_TIMEOUT 2000   // Timeout for receiving all chunks (ms)

// Buffer to hold the reassembled message
char messageBuffer[MAX_MESSAGE_SIZE];
bool chunkReceived[MAX_CHUNKS]; // Track which chunks we've received
unsigned long lastChunkTime = 0; // Time when last chunk was received
int expectedChunks = 0;        // Number of chunks we're expecting

void setup() {
  pinMode(RFM95_RST, OUTPUT);
  digitalWrite(RFM95_RST, HIGH);

  while (!Serial);
  Serial.begin(9600);
  delay(100);

  Serial.println("Arduino LoRa Chunked Receiver");

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

  // The default transmitter power is 13dBm, using PA_BOOST.
  // If you are using RFM95/96/97/98 modules which uses the PA_BOOST transmitter pin, then
  // you can set transmitter powers from 5 to 23 dBm:
  rf95.setTxPower(23, false);
  
  // Initialize the chunk tracking
  resetChunkTracking();
}

// Reset our chunk tracking variables
void resetChunkTracking() {
  memset(messageBuffer, 0, MAX_MESSAGE_SIZE);
  memset(chunkReceived, 0, MAX_CHUNKS);
  lastChunkTime = 0;
  expectedChunks = 0;
}

// Check if we've received all expected chunks
bool allChunksReceived() {
  if (expectedChunks == 0) return false;
  
  for (int i = 0; i < expectedChunks; i++) {
    if (!chunkReceived[i]) return false;
  }
  return true;
}

// Process a received chunk
void processChunk(uint8_t *buf, uint8_t len) {
  if (len < 3) { // Need at least header bytes and some data
    Serial.println("Chunk too small to process");
    return;
  }
  
  // Extract header information
  uint8_t chunkHeader = buf[0];
  uint8_t chunkId = (chunkHeader >> 4) & 0x0F; // Extract upper 4 bits
  uint8_t seqNum = chunkHeader & 0x0F;         // Extract lower 4 bits
  uint8_t totalChunks = buf[1];
  
  // Validate chunk information
  if (chunkId >= MAX_CHUNKS || totalChunks > MAX_CHUNKS) {
    Serial.println("Invalid chunk header");
    return;
  }
  
  // Update expected chunks if this is new information
  if (expectedChunks == 0) {
    expectedChunks = totalChunks;
    lastChunkTime = millis();
  } 
  // If different total chunks reported, something's wrong
  else if (expectedChunks != totalChunks) {
    Serial.println("Chunk count mismatch - resetting");
    resetChunkTracking();
    return;
  }
  
  // Verify sequence number matches chunk ID for simple error checking
  if (seqNum != chunkId) {
    Serial.print("Sequence mismatch in chunk ");
    Serial.print(chunkId);
    Serial.print(", sequence: ");
    Serial.println(seqNum);
    // We'll still process it, but log the error
  }
  
  Serial.print("Received chunk ");
  Serial.print(chunkId + 1);
  Serial.print("/");
  Serial.print(totalChunks);
  Serial.print(" (Header: 0x");
  Serial.print(chunkHeader, HEX);
  Serial.println(")");
  
  // Calculate where in the buffer this chunk's data goes
  int dataSize = len - 2; // Subtract the 2 header bytes
  int bufferPos = chunkId * (MAX_MESSAGE_SIZE / MAX_CHUNKS);
  
  // Safety check to prevent buffer overflow
  if (bufferPos + dataSize >= MAX_MESSAGE_SIZE) {
    Serial.println("Chunk would overflow buffer - truncating");
    dataSize = MAX_MESSAGE_SIZE - bufferPos - 1;
  }
  
  // Copy the chunk data to the message buffer
  memcpy(messageBuffer + bufferPos, buf + 2, dataSize);
  messageBuffer[bufferPos + dataSize] = 0; // Ensure null terminated
  
  // Mark this chunk as received
  chunkReceived[chunkId] = true;
  lastChunkTime = millis();
  
  // Send acknowledgment
  char ackMsg[10];
  sprintf(ackMsg, "ACK:%d", chunkId);
  rf95.send((uint8_t*)ackMsg, strlen(ackMsg));
  rf95.waitPacketSent();
}

// Convert the received string format data to JSON
void convertToJson(char* input, char* jsonOutput, size_t maxSize) {
  // Initialize JSON string
  strcpy(jsonOutput, "{");
  
  // Parse the input string which is in format "P:{pitch},R:{roll},Y:{yaw},D:{distance},T:{timestamp}"
  char *token = strtok(input, ",");
  bool firstItem = true;
  
  while (token != NULL) {
    // Add comma if not the first item
    if (!firstItem) {
      strcat(jsonOutput, ",");
    } else {
      firstItem = false;
    }
    
    char key[20];
    float value;
    unsigned long timeValue;
    
    // Check what type of data this is
    if (token[0] == 'P' && token[1] == ':') {  // Pitch
      strcpy(key, "\"pitch\"");
      value = atof(token + 2);  // Skip "P:"
      char valueStr[15];
      dtostrf(value, 1, 2, valueStr);
      sprintf(jsonOutput + strlen(jsonOutput), "%s:%s", key, valueStr);
    }
    else if (token[0] == 'R' && token[1] == ':') {  // Roll
      strcpy(key, "\"roll\"");
      value = atof(token + 2);  // Skip "R:"
      char valueStr[15];
      dtostrf(value, 1, 2, valueStr);
      sprintf(jsonOutput + strlen(jsonOutput), "%s:%s", key, valueStr);
    }
    else if (token[0] == 'Y' && token[1] == ':') {  // Yaw
      strcpy(key, "\"yaw\"");
      value = atof(token + 2);  // Skip "Y:"
      char valueStr[15];
      dtostrf(value, 1, 2, valueStr);
      sprintf(jsonOutput + strlen(jsonOutput), "%s:%s", key, valueStr);
    }
    else if (token[0] == 'D' && token[1] == ':') {  // Distance
      strcpy(key, "\"distance\"");
      value = atof(token + 2);  // Skip "D:"
      char valueStr[15];
      dtostrf(value, 1, 2, valueStr);
      sprintf(jsonOutput + strlen(jsonOutput), "%s:%s", key, valueStr);
    }
    else if (token[0] == 'T' && token[1] == ':') {  // Timestamp
      strcpy(key, "\"timestamp\"");
      timeValue = atol(token + 2);  // Skip "T:"
      sprintf(jsonOutput + strlen(jsonOutput), "%s:%lu", key, timeValue);
    }
    
    // Get next token
    token = strtok(NULL, ",");
  }
  
  // Close the JSON object
  strcat(jsonOutput, "}");
}

void loop() {
  // Check for timeout on chunked message
  if (lastChunkTime > 0 && (millis() - lastChunkTime > CHUNK_TIMEOUT)) {
    Serial.println("Chunk timeout - resetting");
    resetChunkTracking();
  }
  
  // Check if we've received all chunks
  if (allChunksReceived() && expectedChunks > 0) {
    Serial.println("All chunks received, processing message:");
    Serial.println(messageBuffer);
    
    // Process the complete message
    char jsonBuffer[512];
    convertToJson(messageBuffer, jsonBuffer, sizeof(jsonBuffer));
    
    // Send the JSON data to Python via serial
    Serial.println(jsonBuffer);
    
    // Reset for the next message
    resetChunkTracking();
  }
  
  if (rf95.available()) {
    // Should be a message for us now
    uint8_t buf[RH_RF95_MAX_MESSAGE_LEN];
    uint8_t len = sizeof(buf);

    if (rf95.recv(buf, &len)) {
      // Print RSSI for diagnostics
      Serial.print("RSSI: ");
      Serial.println(rf95.lastRssi(), DEC);
      
      // Process this chunk
      processChunk(buf, len);
    } else {
      Serial.println("Receive failed");
    }
  }
}
