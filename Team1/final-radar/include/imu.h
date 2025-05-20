#ifndef IMU_H 
#define IMU_H

#include <Arduino.h>

typedef struct {
    bool valid;
    float   x_rate, y_rate, z_rate, x_acc, y_acc, z_acc,
            temp, roll, pitch, yaw;
} imu_packet;

void imu_setup();
void imu_read_packet(imu_packet *packet);

#endif