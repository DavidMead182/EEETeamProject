#include <Arduino.h>
#include <arduino-timer.h>
#include <Wire.h>
#include "radar.h"
#include "imu.h"
#include "comms.h"

unsigned int prev_time;

void setup() {
    Serial.begin(115200);

    Wire.begin();

    // if (!comms_setup()) { Serial.println("comms failed"); while (true); }
    radar_setup(100, 7000);
    imu_setup();

    delay(1000);
}

int li = 0;
uint32_t seq = 0;
uint32_t min_distance = 10000;
void loop() {
    // Serial.println("Loop start");

    unsigned int timestamp = millis();

    imu_packet_t packet;
    imu_read_packet(&packet);
    if (!packet.valid) { Serial.println("invalid packet"); return; }

    if (li++ >= 20 && radar_check_errors() == 0) {
        li = 0;

        int n = 9;
        uint32_t distances[n]; 
        int32_t  strengths[n];

        radar_get_distances(distances, n);
        radar_get_strengths(strengths, n);

        min_distance = 10000;
        for (int i = 0; i < n; i++) {
            if (distances[i] < min_distance && distances[i] != 0) {
                min_distance = distances[i];
            }
        }
    }

    if (li % 5 == 0) {
        Serial.print("{ \"sequence\": ");
        Serial.print(seq++);
        Serial.print(", \"packets_lost\": ");
        Serial.print(0);
        Serial.print(", \"pitch\": ");
        Serial.print(packet.pitch);
        Serial.print(", \"roll\": ");
        Serial.print(packet.roll);
        Serial.print(", \"yaw\": ");
        Serial.print(packet.yaw);
        Serial.print(", \"distance\": ");
        Serial.print(min_distance);
        Serial.print(", \"accel_x\": ");
        Serial.print(packet.x_acc);
        Serial.print(", \"accel_y\": ");
        Serial.print(packet.y_acc);
        Serial.print(", \"accel_z\": ");
        Serial.print(packet.z_acc);
        Serial.print(", \"timestamp\": ");
        Serial.print(timestamp);
        Serial.print(" }\n");
    }

    

    /* comms_sensor_data_t comms_data;
    comms_data.pitch = packet.pitch;
    comms_data.yaw = packet.yaw;
    comms_data.roll = packet.roll;
    comms_data.accelX = packet.x_acc;
    comms_data.accelY = packet.y_acc;
    comms_data.accelZ = packet.z_acc;
    comms_data.timestamp = timestamp;
    comms_data.radarDistance = distances[0];
    if (!comms_send_data(&comms_data)) { Serial.println("Bollocks"); }  */
}


// LOGGING FORMAT:
// YAW TIMESTAMP DISTANCE0 DISTANCE1...DISTANCE8 STRENGTH0 STRENGTH1...STRENGTH8 XR YR ZR XA YA ZA T ROLL PITCH YAW \n