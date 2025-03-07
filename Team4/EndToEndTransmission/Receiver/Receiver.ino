#include <SPI.h>
#include <RH_RF95.h>

#define RFM95_CS 10
#define RFM95_RST 9
#define RFM95_INT 2

#define RF95_FREQ 868.0

// Singleton instance of the radio driver
RH_RF95 rf95(RFM95_CS, RFM95_INT);

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

  rf95.setTxPower(23, false);
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
