#include "imu.h"
#include <Arduino.h>

unsigned long last_micros = 0;
bool dataReady = false;

void onDataReady() {
    dataReady = true;
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
        return;
    } else {
        data_ready = false;
    }

    // timing for operation frequency logging
    unsigned long now_micros = micros();
    unsigned long delta_micros = now_micros - last_micros;
    last_micros = now_micros;

    // enable SPI on the IMU
    digitalWrite(CS, LOW);

    // send 0x3D00s as the register and request command
    SPI.transfer(0x3D);
    SPI.transfer(0x00);

    for (uint8_t *i = 0; i < 26; i++) {
        ((uint8_t *) packet) + i = SPI.transfer(0x00); 
    }

    digitalWrite(CS, HIGH);
}