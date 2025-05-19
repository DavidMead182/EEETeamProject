#include "ICM20948.h"
#include <MadgwickAHRS.h>
#define pi 3.141 

Madgwick filter;
unsigned long microsPerReading, microsPrevious;
float accelScale, gyroScale;

ICM20948 IMU(Wire, 0x69); // an ICM20948 object with the ICM-20948 sensor on I2C bus 0 with address 0x69
int status;
const int InButton = 7;   // Pin which is the input to set whether the device is indoors or outdoors.
bool In = 0;              //Initialising the location area. 0 = outside, 1 = inside, 2 = undefined.
float magDec = 4.0;       //The magnetic declination

bool dataAvailable = false;
int dataTime = 0;
int lastDataTime = 0;

//Calibrated value variables initiation
float MagX;
float MagY;
float MagZ;

float GyroX;
float GyroY;
float GyroZ;

float AccX;
float AccY;
float AccZ;

//Madgwick variable initiation
float ax, ay, az;
float gx, gy, gz;
float roll, pitch, heading, yaw_mag;

//Variables to store the sine and cosine of angles
float lsa, lso, lsn, lca, lco, lcn;
float gax, gay, gaz;
float x = 0;
float y = 0;
float z = 0;

float Vx = 0;
float Vy = 0;
float Vz = 0;

unsigned long microsNow;

float biasRemoved[3] = {0, 0, 0};
float ABias[3] = {-0.28071, -0.10724, 0.39683};
float GBias[3] = {-0.00993, 0.01845, 0.00263};

void setup() {
 // serial to display data
  Serial.begin(115200);
  pinMode(InButton, INPUT);
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
  IMU.configAccel(ICM20948::ACCEL_RANGE_4G, ICM20948::ACCEL_DLPF_BANDWIDTH_50HZ);
  IMU.configGyro(ICM20948::GYRO_RANGE_250DPS, ICM20948::GYRO_DLPF_BANDWIDTH_51HZ);
  IMU.setGyroSrd(113); // Output data rate is 1125/(1 + srd) Hz
  IMU.setAccelSrd(113);
  IMU.enableDataReadyInterrupt();

  // start the IMU and filter
  filter.begin(25);

  // initialize variables to pace updates to correct rate
  microsPerReading = 100000 / 25;   //4 milliseconds
  microsPrevious = micros();
}

float convertRawAcceleration(int aRaw) {
  // since we are using 4G range
  // -4g maps to a raw value of -32768
  // +4g maps to a raw value of 32767
  
  float a = (aRaw * 4.0) / 32768.0;
  return a;
}

float convertRawGyro(int gRaw) {
  // since we are using 250 degrees/seconds range
  // -250 maps to a raw value of -32768
  // +250 maps to a raw value of 32767
  
  float g = (gRaw * 250.0) / 32768.0;
  return g;
}

float integrate(float x0, float dx, float dt){
  float x = x0 + dx*dt;
  return x;
}

float A_out[3][3] = {
  { 1.178953,  0.010998, -0.012205},
  { 0.010998,  1.104743,  0.023494},
  {-0.012205,  0.023494,  1.146978}};

float b_out[3] = {-5.243977, -11.492618, -32.648746};

float A_in[3][3] = {
  { 1.121767, 0.013784, 0.002288},
  { 0.013784, 1.041197,  0.013531},
  {0.002288, 0.013531,  1.088577}};

//==================================
//  Average values
//==================================
float b_in[3] = {-3.601709, -12.836361, -30.010240};

float A[3][3];
float b[3];

float correctedMag[3][3];
float dt = 0.004;

void loop() {
  dataTime = micros();
  dataAvailable = true;
  if (dataAvailable) {
    dataAvailable = false;
    int timeDiff = dataTime - lastDataTime;
    lastDataTime = dataTime;
    IMU.readSensor();
  
    // check if it's time to read data and update the filter
    microsNow = micros();
    if (microsNow - microsPrevious >= microsPerReading) {
      //==============================================================
      //      Checking if the device is inside or out
      //      and setting the calibrating coefficients
      //      dependending on the state
      //==============================================================
      if (In != digitalRead(InButton)){
        if (0 == digitalRead(InButton)){
          for (int i; i<3;i++){
            for (int j; j<3; i++){
              A[i][j] = A_out[i][j];
            }
            b[i] = b_out[i];
          }
        }
        else{
          for (int i; i<3;i++){
            for (int j; j<3; i++){
              A[i][j] = A_in[i][j];
            }
            b[i] = b_in[i];
          }
        }
      }

      float A[3][3] = {
      { 1.121767, 0.013784, 0.002288},
      { 0.013784, 1.041197,  0.013531},
      {0.002288, 0.013531,  1.088577 }};

      float b[3] = {-3.601709, -12.836361, -30.010240};

      //Reading the data
      float MagVal [3] = {IMU.getMagX_uT(), IMU.getMagY_uT(), IMU.getMagZ_uT()};
      float AVal [3] = {IMU.getAccelX_mss(), IMU.getAccelY_mss(), IMU.getAccelZ_mss()};
      float GVal [3] = {IMU.getGyroX_rads() ,IMU.getGyroY_rads(), IMU.getGyroZ_rads()};

      //==============================================================
      //      Calibratinig magnetometer data
      //==============================================================
      // [13][5]  13 would be the number of rows, 5 would be the number of columns

      for (int i=0;i<=2;i++){
        biasRemoved[i] = MagVal[i] - b[i];
        for (int j=0;j<=2;j++){
          correctedMag[i][j] = A[j][i] * biasRemoved[i];
        }
      }


      MagX = correctedMag[0][0] + correctedMag[0][1] + correctedMag[0][2];
      MagY = correctedMag[1][0] + correctedMag[1][1] + correctedMag[1][2];
      MagZ = correctedMag[2][0] + correctedMag[2][1] + correctedMag[2][2];

      //==============================================================
      //     Calibrating accelerometer and gyroscope data 
      //==============================================================

      AccX = AVal[0] - ABias[0];
      AccY = AVal[1] - ABias[1];
      AccZ = AVal[2] - ABias[2];

      GyroX = GVal[0] - GBias[0];
      GyroY = GVal[1] - GBias[1];
      GyroZ = GVal[2] - GBias[2]; 

      // Serial.print(AccX);Serial.print("  ");
      // Serial.print(AccY);Serial.print("  ");
      // Serial.print(AccZ);Serial.print("  ");
      // Serial.print(GyroX);Serial.print("  ");
      // Serial.print(GyroY);Serial.print("  ");
      // Serial.print(GyroZ);Serial.print("  ");
      // Serial.print(MagX);Serial.print("  ");
      // Serial.print(MagY);Serial.print("  ");
      // Serial.print(MagZ);Serial.print("  ");
      // Serial.print("\n");Serial.print("  ");

      //==============================================================
      //     Sensor fusion 
      //==============================================================
  
      // convert from raw data to gravity and degrees/second units
      ax = convertRawAcceleration(AccX);
      ay = convertRawAcceleration(AccY);
      az = convertRawAcceleration(AccZ);
      gx = convertRawGyro(GyroX);
      gy = convertRawGyro(GyroY);
      gz = convertRawGyro(GyroZ);
  
      // update the filter, which computes orientation
      filter.updateIMU(gx, gy, gz, ax, ay, az);
  
      // print the heading, pitch and roll
      roll = filter.getRoll();
      pitch = filter.getPitch();
      heading = filter.getYaw();
      yaw_mag = atan2(MagY,MagX)*180/pi - magDec;
      Serial.print("Ori: ");
      Serial.print(pitch);
      Serial.print("   ");
      Serial.print(roll);
      Serial.print("   ");
      Serial.print(yaw_mag);

      //==============================================================
      //     Must add complimentary filter to find the most
      //     accurate yaw using gyro and magnetometer
      //     estimates. 
      //==============================================================  

      //==============================================================
      //     Converting local acceleration into global 
      //==============================================================
      lsn = sin(radians(roll));
      lcn = cos(radians(roll));
      lso = sin(radians(pitch));
      lco = cos(radians(pitch));
      lsa = sin(radians(yaw_mag));
      lca = cos(radians(yaw_mag));

      gax = lco*lca*AccX + (-lsa*lcn + lca*lso*lsn)*AccY + (lsa*lsn + lca*lcn*lso)*AccZ;
      gay = (lsa*lco)*AccX + (lca*lcn + lsa*lso*lsn)*AccY + (-lsn*lca + lsa*lso*lcn)*AccZ;
      gaz = -lso*AccX + lco*lsn*AccY + lco*lcn*AccZ;

      //==============================================================
      //     Displayig global acceleration 
      //==============================================================
      Serial.print(" |  Glob acc: ");
      Serial.print(gax);
      Serial.print("   ");
      Serial.print(gay);
      Serial.print("   ");
      Serial.print(gaz);

      //Removing the acceleration due
      gaz -= 9.81;

      //Integrating acceleration twice to find the displacement
      Vx = integrate(Vx, gax, dt);
      Vy = integrate(Vy, gay, dt);
      Vz = integrate(Vz, gaz, dt);

      x = integrate(x, Vx, dt);
      y = integrate(y, Vz, dt);
      z = integrate(z, Vy, dt);

      //==============================================================
      //     Displaying global acceleration with gravity removed
      //==============================================================
      Serial.print(" |  Glob acc: ");
      Serial.print(gax);
      Serial.print("   ");
      Serial.print(gay);
      Serial.print("   ");
      Serial.print(gaz);

      //==============================================================
      //     Displaying global velocity
      //==============================================================
      Serial.print(" |  Glob vel: ");
      Serial.print(Vx,2);
      Serial.print("   ");
      Serial.print(Vy,2);
      Serial.print("   ");
      Serial.print(Vz,2);

      //==============================================================
      //     Displaying global displacemet
      //==============================================================
      Serial.print(" |  Glob pos: ");
      Serial.print(x,3);
      Serial.print("   ");
      Serial.print(y,3);
      Serial.print("   ");
      Serial.println(z,3);
  
      // increment previous time, so we keep proper pace
      microsPrevious = microsPrevious + microsPerReading;
    }
  }
}

