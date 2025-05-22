#include "radar.h"
#include "SparkFun_Qwiic_XM125_Arduino_Library.h"
#include <Arduino.h>


SparkFunXM125Distance radarSensor;

bool radar_setup(uint32_t start, uint32_t end) {
    uint32_t errorStatus;

        // If begin is successful (0), then start example
    if (radarSensor.begin(SFE_XM125_I2C_ADDRESS, Wire) != 1) return false;

    // Distance Sensor Setup
    // Reset sensor configuration to reapply configuration registers
    radarSensor.setCommand(SFE_XM125_DISTANCE_RESET_MODULE);

    radarSensor.busyWait();

    // Check error and busy bits
    radarSensor.getDetectorErrorStatus(errorStatus);
    if (errorStatus != 0)
    {
        Serial.print("Detector status error: ");
        Serial.println(errorStatus);
        return false;
    }

    delay(100);

    // Set Start register
    if (radarSensor.setStart(start) != 0)
    {
        Serial.println("Distance Start Error");
        return false;
    }

    delay(100);
    // Set End register
    if (radarSensor.setEnd(end) != 0)
    {
        Serial.println("Distance End Error");
        return false;
    }
    
    delay(100);

    // Apply configuration
    if (radarSensor.setCommand(SFE_XM125_DISTANCE_APPLY_CONFIGURATION) != 0)
    {
        // Check for errors
        radarSensor.getDetectorErrorStatus(errorStatus);
        if (errorStatus != 0)
        {
            Serial.print("Detector status error: ");
            Serial.println(errorStatus);
        }

        Serial.println("Configuration application error");
        return false;
    }

    // Poll detector status until busy bit is cleared
    if (radarSensor.busyWait() != 0)
    {
        Serial.print("Busy wait error");
        return false;
    }

    // Check detector status
    radarSensor.getDetectorErrorStatus(errorStatus);
    if (errorStatus != 0)
    {
        Serial.print("Detector status error: ");
        Serial.println(errorStatus);
        return false;
    }

    return true;
}

int radar_check_errors() {
    uint32_t errorStatus;

    // Check error bits
    radarSensor.getDetectorErrorStatus(errorStatus);
    if (errorStatus != 0) {
        Serial.print("Detector status error: ");
        Serial.println(errorStatus);

        return errorStatus;
    }

    // Start detector
    if (radarSensor.setCommand(SFE_XM125_DISTANCE_START_DETECTOR) != 0) {
        Serial.println("Start detector error");
        return -1;
    }

    // Poll detector status until busy bit is cleared - CHECK ON THIS!
    if (radarSensor.busyWait() != 0) {
        Serial.println("Busy wait error");
        return -1;
    }

    // Verify that no error bits are set in the detector status register
    radarSensor.getDetectorErrorStatus(errorStatus);
    if (errorStatus != 0) {
        Serial.print("Detector status error: ");
        Serial.println(errorStatus);

        return errorStatus;
    }

    // Check MEASURE_DISTANCE_ERROR for measurement failed
    radarSensor.getMeasureDistanceError(errorStatus);
    if (errorStatus == 1) {
        Serial.println("Measure Distance Error");
        return errorStatus; 
    }

    return 0;
}

void radar_get_distances(uint32_t *distances, int nd) {
    uint32_t distance;
    
    for (int i = 0; i < nd; i++) {
        radarSensor.getPeakDistance(i, distance);
        distances[i] = distance;   
    }
}

void radar_get_strengths(int32_t *strengths, int ns) {
    uint32_t strength;
    
    for (int i = 0; i < ns; i++) {
        radarSensor.getPeakStrength(i, strength);
        strengths[i] = strength;
    }
}