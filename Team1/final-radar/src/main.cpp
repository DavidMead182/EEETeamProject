/*
  Example 9: Distance Advanced Settings

  Using the Acconeer XM125 A121 60GHz Pulsed Coherent Radar Sensor.

  This example shows how operate the XM125 when the device is in Distance Reading Mode.
  The sensor is initialized, then the distance values will print out to the terminal in
  mm.

  By: Madison Chodikov
  SparkFun Electronics
  Date: 2024/1/22
  SparkFun code, firmware, and software is released under the MIT License.
    Please see LICENSE.md for further details.

  Hardware Connections:
  QWIIC --> QWIIC

  Serial.print it out at 115200 baud to serial monitor.

  Feel like supporting our work? Buy a board from SparkFun!
  https://www.sparkfun.com/products/ - Qwiic XM125 Breakout
*/
#include "SparkFun_Qwiic_XM125_Arduino_Library.h"
#include <Arduino.h>
#include <arduino-timer.h>
#include "ICM_20948.h"

SparkFunXM125Distance radarSensor;
ICM_20948_I2C imu;

// I2C default address
uint8_t i2cAddress = SFE_XM125_I2C_ADDRESS;

// Setup Variables
uint32_t startVal = 0;
uint32_t endVal = 0;
uint32_t numDistances = 9;
uint32_t calibrateNeeded = 0;
uint32_t measDistErr = 0;
uint32_t beginReading = 800;
uint32_t endReading = 7000;

// Error statuses
uint32_t errorStatus = 0;

// Distance Variables
uint32_t distancePeakStrength = 0;
uint32_t distancePeak = 0;

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
    // Start serial
    Serial.begin(115200);
    Serial.println("XM125 Example 9: Basic Advanced Settings");
    // Serial.println("");

    Wire.begin();

    // If begin is successful (0), then start example
    if (radarSensor.begin(i2cAddress, Wire) == 1)
    {
        // Serial.println("Begin");
    }
    else // Otherwise, infinite loop
    {
        Serial.println("Device failed to setup - Freezing code.");
        while (1)
            ; // Runs forever
    }

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
    }

    delay(100);

    // Set Start register
    if (radarSensor.setStart(beginReading) != 0)
    {
        Serial.println("Distance Start Error");
    }
    radarSensor.getStart(startVal);
    // Serial.print("Start Val: ");
    // Serial.println(startVal);

    delay(100);
    // Set End register
    if (radarSensor.setEnd(endReading) != 0)
    {
        Serial.println("Distance End Error");
    }
    radarSensor.getEnd(endVal);
    // Serial.print("End Val: ");
    // Serial.println(endVal);
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
    }

    // Poll detector status until busy bit is cleared
    if (radarSensor.busyWait() != 0)
    {
        Serial.print("Busy wait error");
    }

    // Check detector status
    radarSensor.getDetectorErrorStatus(errorStatus);
    if (errorStatus != 0)
    {
        Serial.print("Detector status error: ");
        Serial.println(errorStatus);
    }

    do {
        delay(500);
        imu.begin(Wire, 1);
        log_init_error(imu.status);
    } while (imu.status != ICM_20948_Stat_Ok);


    delay(1000);
}

// Handy helpful output function

void outputResults(uint sample, uint32_t distance, uint32_t strength, uint64_t timestamp, float magX, float magY, float magZ) {
    if (distance == 0)
        return;

    Serial.print(sample);
    Serial.print(",");
    Serial.print(distance);
    Serial.print(",");
    Serial.print(strength);
    Serial.print(",");
    Serial.print(i2cAddress);
    Serial.print(",");
    Serial.print(magX);
    Serial.print(",");
    Serial.print(magY);
    Serial.print(",");
    Serial.print(magZ);
    Serial.print(",");
    Serial.print(timestamp);

    Serial.println();
}

void loop() {
    // Check error bits
    radarSensor.getDetectorErrorStatus(errorStatus);
    if (errorStatus != 0)
    {
        Serial.print("Detector status error: ");
        Serial.println(errorStatus);
    }

    // Start detector
    if (radarSensor.setCommand(SFE_XM125_DISTANCE_START_DETECTOR) != 0)
    {
        Serial.println("Start detector error");
    }

    // Poll detector status until busy bit is cleared - CHECK ON THIS!
    if (radarSensor.busyWait() != 0)
    {
        Serial.println("Busy wait error");
    }

    // Verify that no error bits are set in the detector status register
    radarSensor.getDetectorErrorStatus(errorStatus);
    if (errorStatus != 0)
    {
        Serial.print("Detector status error: ");
        Serial.println(errorStatus);
    }

    // Check MEASURE_DISTANCE_ERROR for measurement failed
    radarSensor.getMeasureDistanceError(measDistErr);
    if (measDistErr == 1)
    {
        Serial.println("Measure Distance Error");
    }

    // Recalibrate device if calibration error is triggered
    radarSensor.getCalibrationNeeded(calibrateNeeded);
    if (calibrateNeeded == 1)
    {
        Serial.println("Calibration Needed - Recalibrating.. ");
        // Calibrate device (write RECALIBRATE command)
        radarSensor.setCommand(SFE_XM125_DISTANCE_RECALIBRATE);
    }

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

    for (int i = 0; i < 9; i++) {
        radarSensor.getPeakDistance(i, distancePeak);
        radarSensor.getPeakStrength(i, distancePeakStrength);
        // if (distancePeakStrength > maxStrength) { maxStrength = distancePeakStrength; maxPeak = i; }
        
        if (distancePeak == 0)
            Serial.print(1E8);
        else    
            Serial.print(distancePeak);
        
        if (i != 8) Serial.print(",");
        // outputResults(i, distancePeak, UINT32_MAX - distancePeakStrength, timestamp, magX, magY, magZ);
    }
    Serial.println();
}
