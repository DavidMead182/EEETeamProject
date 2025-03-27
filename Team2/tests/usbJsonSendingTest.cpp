#include "mbed.h"
#include <cstdio>

// Serial connection (TX, RX) - connected to ST-Link Virtual COM Port
BufferedSerial pc(USBTX, USBRX, 115200); 

// Onboard LED
DigitalOut led(LED1);

void send_json_data(float temperature, uint32_t counter, const char* status) {
    char json_buffer[128];
    
    // Create JSON string
    int written = snprintf(json_buffer, sizeof(json_buffer),
             "{\"temp\":%.2f,\"count\":%u,\"status\":\"%s\"}\r\n",
             temperature, counter, status);
    
    // Check for buffer overflow
    if (written < 0 || (size_t)written >= sizeof(json_buffer)) {
        led = 1; // Turn LED on for error
        return;
    }
    
    // Send over serial
    pc.write(json_buffer, written);
    
    // Brief LED blink on successful transmission
    led = 1;
    wait_us(50000); // 50ms
    led = 0;
}

int main() {
    // Blink LED once at startup
    led = 1;
    ThisThread::sleep_for(100ms);
    led = 0;
    
    float temp = 25.5f;
    uint32_t counter = 0;
    
    while (true) {
        send_json_data(temp, counter, "OK");
        
        // Update values
        temp += 0.1f;
        counter++;
        
        // Toggle status every 10 iterations
        if(counter % 10 == 0) {
            led = !led; // Toggle LED for status change
        }
        
        ThisThread::sleep_for(1000ms); // 1 second delay
    }
}