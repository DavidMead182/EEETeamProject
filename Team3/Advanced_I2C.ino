#include "ICM20948.h"
#include <MadgwickAHRS.h>

ICM20948 IMU(Wire, 0x69); // an ICM20948 object with the ICM-20948 sensor on I2C bus 0 with address 0x69
int status;

bool dataAvailable = false;
int dataTime = 0;
int lastDataTime = 0;
int runCount = 1;
float MagX;
float MagY;
float MagZ;
float MagXAvg = 0;
float MagYAvg = 0;
float MagZAvg = 0;
#define sampleSize 10000 //Number of data points used to find the average


Madgwick filter;
float accelScale, gyroScale;
unsigned long microsPerReading, microsPrevious;

void setup() {
  // serial to display data
  Serial.begin(115200);
  while(!Serial) {}

  // start communication with IMU 
  status = IMU.begin();
  Serial.print("status = ");
  Serial.println(status);
  if (status < 0) {
    Serial.println("IMU initialization unsuccessful");
    Serial.println("Check IMU wiring or try cycling power");
    Serial.print("Status: ");
    Serial.println(status);
    while(1) {}
   }
  IMU.configAccel(ICM20948::ACCEL_RANGE_16G, ICM20948::ACCEL_DLPF_BANDWIDTH_50HZ);
  IMU.configGyro(ICM20948::GYRO_RANGE_2000DPS, ICM20948::GYRO_DLPF_BANDWIDTH_51HZ);
  IMU.setGyroSrd(113); // Output data rate is 1125/(1 + srd) Hz
  IMU.setAccelSrd(113);
  IMU.enableDataReadyInterrupt();

  filter.begin(5);
  microsPerReading = 1000000 / 5;
  microsPrevious = micros();
  
}

int aix, aiy, aiz;
int gix, giy, giz;
float ax, ay, az;
float gx, gy, gz;
float roll, pitch, heading;

float convertRawAcceleration(int aRaw) {
  // since we are using 2G range
  // -2g maps to a raw value of -32768
  // +2g maps to a raw value of 32767
  
  float a = (aRaw * 2.0) / 32768.0;
  return a;
}

float convertRawGyro(int gRaw) {
  // since we are using 250 degrees/seconds range
  // -250 maps to a raw value of -32768
  // +250 maps to a raw value of 32767
  
  float g = (gRaw * 250.0) / 32768.0;
  return g;
}

void loop() {
  
  
  dataTime = micros();
  dataAvailable = true;
  if (dataAvailable) {
    dataAvailable = false;
    int timeDiff = dataTime - lastDataTime;
    lastDataTime = dataTime;
    IMU.readSensor();
    if (runCount == 0){
      Serial.print("Calculating average readings... \n");
      
      for (int i = 0; i < sampleSize; i++){
        MagX = (IMU.getMagX_uT());
        MagY = (IMU.getMagY_uT());
        MagZ = (IMU.getMagZ_uT());
        MagXAvg = (MagX + MagXAvg) / 2;
        MagYAvg = (MagY + MagYAvg) / 2;
        MagZAvg = (MagZ + MagZAvg) / 2;      
      }
      Serial.print("\n=====================================\n");
      Serial.print(MagXAvg);Serial.print(",");
      Serial.print(MagYAvg);Serial.print(",");
      Serial.print(MagZAvg);
      Serial.print("\n=====================================\n");
      runCount = 2;
    }
    else if (runCount == 1){
      MagXAvg = -9.080902882213438;
      MagYAvg = -7.232474158102767;
      MagZAvg = -53.752484899077736;
      runCount = 2; 
    }
    //display the data
    //Serial.print(dataTime);
    //Serial.print("\t");
    //Serial.print("delta t:");Serial.print(timeDiff);
    //Serial.print("\t");
    //Serial.print("Variable_1");
    //Raw data
//    Serial.print("  A_x:");Serial.print(IMU.getAccelX_mss(),6);Serial.print(",");
//    Serial.print("  A_y:");Serial.print(IMU.getAccelY_mss(),6);Serial.print(",");
//    Serial.print("  A_z:");Serial.print(IMU.getAccelZ_mss(),6);Serial.print(",");
//    Serial.print("  G_x:");Serial.print(IMU.getGyroX_rads(),6);Serial.print(",");
//    Serial.print("  G_y:");Serial.print(IMU.getGyroY_rads(),6);Serial.print(",");
//    Serial.print("  G_z:");Serial.print(IMU.getGyroZ_rads(),6);Serial.print(",");
//    Serial.print("  M_x:");Serial.print(IMU.getMagX_uT(),6);Serial.print(",");
//    Serial.print("  M_y:");Serial.print(IMU.getMagY_uT(),6);Serial.print(",");
//    Serial.print("  M_z:");Serial.print(IMU.getMagZ_uT(),6);Serial.print(",");

    //Raw data, no labels:
//    Serial.print(IMU.getAccelX_mss(),6);Serial.print(",");
//    Serial.print(IMU.getAccelY_mss(),6);Serial.print(",");
//    Serial.print(IMU.getAccelZ_mss(),6);Serial.print(",");
//    Serial.print(IMU.getGyroX_rads(),6);Serial.print(",");
//    Serial.print(IMU.getGyroY_rads(),6);Serial.print(",");
//    Serial.print(IMU.getGyroZ_rads(),6);Serial.print(",");
//    Serial.print(IMU.getMagX_uT(),6);Serial.print(",");
//    Serial.print(IMU.getMagY_uT(),6);Serial.print(",");
//    Serial.print(IMU.getMagZ_uT(),6);Serial.print(",");

      //Bias removed
//    Serial.print("A_x:");Serial.print(IMU.getAccelX_mss(),6);Serial.print(",");
//    Serial.print("  A_y:");Serial.print(IMU.getAccelY_mss(),6);Serial.print(",");
//    Serial.print("  A_z:");Serial.print(IMU.getAccelZ_mss(),6);Serial.print(",");
//    Serial.print("  G_x:");Serial.print(IMU.getGyroX_rads(),6);Serial.print(",");
//    Serial.print("  G_y:");Serial.print(IMU.getGyroY_rads(),6);Serial.print(",");
//    Serial.print("  G_z:");Serial.print(IMU.getGyroZ_rads(),6);Serial.print(",");
//    
//    Serial.print("  relM_x:");Serial.print(IMU.getMagX_uT() - MagXAvg);Serial.print(",");
//    Serial.print("  relM_y:");Serial.print(IMU.getMagY_uT() - MagYAvg);Serial.print(",");
//    Serial.print("  relM_z:");Serial.print(IMU.getMagZ_uT() - MagZAvg);Serial.print(",");
//    //Serial.println(IMU.getTemperature_C(),6);
    Serial.print("\n");

    // plot the data
//    Serial.print(dataTime);
//    Serial.print("\n");
//    Serial.print(timeDiff);
//    Serial.print("\n");
//    Serial.print(IMU.getAccelX_mss(),6);
//    Serial.print("\n");
//    Serial.print(IMU.getAccelY_mss(),6);
//    Serial.print("\n");
//    Serial.print(IMU.getAccelZ_mss(),6);
//    Serial.print("\n");
//    Serial.print(IMU.getGyroX_rads(),6);
//    Serial.print("\n");
//    Serial.print(IMU.getGyroY_rads(),6);
//    Serial.print("\n");
//    Serial.print(IMU.getGyroZ_rads(),6);
//    Serial.print("\n");
//    Serial.print(IMU.getMagX_uT(),6);
//    Serial.print("\n");
//    Serial.print(IMU.getMagY_uT(),6);
//    Serial.print("\n");
//    Serial.print(IMU.getMagZ_uT(),6);
//    Serial.print("\n");
//    Serial.println(IMU.getTemperature_C(),6);


      //Implementing Madgwick
      if (dataTime - microsPrevious >= microsPerReading) {
        aix = (IMU.getAccelX_mss());
        aiy = IMU.getAccelY_mss();
        aiz = IMU.getAccelZ_mss();
        gix = IMU.getGyroX_rads();
        giy = IMU.getGyroY_rads();
        giz = IMU.getGyroZ_rads();
        
        // convert from raw data to gravity and degrees/second units
        ax = convertRawAcceleration(aix);
        ay = convertRawAcceleration(aiy);
        az = convertRawAcceleration(aiz);
        gx = convertRawGyro(gix);
        gy = convertRawGyro(giy);
        gz = convertRawGyro(giz);
  
        
        // update the filter, which computes orientation
        filter.updateIMU(gx, gy, gz, ax, ay, az);
    
        // print the heading, pitch and roll
        roll = filter.getRoll();
        pitch = filter.getPitch();
        heading = filter.getYaw();
        //newHeading = (heading - 179.86)*
        Serial.print("Orientation: ");
        Serial.print(heading);
        Serial.print(" pitch:");
        Serial.print(pitch);
        Serial.print(" roll");
        Serial.println(roll);
    
        // increment previous time, so we keep proper pace
        microsPrevious = microsPrevious + microsPerReading;
      }

  }

}
