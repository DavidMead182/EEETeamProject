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
    // comms_setup();

    delay(1000);
}

void loop() {
    // Serial.println("isudhfisudf");

    radar_check_errors();

    uint64_t timestamp = millis();

    imu_packet_t packet;
    imu_read_packet(&packet);
    if (!packet.valid) { Serial.println("invalid packet"); return; }

    Serial.print(packet.yaw);
    Serial.print("\t");
    Serial.print(timestamp);
    Serial.print("\t");

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
        
        Serial.print("\t");
    }

    for (int i = 0; i < n; i++) {
        Serial.print(strengths[i]);

        if (i != n-1) { Serial.print("\t"); }
    }

    Serial.print(packet.x_rate);
    Serial.print("\t"); 
    Serial.print(packet.y_rate);
    Serial.print("\t"); 
    Serial.print(packet.z_rate);
    Serial.print("\t"); 
    Serial.print(packet.x_acc);
    Serial.print("\t"); 
    Serial.print(packet.y_acc); 
    Serial.print("\t"); 
    Serial.print(packet.z_acc);
    Serial.print("\t"); 
    Serial.print(packet.temp);
    Serial.print("\t"); 
    Serial.print(packet.roll);
    Serial.print("\t"); 
    Serial.print(packet.pitch);
    Serial.print("\t"); 
    Serial.print(packet.yaw);
    Serial.print("\n"); 

    /* comms_sensor_data_t comms_data;
    comms_data.pitch = packet.pitch;
    comms_data.yaw = packet.yaw;
    comms_data.roll = packet.roll;
    comms_data.accelX = packet.x_acc;
    comms_data.accelY = packet.y_acc;
    comms_data.accelZ = packet.z_acc;
    comms_data.timestamp = timestamp;
    comms_data.radarDistance = distances[0];
    comms_send_data(&comms_data); */
}


// LOGGING FORMAT:
// YAW TIMESTAMP DISTANCE0 DISTANCE1...DISTANCE8 STRENGTH0 STRENGTH1...STRENGTH8 XR YR ZR XA YA ZA T ROLL PITCH YAW \n