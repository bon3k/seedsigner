# Wiring NES Controller + Display

## LCD → Raspberry Pi (BCM)

| LCD | Raspberry Pi (BCM)   |
|-----|--------------------  |
| VCC | 3.3V (Pin 1)         |
| GND | GND (Pin 6)          |
| DIN | MOSI GPIO10 (Pin 19) |
| CLK | SCLK GPIO11 (Pin 23) |
| CS  | CE0 GPIO8 (Pin 24)   |
| DC  | GPIO25 (Pin 22)      |
| RST | GPIO5 (Pin 29)       |
| BL  | GPIO18 (Pin 12)      |

## NES → Raspberry Pi (BCM)

| NES wire | Raspberry Pi (BCM) |
|----------|--------------------|
| WHITE    | 3.3V (Pin 17)      |
| BROWN    | GND (Pin 9)        |
| YELLOW   | GPIO17 (Pin 11)    |
| RED      | GPIO27 (Pin 13)    |
| ORANGE   | GPIO22 (Pin 15)    |
