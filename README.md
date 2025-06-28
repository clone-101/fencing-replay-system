# Fencing Replay System

This project is a light weight desktop application that can be used by fencing referees to replay/review calls in real time.

## Description

## Requirements

### Software Dependencies

to install the required dependencies run:

```bash
pip install -r requirements.txt
```

> Ensure that `tkinter` is installed on your system. On Ubuntu/Debian: `sudo apt install python3-tk`

### Hardware

- 1 Wemos D1 Mini (ESP8266)
- 1 $100 \Omega$ resistor
- 1 RJ-11/12 6-pin breakout (6P6C)
- 1 $30 \times 70 \text{mm}$ protoboard

## Serial Stream

Chart created by [@Gioee](https://github.com/Gioee): https://github.com/Gioee/fav3er0-master-emulator

| Byte        | 0                                                                          | 1                           | 2                           | 3                        | 4                       | 5                                                                                                 | 6                                      | 7           | 8                            | 9                                      |
| ----------- | -------------------------------------------------------------------------- | --------------------------- | --------------------------- | ------------------------ | ----------------------- | ------------------------------------------------------------------------------------------------- | -------------------------------------- | ----------- | ---------------------------- | -------------------------------------- |
| Example     | 0xFF                                                                       | 0x06                        | 0x12                        | 0x56                     | 0x02                    | 0x14                                                                                              | 0x0A                                   | 0x00        | 0x38                         | 0xC5                                   |
| Explanation | This Byte identifies the beginning of the string, it has to be always 0xFF | Right score, in this case 6 | Left score, in this case 12 | Seconds, in this case 56 | Minutes, in this case 2 | State of the lamps, case 0b00000000 no lamp is activated, case 0b00111111 every lamp is activated | Number of matches and priorite signals | Always 0x00 | Red and yellow penalty cards | Checksum = Sum of previous Bytes % 256 |

- 6° byte: XXh = Define the state of the lamps (red, green, whites and yellows). Every bit defines the state of a lamp (zero=OFF, 1=ON). Following is the correspondence of the 8 bits:
  - Bit D0 = Left white lamp
  - Bit D1 = Right white lamp
  - Bit D2 = RED lamp (left)
  - Bit D3 = GREEN lamp (right)
  - Bit D4 = Right yellow lamp
  - Bit D5 = Left yellow lamp
  - Bit D6 = 0 not used
  - Bit D7 = 0 not used
  - Example: if byte 6° = 14h , we have D2=1 (red light=on) and D4=1 (right yellow light=on)
  - Credit to /u/Dalboz989 on Reddit: https://www.reddit.com/r/Fencing/comments/cufcku/do_anyone_know_where_to_find_those_lightings_and/ey15ezm/

## Help

## License

This project is license under the GNU General Public License v3.0 License - see the LICENSE file for details

## Acknowledgements

The `FaveroParser` is based off [@vehmont](https://github.com/vehemont)'s parser used in their [favero repeater](https://github.com/vehemont/Favero_Repeater) project

> importantly this work is originally based off [@BenHohn2004](https://github.com/BenKohn2004)'s [favero overlay](https://github.com/BenKohn2004/Favero_Overlay) and [@Gioee](https://github.com/Gioee)'s [favero emulator](https://github.com/Gioee/fav3er0-master-emulator)
