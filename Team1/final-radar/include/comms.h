#ifndef COMMS_H 
#define COMMS_H 

#include <Arduino.h>

typedef struct {
  float     pitch;
  float     roll;
  float     yaw;
  float     radarDistance;
  float     accelX;
  float     accelY;
  float     accelZ;
  uint64_t  timestamp;
} comms_sensor_data_t;

/**
* Initialises the comms and prints any errors. Requires Serial to have been initialised
* @returns false if setup fails, true if succeeds
*/
bool comms_setup();

/**
* Sends data packet
* @returns false if unsuccessful, true otherwise 
*/
bool comms_send_data(comms_sensor_data_t *data); 

#endif