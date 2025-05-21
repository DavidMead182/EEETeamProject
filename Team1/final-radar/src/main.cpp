#include <Arduino.h>
#include <arduino-timer.h>
#include <Wire.h>
#include "radar.h"
#include "imu.h"
#include "comms.h"

void print_data(int32_t *strengths) {

}

void setup() {
    Serial.begin(921600);

    Wire.begin();

    radar_setup(100, 7000);

    imu_setup();

    delay(1000);
}

void loop() {
    radar_check_errors();

    uint64_t timestamp = millis();

    imu_packet_t packet;
    imu_read_packet(&packet);
    if (!packet.valid) { return; }

    Serial.print(packet.yaw);
    Serial.print(",");
    Serial.print(timestamp);
    Serial.print(",");

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

        if (i != n-1) { Serial.print(","); }
    }

    Serial.print("\n"); 
}


// LOGGING FORMAT:
// MAGX,MAGY,MAGZ,TIMESTAMP,DISTANCE0,DISTANCE1...DISTANCE8,STRENGTH0,STRENGTH1...STRENGTH8 \n