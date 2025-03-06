//------------------------------------------------------------
//
//        Including Libraies
//
//------------------------------------------------------------

#include "ICM20948.h"
#include <MatrixMath.h>

//------------------------------------------------------------
//
//        Initialising Addresses
//
//------------------------------------------------------------

// an ICM20948 object with the ICM-20948 sensor on I2C bus 0 with address 0x69
ICM20948 IMU(Wire, 0x69);
int status;

//Arduino pins:
//A4 is Data
//A5 is Clock


//------------------------------------------------------------
//
//        Initialising variables
//
//------------------------------------------------------------

//Maximum number of values in calibration array
#define calLen 50 
//Number of milliseconds between readings to calibrate
#define calDelay 20;

//Variables assosciated with measuring time difference between readings
unsigned long microsPerReading, microsPrevious;

//Variables to measure the time between each data set
int dataTime = 0;
int lastDataTime = 0;
bool dataAvailable = false;

//Variables to store the calibrated magnetometer data
float MagX;
float MagY;
float MagZ;

//Vectors and matrices to handle calibration of 
float biasRemoved[3] = {0, 0, 0};
float correctedMag [3][3];
float b[3];
float A[3][3];

//Values which will be stored in A and b
float a11, a12, a13;
float a21, a22, a23;
float a31, a32, a33;
float b1,  b2,  b3;


//------------------------------------------------------------
//
//        Setup
//
//------------------------------------------------------------

void setup() {
  // put your setup code here, to run once:

  //PTM to begin and end the calibration
  pinMode(3, INPUT);    //Selecting pin 3 as an input
  pinMode(3, HIGH);     //Turning the pull up resistor on for pin 3

  //Matrix used to store all incoming data for calibration.
  
  // serial to display data
  Serial.begin(115200);
  while(!Serial) {}

  // start communication with IMU 
  status = IMU.begin();
  Serial.print("status = ");
  Serial.println(status);

  //Check if an error has occured with initialising the IMU
  if (status < 0) {
    Serial.println("IMU initialization unsuccessful");
    Serial.println("Check IMU wiring or try cycling power");
    Serial.print("Status: ");
    Serial.println(status);
    while(1) {}
   }

  //Initialise the IMU settings
  IMU.configAccel(ICM20948::ACCEL_RANGE_16G, ICM20948::ACCEL_DLPF_BANDWIDTH_50HZ);
  IMU.configGyro(ICM20948::GYRO_RANGE_2000DPS, ICM20948::GYRO_DLPF_BANDWIDTH_51HZ);
  IMU.setGyroSrd(113); // Output data rate is 1125/(1 + srd) Hz
  IMU.setAccelSrd(113);
  IMU.enableDataReadyInterrupt();

  
  Serial.print("Setup done \n");
  Serial.print("dd\n");
  //==============================================================
  //      Calibration
  //==============================================================
  A[0][0] = calibrate(&a12, &a13, &a21, &a22, &a23, &a31, &a32, &a33, &b1, &b2, &b3);
  A[0][1] = a12;
  A[0][2] = a13;
  A[1][0] = a21;
  A[1][1] = a22;
  A[1][2] = a23;
  A[2][0] = a31;
  A[2][1] = a32;
  A[2][2] = a33;
  b[0] = b1;
  b[1] = b2;
  b[2] = b3;
  
  //Return A and B

}

//------------------------------------------------------------
//
//        Calibration functions
//
//------------------------------------------------------------
//Arduino cannot return multiple values from one function.
//Need 9 values for A matrix and 3 for B vector = 12 total
//This means 1 value can return and 11 can be passed by reference
float calibrate(float* a12, float* a13, float* a21, float* a22, float* a23, float* a31, float* a32, float* a33, float* b1, float* b2, float* b3){
  int calibrationSwitch = digitalRead(3);   //Reading the status of pin3

  //Maximum number of values being read is currently calLen.
  float rawMag[calLen][3];
  rawMag[calLen-1][0] = {0.0};
  

  //==============================================================
  //      Saving data for calibration
  //==============================================================
  int i = 0;
  while ((calibrationSwitch != 1) and (rawMag[calLen-1][0] == 0.0)){
    dataAvailable = true;
    if (dataAvailable){
      dataAvailable = false;
      IMU.readSensor();
      //calibrationSwitch = digitalRead(3);
      //Measure values and save them.
      rawMag[i][0] = {IMU.getMagX_uT()};
      rawMag[i][1] = {IMU.getMagY_uT()};
      rawMag[i][2] = {IMU.getMagZ_uT()};
      Serial.print("rawMag x: "); Serial.print(rawMag[i][0]);Serial.print("\n");
      i++;
      
      delay(calDelay);
    }
  }
  Serial.print("Exit cal \n");

  //==============================================================
  //      Analysing the saved data
  //==============================================================
  //Creation of 'design matrix'
  mtx_type D [10][calLen];
  mtx_type DT [calLen][10];
  for (int i=0;i<calLen/10;i++){
    //Axis^2
    D[0][i] = rawMag[i][0] * rawMag[i][0];
    D[1][i] = rawMag[i][1] * rawMag[i][1];
    D[2][i] = rawMag[i][2] * rawMag[i][2];

    DT[i][0] = D[0][i];
    DT[i][1] = D[1][i];
    DT[i][2] = D[2][i];
    
    //2*axisA*axisB
    D[3][i] = 2 * rawMag[i][1] * rawMag[i][2];
    D[4][i] = 2 * rawMag[i][0] * rawMag[i][2];
    D[5][i] = 2 * rawMag[i][0] * rawMag[i][1];

    DT[i][3] = D[3][i];
    DT[i][4] = D[4][i];
    DT[i][5] = D[5][i];
    
    //2*axis
    D[6][i] = 2 * rawMag[i][0];
    D[7][i] = 2 * rawMag[i][1];
    D[8][i] = 2 * rawMag[i][2];

    DT[i][6] = D[6][i];
    DT[i][7] = D[7][i];
    DT[i][8] = D[8][i];
    
    //1
    D[9][i] = 1;
    DT[i][9] = 1;
  }
  //Creation of S matrix
  mtx_type S [10][10];
  //D * D^T = S
  Matrix.Multiply((mtx_type*)D, (mtx_type*)DT, 10, calLen, 10, (mtx_type*)S);
  delete(D);
  delete(DT);

  //Creation of S11 matrix
  mtx_type S11 [6][6];
  for (int i=0;i<6;i++){
    for (int j=0;j<6;j++){
      S11[i][j] = S[i][j];
    }
  }

  //Creation of S12 and S21 matrices
  mtx_type S12 [6][4];
  mtx_type S21 [4][6];
  for (int i=0;i<4;i++){
    for (int j=0;j<6;j++){
      S12[j][i] = S[j][i+6];
      S21[i][j] = S[i+6][j];
    }
  }

  //Creation of S22 matrix
  mtx_type S22 [6][6];
  for (int i=0;i<6;i++){
    for (int j=0;j<6;j++){
      S22[i][j] = S[i+6][j+6];
    }
  }

    
  
}


void loop() {
  // put your main code here, to run repeatedly:
  dataTime = micros();
  int timeDiff = dataTime - lastDataTime;
  lastDataTime = dataTime;
  IMU.readSensor();

  //Magnetometer  raw readings
  float MagVal [3] = {IMU.getMagX_uT(), IMU.getMagY_uT(), IMU.getMagZ_uT()};

  // [x][y]  x: number of rows, y: number of columns

  //==============================================================
  //      Matrix multiplication
  //==============================================================
  //CalVector = CalMatrix * (RawVector - BiasVector)
  for (int i=0;i<=2;i++){
    biasRemoved[i] = MagVal[i] - b[i];
    for (int j=0;j<=2;j++){
      correctedMag[j][i] = A[j][i] * biasRemoved[i];
    }
  }
  //Resetting calibrated magnetometers to 0
  MagX = 0;
  MagY = 0;
  MagZ = 0;

  //Finding the calibrated X, Y and Z values
  for (int i=0;i<=2;i++){
    MagX = MagX + correctedMag[1][i];
    MagY = MagY + correctedMag[2][i];
    MagZ = MagZ + correctedMag[3][i];

  }
  //==============================================================
  //      Displaying new corrected magnetometer readings 
  //==============================================================
  Serial.print("MagX: ");
  Serial.print(MagX);Serial.print(",");
  Serial.print("MagY: ");
  Serial.print(MagY);Serial.print(",");
  Serial.print("MagZ: ");
  Serial.print(MagZ);Serial.print(",");
  Serial.print("\n");






}
