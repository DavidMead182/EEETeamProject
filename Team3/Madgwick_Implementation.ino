

#include <MadgwickAHRS.h>
#include "ICM20948.h"
Madgwick filter;
unsigned long microsPerReading, microsPrevious;
float accelScale, gyroScale;

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

  // start the IMU and filter
  filter.begin(25);

  // initialize variables to pace updates to correct rate
  microsPerReading = 1000000 / 25;
  microsPrevious = micros();

  
}

void loop() {
  dataTime = micros();
  dataAvailable = true;
  if (dataAvailable) {
    dataAvailable = false;
    int timeDiff = dataTime - lastDataTime;
    lastDataTime = dataTime;
    IMU.readSensor();
    int aix, aiy, aiz;
    int gix, giy, giz;
    float ax, ay, az;
    float gx, gy, gz;
    float roll, pitch, heading;
    unsigned long microsNow;
  
    // check if it's time to read data and update the filter
    microsNow = micros();
    if (microsNow - microsPrevious >= microsPerReading) {
  
      // read raw data from CurieIMU
      //CurieIMU.readMotionSensor(aix, aiy, aiz, gix, giy, giz);
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
      Serial.print("Orientation: ");
      Serial.print(heading);
      Serial.print(" ");
      Serial.print(pitch);
      Serial.print(" ");
      Serial.println(roll);
  
      // increment previous time, so we keep proper pace
      microsPrevious = microsPrevious + microsPerReading;
    }
  }
}

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
