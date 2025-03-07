# Team 4

## Data Format

Transmitter format: P:{pitch},R:{roll},Y:{yaw},D:{distance},T:{timestamp}
JSON format: {"pitch":value, "roll":value, "yaw":value, "distance":value, "timestamp":value}
Processed data: other data formats etc, cardinal directions derived from yaw angles

## Chunking Protocol

First half-byte: Chunk ID (0-F hex)
Second half-byte: Sequence number for basic continuity checking
Second byte: Total number of chunks expected
Remainder: Chunk data
Maximum 16 chunks per message

## File Logging

Raw JSON data: logs/raw_data_[timestamp].json
Processed data: logs/processed_data_[timestamp].txt
Debug information: logs/debug_[timestamp].log


Board Connection Guide:
RFM69 Pin | Arduino Uno Pin
--- | ---
VCC	| 3.3V  (⚠ DO NOT use 5V)
GND |	GND
SCK |	D13 (SPI Clock)
MISO |	D12 (SPI MISO)
MOSI |	D11 (SPI MOSI)
CS |	D10
INT (G0) |	D2
RST |	D9
