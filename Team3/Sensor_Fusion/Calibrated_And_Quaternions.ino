#include "ICM20948.h"

//Arduino pins:
//A4 is Data
//A5 is Clock

ICM20948 IMU(Wire, 0x69); // an ICM20948 object with the ICM-20948 sensor on I2C bus 0 with address 0x69
int status;

bool dataAvailable = false;
int dataTime = 0;
int lastDataTime = 0;
float MagX;
float MagY;
float MagZ;

float GyroX;
float GyroY;
float GyroZ;

float AccX;
float AccY;
float AccZ;

float AccAvg, GyroAvg, MagAvg;
float AccNX, AccNY, AccNZ;
float GyroNX, GyroNY, GyroNZ;
float MagNX, MagNY, MagNZ;

float biasRemoved[3] = {0, 0, 0};
float ABias[3] = {-0.28071, -0.10724, 0.39683};
float GBias[3] = {-0.00993, 0.01845, 0.00263};
float Corrected [3];
#define sampleSize 10000 //Number of data points used to find the average

//Quaternion for acc
float q_acc[4];

//Quaternion for gyro
float q_gyro[4];
//sin and cosines of values
float sG_x;
float cG_x;
float sG_y;
float cG_y;
float sG_z;
float cG_z;

//Quaternion for mag
float q_mag[4] = {0, 0, 0, 0};
float Gamma;


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
  IMU.setGyroSrd(10.2); // Output data rate is 1125/(1 + srd) Hz
  IMU.setAccelSrd(10.2); //113
  IMU.enableDataReadyInterrupt();
  
}

float A[3][3] = {
  { 1.121767, 0.013784, 0.002288},
  { 0.013784, 1.041197,  0.013531},
  {0.002288, 0.013531,  1.088577}};

//==================================
//  Average values
//==================================
float b[3] = {-3.601709, -12.836361, -30.010240};

float correctedMag[3][3];


//==================================
//  Main
//==================================
void loop() {
  
  dataTime = micros();
  dataAvailable = true;
  if (dataAvailable) {
    dataAvailable = false;
    int timeDiff = dataTime - lastDataTime;
    lastDataTime = dataTime;
    IMU.readSensor();

    //Reading the data
    float MagVal [3] = {IMU.getMagX_uT(), IMU.getMagY_uT(), IMU.getMagZ_uT()};
    float AVal [3] = {IMU.getAccelX_mss(), IMU.getAccelY_mss(), IMU.getAccelZ_mss()};
    float GVal [3] = {IMU.getGyroX_rads() ,IMU.getGyroY_rads(), IMU.getGyroZ_rads()};

    //==============================================================
    //      Matrix multiplication
    //==============================================================
    // [13][5]  13 would be the number of rows, 5 would be the number of columns

    for (int i=0;i<=2;i++){
      biasRemoved[i] = MagVal[i] - b[i];
      for (int j=0;j<=2;j++){
        correctedMag[j][i] = A[j][i] * biasRemoved[i];
      }
    }
    MagX = 0;
    MagY = 0;
    MagZ = 0;
    for (int i=0;i<=2;i++){
      MagX = MagX + correctedMag[0][i];
      MagY = MagY + correctedMag[1][i];
      MagZ = MagZ + correctedMag[2][i];

    }

    //==============================================================
    //     Displaying calibrated readings 
    //==============================================================

    AccX = AVal[0] - ABias[0];
    AccY = AVal[1] - ABias[1];
    AccZ = AVal[2] - ABias[2];

    GyroX = GVal[0] - GBias[0];
    GyroY = GVal[1] - GBias[1];
    GyroZ = GVal[2] - GBias[2];

    Serial.print(AccX,6);Serial.print(",");
    Serial.print(AccY,6);Serial.print(",");
    Serial.print(AccZ,6);Serial.print(",");
    Serial.print(GyroX,6);Serial.print(",");
    Serial.print(GyroY,6);Serial.print(",");
    Serial.print(GyroZ,6);Serial.print(",");

    //Serial.print("MagX: ");
    Serial.print(MagX);Serial.print(",");
    //Serial.print("MagY: ");
    Serial.print(MagY);Serial.print(",");
    //Serial.print("MagZ: ");
    Serial.print(MagZ);Serial.print(",");
    Serial.print("\n");

    // ================================================================ //
    //                    Accelerometer Quaternion
    // ================================================================ //
    //Finding average of the acceleration values to normalise them.
    AccAvg = sqrt((AccX*AccX) + (AccY*AccY) + (AccZ*AccZ));
    AccNX = AccX/AccAvg;
    AccNY = AccY/AccAvg;
    AccNZ = AccZ/AccAvg;

    if (AccZ >= 0){
      q_acc[0] = - sqrt((AccNX + 1) / 2);
      q_acc[1] = - (AccNY) / sqrt(2 * (1 + AccNZ));
      q_acc[2] = (AccNZ) / sqrt(2 * (1 + AccNZ));
      q_acc[3] = 0;
    }
    else{
      q_acc[0] = - (AccNY) / sqrt(2 * (1 - AccNZ));
      q_acc[1] = sqrt((1 - AccNZ) / 2);
      q_acc[2] = 0;
      q_acc[3] = (AccNZ) / sqrt(2 * (1 - AccNZ));
    }

    // ============================================================ //
    //                      Gyroscope Quaternion
    // ============================================================ //
    //Finding average of the gyroscope values to normalise them
    GyroAvg = sqrt((GyroX*GyroX) + (GyroY*GyroY) + (GyroZ*GyroZ));
    GyroNX = GyroX/GyroAvg;
    GyroNY = GyroY/GyroAvg;
    GyroNZ = GyroZ/GyroAvg;

    sG_x = sin(GyroNX)/2;
    cG_x = cos(GyroNX)/2;
    sG_y = sin(GyroNY)/2;
    cG_y = cos(GyroNY)/2;
    sG_z = sin(GyroNZ)/2;
    cG_z = cos(GyroNZ)/2;
    
    q_gyro[0] = cG_x * cG_y * cG_z + sG_x * sG_y * sG_z;
    q_gyro[1] = sG_x * cG_y * cG_z - cG_x * sG_y * sG_z;
    q_gyro[2] = cG_x * sG_y * cG_z + sG_x * cG_y * sG_z;
    q_gyro[3] = cG_x * cG_y * sG_z - sG_x * sG_y * cG_z;

    // ============================================================ //
    //                  Magnetometer Quaternion
    // ============================================================ //
    //Finding average of the gyroscope values to normalise them
    MagAvg = sqrt((MagX*MagX) + (MagY*MagY) + (GyroZ*GyroZ));
    MagNX = MagX/MagAvg;
    MagNY = MagY/MagAvg;
    MagNZ = MagZ/MagAvg;

    // As q1 and q2 are always 0, do not need to update them
    Gamma = (MagNX * MagNX) + (MagNY * MagNY);

    if (MagX >= 0){
      q_mag[0] = sqrt(Gamma + MagNX*sqrt(Gamma)) / sqrt(2*Gamma);
      q_mag[3] = MagNY / sqrt(2 * (Gamma + MagNX*sqrt(Gamma)));
    }
    else{
      q_mag[0] = MagNY / sqrt(2 * (Gamma - MagNX*sqrt(Gamma)));
      q_mag[3] = sqrt(Gamma - MagNX*sqrt(Gamma)) / sqrt(2*Gamma);
    }
  }
}

