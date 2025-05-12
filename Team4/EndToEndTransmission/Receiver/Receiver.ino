#include <SPI.h>
#include <RH_RF95.h>

#define RFM95_CS 10
#define RFM95_RST 9
#define RFM95_INT 2

#define RF95_FREQ 868.0

// #define SPI_BUS SPI1  // Uncomment if using SPI1
// #define SPI_BUS SPI2  // Uncomment if using SPI2


// Singleton instance of the radio driver
RH_RF95 rf95(RFM95_CS, RFM95_INT);

// Variables for tracking packets
uint16_t lastSequence = 0;
uint16_t packetsLost = 0;
bool firstPacket = true;
unsigned long lastPacketTime = 0;  // Track time of last packet
float packetRate = 0.0;           // Packets per second
unsigned long rateUpdateTime = 0;  // Time of last rate calculation
uint16_t packetCount = 0;         // Count packets for rate calculation 

void setup() {
  pinMode(RFM95_RST, OUTPUT);
  digitalWrite(RFM95_RST, HIGH);

  while (!Serial);
  Serial.begin(9600);
  delay(100);

  Serial.println("Arduino LoRa Receiver");

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

  // set bandwidth to 250 kHz instead of the default
  // Manually set modem configuration for 250 kHz bandwidth
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

void loop() {
  if (rf95.available()) {
    // Should be a message for us now
    uint8_t buf[RH_RF95_MAX_MESSAGE_LEN];
    uint8_t len = sizeof(buf);

    if (rf95.recv(buf, &len)) {
      // Ensure the string is null-terminated
      if (len < RH_RF95_MAX_MESSAGE_LEN) {
        buf[len] = 0;
      } else {
        buf[RH_RF95_MAX_MESSAGE_LEN - 1] = 0;
      }

      // Print diagnostics
      Serial.print("RSSI: ");
      Serial.println(rf95.lastRssi(), DEC);

      // Convert the received data to JSON format
      char jsonBuffer[256];
      convertToJson((char*)buf, jsonBuffer, sizeof(jsonBuffer));
      
      // Send the JSON data to Python via serial
      Serial.println(jsonBuffer);
      
      // Send an acknowledgment back
      const char* responseMsg = "ACK";
      rf95.send((uint8_t*)responseMsg, strlen(responseMsg));
      rf95.waitPacketSent();
    } else {
      Serial.println("Receive failed");
    }
  }
}



// Convert the received string format data to JSON
void convertToJson(char* input, char* jsonOutput, size_t maxSize) {
  // Calculate packet rate every second
  unsigned long currentTime = millis();
  if (currentTime - rateUpdateTime >= 1000) {  // Update rate every second
    packetRate = (float)packetCount * 1000.0 / (float)(currentTime - rateUpdateTime);
    packetCount = 0;  // Reset counter
    rateUpdateTime = currentTime;
  }
  packetCount++;  // Increment packet counter

  // Initialize JSON string
  strcpy(jsonOutput, "{");
  
  // Parse the input string which is in format "SEQ:{seq},P:{pitch},R:{roll},Y:{yaw},D:{distance},AX:{accelX},AY:{accelY},AZ:{accelZ},T:{timestamp}"
  char *token = strtok(input, ",");
  bool firstItem = true;
  uint16_t currentSequence = 0;
  
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
    if (token[0] == 'S' && token[1] == 'E' && token[2] == 'Q' && token[3] == ':') {  // Sequence
      strcpy(key, "\"sequence\"");
      char seqHex[4] = {0};
      strncpy(seqHex, token + 4, 3); // Get the 3 hex digits
      currentSequence = strtol(seqHex, NULL, 16); // Convert hex to decimal
      sprintf(jsonOutput + strlen(jsonOutput), "%s:%d", key, currentSequence);
      
      // Calculate packet loss
      if (!firstPacket) {
        // Expected next sequence
        uint16_t expectedSeq = (lastSequence + 1) & 0xFFF;
        
        // If current sequence is not what we expected
        if (currentSequence != expectedSeq) {
          // Calculate how many packets were lost
          uint16_t lost;
          if (currentSequence > expectedSeq) {
            lost = currentSequence - expectedSeq;
          } else {
            // Handle wrap-around
            lost = (0xFFF - expectedSeq) + currentSequence + 1;
          }
          packetsLost += lost;
        }
      } else {
        firstPacket = false;
      }
      
      // Update last sequence
      lastSequence = currentSequence;
      
      // Add packet loss stats to JSON
      sprintf(jsonOutput + strlen(jsonOutput), ",\"packets_lost\":%d", packetsLost);
      
      // Add packet rate to JSON
      char rateStr[15];
      dtostrf(packetRate, 1, 2, rateStr);
      sprintf(jsonOutput + strlen(jsonOutput), ",\"packet_rate\":%s", rateStr);
    }
    else if (token[0] == 'P' && token[1] == ':') {  // Pitch
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
    else if (token[0] == 'A' && token[1] == 'X' && token[2] == ':') {  // AccelX
      strcpy(key, "\"accel_x\"");
      value = atof(token + 3);  // Skip "AX:"
      char valueStr[15];
      dtostrf(value, 1, 2, valueStr);
      sprintf(jsonOutput + strlen(jsonOutput), "%s:%s", key, valueStr);
    }
    else if (token[0] == 'A' && token[1] == 'Y' && token[2] == ':') {  // AccelY
      strcpy(key, "\"accel_y\"");
      value = atof(token + 3);  // Skip "AY:"
      char valueStr[15];
      dtostrf(value, 1, 2, valueStr);
      sprintf(jsonOutput + strlen(jsonOutput), "%s:%s", key, valueStr);
    }
    else if (token[0] == 'A' && token[1] == 'Z' && token[2] == ':') {  // AccelZ
      strcpy(key, "\"accel_z\"");
      value = atof(token + 3);  // Skip "AZ:"
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
  
  // Add packet loss stats and rate to JSON
  sprintf(jsonOutput + strlen(jsonOutput), ",\"packets_lost\":%d,\"packet_rate\":%.2f", 
          packetsLost, packetRate);

    // Add RSSI to JSON
  sprintf(jsonOutput + strlen(jsonOutput), ",\"rssi\":%d", rf95.lastRssi());
  
  // Close the JSON object
  strcat(jsonOutput, "}");
}
