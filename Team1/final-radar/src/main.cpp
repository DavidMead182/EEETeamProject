#include <Arduino.h>
#include <arduino-timer.h>
#include "ICM_20948.h"
#include "radar.h"
#include "imu.h"

ICM_20948_I2C imu;

void log_init_error(int status) {
    switch (status) { 
    case ICM_20948_Stat_Err:
        Serial.println("error");
        break;       // A general error
    case ICM_20948_Stat_NotImpl:
        Serial.println("Not implemented");
        break; // Returned by virtual functions that are not implemented
    case ICM_20948_Stat_ParamErr:
        Serial.println("Parameter error");
        break;
    case ICM_20948_Stat_WrongID:
        Serial.println("Wrong ID");
        break;
    case ICM_20948_Stat_InvalSensor:
        Serial.println("Invalid sensor");
        break; // Tried to apply a function to a sensor that does not support it (e.g. DLPF to the temperature sensor)
    case ICM_20948_Stat_NoData:
        Serial.println("No data");
        break;
    case ICM_20948_Stat_SensorNotSupported:
        Serial.println("Sensor not supported");
        break;
    case ICM_20948_Stat_DMPNotSupported:
        Serial.println("DMP not supported");
        break;    // DMP not supported (no #define ICM_20948_USE_DMP)
    case ICM_20948_Stat_DMPVerifyFail:
        Serial.println("DMP failed verify");
        break;      // DMP was written but did not verify correctly
    case ICM_20948_Stat_FIFONoDataAvail:
        Serial.println("No FIFO data");
        break;    // FIFO contains no data
    case ICM_20948_Stat_FIFOIncompleteData:
        Serial.println("Incomplete FIFO data");
        break;  // FIFO contained incomplete data
    case ICM_20948_Stat_FIFOMoreDataAvail:
        Serial.println("More FIFO data avail");
        break;  // FIFO contains more data
    case ICM_20948_Stat_UnrecognisedDMPHeader:
        Serial.println("Unrecognised DMP header");
        break;
    case ICM_20948_Stat_UnrecognisedDMPHeader2:
        Serial.println("Unrecognised DMP header");
        break;
    case ICM_20948_Stat_InvalDMPRegister:
        Serial.println("Invalid DMP register");
        break;
    default:
        Serial.print("Unknown error: ");
        Serial.println(status);
    } 
}


void setup() {
    Serial.begin(921600);
    Serial.println("XM125 Example 9: Basic Advanced Settings");

    Wire.begin();

    radar_setup(20, 7000);

    imu_setup();

    /* int attempts = 0;
    do {
        delay(500);
        imu.begin(Wire, 1);
        log_init_error(imu.status);
        attempts++;
    } while (imu.status != ICM_20948_Stat_Ok && attempts <= 4);

    if (attempts > 4) {
        Serial.println("4 failed attempts, giving up on IMU.");
    } */


    delay(1000);
}

void loop() {
    /* Serial.println("START OF LOOP");
    radar_check_errors();

    // Read PeakX Distance and PeakX Strength registers for the number of distances detected
    uint64_t timestamp = millis();
    imu.getAGMT();
    float magX = imu.magX();
    float magY = imu.magY();
    float magZ = imu.magZ();
    Serial.print(magX);
    Serial.print(",");
    Serial.print(magY);
    Serial.print(",");
    Serial.print(magZ);
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

        if (i != n-1) Serial.print(",");
    }
    Serial.print("\n");

    Serial.println("GOT RADAR");
    Serial.flush(); */

    imu_packet packet;
    imu_read_packet(&packet);
    if (!packet.valid) { return; }

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
}


// LOGGING FORMAT:
// MAGX,MAGY,MAGZ,TIMESTAMP,DISTANCE0,DISTANCE1...DISTANCE8,STRENGTH0,STRENGTH1...STRENGTH8 \n