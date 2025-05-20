#include <Arduino.h>
#include <arduino-timer.h>
#include <Wire.h>
#include "radar.h"
#include "imu.h"

void setup() {
    Serial.begin(921600);
    Serial.println("XM125 Example 9: Basic Advanced Settings");

    Wire.begin();

    radar_setup(20, 7000);

    imu_setup();


    delay(1000);
}

void loop() {
    radar_check_errors();

    // Read PeakX Distance and PeakX Strength registers for the number of distances detected
    uint64_t timestamp = millis();

    int n = 9;
    uint32_t distances[n]; 
    int32_t  strengths[n];

    radar_get_distances(distances, n);
    radar_get_strengths(strengths, n);

    for (int i = 0; i < n; i++) {
        if (distances[i] == 0) {
            Serial.print(1E8);
        } else {    
            Serial.print(distances[i]);
        }
        
        Serial.print(",");
    }

    for (int i = 0; i < n; i++) {
        Serial.print(strengths[i]);

        if (i != n-1) Serial.print(",");
    }

    imu_packet packet;
    imu_read_packet(&packet);
    if (!packet.valid) { return; }

    Serial.print(packet.x_rate);
    Serial.print(","); 
    Serial.print(packet.y_rate);
    Serial.print(","); 
    Serial.print(packet.z_rate);
    Serial.print(","); 
    Serial.print(packet.x_acc);
    Serial.print(","); 
    Serial.print(packet.y_acc); 
    Serial.print(","); 
    Serial.print(packet.z_acc);
    Serial.print(","); 
    Serial.print(packet.temp);
    Serial.print(","); 
    Serial.print(packet.roll);
    Serial.print(","); 
    Serial.print(packet.pitch);
    Serial.print(","); 
    Serial.print(packet.yaw);
    Serial.print("\n"); 
}


// LOGGING FORMAT:
// MAGX,MAGY,MAGZ,TIMESTAMP,DISTANCE0,DISTANCE1...DISTANCE8,STRENGTH0,STRENGTH1...STRENGTH8 \n