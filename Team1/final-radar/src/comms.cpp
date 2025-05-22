#include "comms.h"

#include <SPI.h>
#include "RH_RF95.h"
// #include "RHHardwareSPI1.h"

#define RFM95_CS  3 
#define RFM95_RST 4
#define RFM95_INT 5

#define RF95_FREQ 868.0

// Singleton instance of the radio driver
RH_RF95 rf95(RFM95_CS, RFM95_INT);

// Constants for the simulation
#define UPDATE_INTERVAL 100    // ms between sensor readings (10Hz)
#define MAX_SEQUENCE    0xFFF  // 12-bit sequence number (0 to 4095)

// #define SPI_BUS SPI1

uint16_t sequence_number = 0;

bool comms_setup() {
    pinMode(RFM95_RST, OUTPUT);
    digitalWrite(RFM95_RST, HIGH);

    // manual reset
    digitalWrite(RFM95_RST, LOW);
    delay(10);
    digitalWrite(RFM95_RST, HIGH);
    delay(10);

    while (!rf95.init()) {
        Serial.println("LoRa radio init failed");
        return false;
    }
    Serial.println("LoRa radio init OK!");

    // Set frequency
    if (!rf95.setFrequency(RF95_FREQ)) {
        Serial.println("setFrequency failed");
        return false;    
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
    rf95.setSpreadingFactor(7);
    // Set transmitter power
    rf95.setTxPower(23, false);

    return true;
}

bool comms_send_data(comms_sensor_data_t *data) {
    char pitchStr[8], rollStr[8], yawStr[8], distanceStr[8];
    char accelXStr[8], accelYStr[8], accelZStr[8];
    char seqHex[4];         // 3 hex chars + null terminator
    char dataPacket[256];   // Increased size for additional data

    // Increment sequence number and wrap around
    sequence_number = (sequence_number + 1) & MAX_SEQUENCE;

    // Convert sequence number to 3-digit hex
    sprintf(seqHex, "%03X", sequence_number);

    // Convert floats to strings manually
    dtostrf(data->pitch, 6, 2, pitchStr);
    dtostrf(data->roll, 6, 2, rollStr);
    dtostrf(data->yaw, 6, 2, yawStr);
    dtostrf(data->radarDistance, 6, 2, distanceStr);
    dtostrf(data->accelX, 6, 2, accelXStr);
    dtostrf(data->accelY, 6, 2, accelYStr);
    dtostrf(data->accelZ, 6, 2, accelZStr);

    Serial.println("Converted shite");
    
    // Format data as a simple string
    // Format: "SEQ:{seq},P:{pitch},R:{roll},Y:{yaw},D:{distance},AX:{accelX},AY:{accelY},AZ:{accelZ},T:{timestamp}"
    sprintf(dataPacket, "SEQ:%s,P:%s,R:%s,Y:%s,D:%s,AX:%s,AY:%s,AZ:%s,T:%llu",
        seqHex, pitchStr, rollStr, yawStr, distanceStr,
        accelXStr, accelYStr, accelZStr, data->timestamp);
        
    int packetLength = strlen(dataPacket);
    Serial.println("Done the sprintf");
    Serial.println(packetLength);
    
    // Send the packet
    rf95.send((uint8_t *)dataPacket, packetLength);
    Serial.println("Done the packet send");
    // rf95.waitPacketSent();
    // Serial.println("Packet sent");

    Serial.println(RH_RF95_MAX_MESSAGE_LEN);
    
    // Wait for a reply (acknowledgment)
    uint8_t buf[RH_RF95_MAX_MESSAGE_LEN];
    uint8_t len = sizeof(buf);


    if (rf95.waitAvailableTimeout(500)) {
        if (rf95.recv(buf, &len)) {
            Serial.print("RSSI: ");
            Serial.println(rf95.lastRssi(), DEC);
        } else {
            Serial.println("Receive failed");
            return false;
        }
    } else {
        Serial.println("No reply from receiver");
        return false;
    }

    return true;
}
