#include "imu.h"
#include <Arduino.h>
#include <SPI.h>

#define NRST        8 
#define DATA_READY  9
#define CS          10
#define PACKET_SIZE 26

unsigned long last_micros = 0;
bool data_ready = false;

void onDataReady() {
    data_ready = true;
}

void query_imu(uint8_t *buf) {
    // enable SPI on the IMU
    digitalWrite(CS, LOW);

    // send 0x3D00s as the register and request command
    SPI.transfer(0x3D);
    SPI.transfer(0x00);

    for (int i = 0; i < PACKET_SIZE; i++) {
        buf[i] = SPI.transfer(0x00);
    }

    digitalWrite(CS, HIGH);
}

void imu_setup() {
    pinMode(NRST, OUTPUT); //puts IMU in reset mode
    digitalWrite(NRST, LOW);
    delay(100);

    pinMode(DATA_READY, INPUT_PULLUP);  // Defines dataready pin as input with pullup

    pinMode(CS, OUTPUT);
    digitalWrite(CS, HIGH);  // CS high to disable SPI on IMU

    digitalWrite(NRST, HIGH);  // pull reset high to stop resetting 
    delay(1000);  // Let IMU boot

    SPI.begin();
    SPI.beginTransaction(SPISettings(1000000, MSBFIRST, SPI_MODE3)); //1Mhz, MSB first

    // interupt on the rsing edge of the DATA_Ready Pin
    attachInterrupt(digitalPinToInterrupt(DATA_READY), onDataReady, RISING);

    Serial.println("Setup complete.");

}

void imu_read_packet(imu_packet *packet) { 
    if (!data_ready) {
        packet->valid = false;
        return;
    } else {
        data_ready = false;
    }

    // timing for operation frequency logging
    unsigned long now_micros = micros();
    unsigned long delta_micros = now_micros - last_micros;
    last_micros = now_micros;

    /* uint8_t buf[PACKET_SIZE];
    query_imu(buf);

    int16_t *values = (int16_t *) &buf; */

    digitalWrite(CS, LOW);

    // send 0x3D00s as the register and request command
    SPI.transfer(0x3D);
    SPI.transfer(0x00);

    // Read 26 bytes: 2 junk + 24 actual (12 x int16_t)
    uint8_t rawData[26];
    for (int i = 0; i < 26; i++) {
        rawData[i] = SPI.transfer(0x00);
    }

    digitalWrite(CS, HIGH); // disable SPI on IMU

    // Skip first 2 junk bytes
    int16_t values[12];
    for (int i = 0; i < 12; i++) {
        int index = 2 + i * 2;
        values[i] = (int16_t)((rawData[index] << 8) | rawData[index + 1]);  // MSB first
    }

    packet->x_rate = values[0] / 64.0;
    packet->y_rate = values[1] / 64.0;
    packet->z_rate = values[2] / 64.0;
    packet->x_acc  = values[3] / 4000.0;
    packet->y_acc  = values[4] / 4000.0;
    packet->z_acc  = values[5] / 4000.0;
    packet->temp   = values[6]  * 0.073111172849435 + 31.0;
    packet->roll   = values[7]  * (2 * PI / 65536.0);
    packet->pitch  = values[8]  * (2 * PI / 65536.0);
    packet->yaw    = values[9]  * (2 * PI / 65536.0);

    packet->valid = true;

    /* packet->x_rate = values[1] / 64.0;
    packet->y_rate = values[2] / 64.0;
    packet->z_rate = values[3] / 64.0;
    packet->x_acc  = values[4] / 4000.0;
    packet->y_acc  = values[5] / 4000.0;
    packet->z_acc  = values[6] / 4000.0;
    packet->temp   = values[7]  * 0.073111172849435 + 31.0;
    packet->roll   = values[8]  * (2 * PI / 65536.0);
    packet->pitch  = values[9]  * (2 * PI / 65536.0);
    packet->yaw    = values[10] * (2 * PI / 65536.0); */
}