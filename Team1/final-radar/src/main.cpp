#include <Arduino.h>
#include <arduino-timer.h>
#include <Wire.h>
#include <AceSorting.h>
#include "radar.h"
#include "imu.h"
#include "comms.h"

unsigned int prev_time;

typedef struct {
    uint32_t distance;
    int32_t  strength;
} radar_pair_t;

void setup() {
    Serial.begin(115200);

    Wire.begin();

    Serial.println("Setup...");
    // if (!comms_setup()) { Serial.println("comms failed"); while (true); }
    radar_setup(100, 7000);
    // imu_setup();

    delay(1000);
}

uint32_t min_distance = 10000;
void loop() {
    unsigned long timestamp = millis();

    if (radar_check_errors() != 0) { return; }

    Serial.print(timestamp);
    prev_time = timestamp;
    Serial.print("\t");

    int n = 9;
    uint32_t distances[n]; 
    int32_t  strengths[n];

    radar_get_distances(distances, n);
    radar_get_strengths(strengths, n);

    radar_pair_t pairs[n];
    for (int i = 0; i < n; i++) {
        pairs[i].distance = distances[i];
        pairs[i].strength = strengths[i];
    }

    ace_sorting::shellSortKnuth(pairs, n, [](radar_pair_t a, radar_pair_t b) { return a.distance < b.distance; } );

    for (int i = 0; i < n; i++) {
        Serial.print(pairs[i].distance);
        Serial.print("\t");
    }

    for (int i = 0; i < n; i++) {
        Serial.print(pairs[i].strength);
        Serial.print("\t");
    }

    Serial.print("\n");
}


// LOGGING FORMAT:
// YAW TIMESTAMP DISTANCE0 DISTANCE1...DISTANCE8 STRENGTH0 STRENGTH1...STRENGTH8 XR YR ZR XA YA ZA T ROLL PITCH YAW \n