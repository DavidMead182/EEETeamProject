#ifndef IMU_H 
#define IMU_H

#include <Arduino.h>

#define NRST        8 
#define DATA_READY  9
#define CS          10

typedef struct {
    uint8_t     _junk_a, _junk_b;
    float16_t   x_rate, y_rate, z_rate, x_acc, y_accel, z_accel,
                temp, roll, pitch, yaw;
} imu_packet;

void imu_setup();
void imu_read_packet(imu_packet *packet);

#endif