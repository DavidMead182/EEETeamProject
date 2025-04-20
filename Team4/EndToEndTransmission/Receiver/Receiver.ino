#include <SPI.h>
#include <SX127x.h>

// Pin definitions
#define NSS_PIN 10
#define RESET_PIN 9
#define DIO0_PIN 2
#define TXEN_PIN -1  
#define RXEN_PIN -1  

// Frequency setting
#define RF_FREQUENCY 868000000  


SX127x LoRa;


uint16_t lastSequence = 0;
uint16_t packetsLost = 0;
bool firstPacket = true;
unsigned long lastPacketTime = 0;  // Track time of last packet
float packetRate = 0.0;           // Packets per second
unsigned long rateUpdateTime = 0;  // Time of last rate calculation
uint16_t packetCount = 0;         // Count packets for rate calculation

void setup() {
  while (!Serial);
  Serial.begin(9600);
  delay(100);

  Serial.println("Arduino LoRa Receiver");

  // Configure pins
  LoRa.setPins(NSS_PIN, RESET_PIN, DIO0_PIN, TXEN_PIN, RXEN_PIN);
  
  // Initialize LoRa module
  if (!LoRa.begin()) {
    Serial.println("LoRa radio init failed");
    while (1);
  }
  Serial.println("LoRa radio init OK!");

  LoRa.setFrequency(RF_FREQUENCY);
  Serial.print("Set Freq to: "); Serial.println(RF_FREQUENCY / 1000000.0);
  
  // Bandwidth 250 kHz, Spreading Factor 10, Coding Rate 4/5
  LoRa.setLoRaModulation(10, 250000, 5, false);
  
  // Explicit header mode, preamble length 8, payload length variable, CRC on, no invert IQ
  LoRa.setLoRaPacket(LORA_HEADER_EXPLICIT, 8, 0, true, false);
  
  LoRa.setTxPower(20, SX127X_TX_POWER_PA_BOOST);
  
  // Set receive gain to boosted
  LoRa.setRxGain(LORA_RX_GAIN_BOOSTED);
  
  rateUpdateTime = millis();
}

void loop() {
  LoRa.request();
  LoRa.wait();
  
  if (LoRa.available()) {
    char buf[256];
    int i = 0;
    
    while (LoRa.available() && i < 255) {
      buf[i++] = LoRa.read();
    }
    buf[i] = '\0';  // Null terminate
    
    Serial.print("RSSI: ");
    Serial.println(LoRa.packetRssi());
    
    char jsonBuffer[256];
    convertToJson(buf, jsonBuffer, sizeof(jsonBuffer));
    
    // Send the JSON data to Python via serial
    Serial.println(jsonBuffer);
    
    const char* responseMsg = "ACK";
    LoRa.beginPacket();
    LoRa.write((uint8_t*)responseMsg, strlen(responseMsg));
    LoRa.endPacket();
    LoRa.wait();
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
      
      lastSequence = currentSequence;
      
      // Add packet loss stats and rate to JSON using dtostrf for proper float formatting
      char rateStr[10];
      dtostrf(packetRate, 1, 2, rateStr);  // Convert float to string with 2 decimal places
      sprintf(jsonOutput + strlen(jsonOutput), ",\"packets_lost\":%d,\"packet_rate\":%s", 
              packetsLost, rateStr);
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
  
  // Close the JSON object
  strcat(jsonOutput, "}");
}