#include <ESP8266WiFi.h>
#include <WiFiUdp.h>
#include <ArduinoJson.h>

#define MY_NAME "PARSER"

const char *ssid = "replaySystem";
const char *password = "12345678";

const unsigned int MAX_MESSAGE_LEN = 10;
const unsigned int MAX_SERIAL_BUFFER_BYTES = 512;
const char STARTING_BYTE = 255;

unsigned int COUNTER = 0;
bool MACHINE_OFF = true;

WiFiUDP udp;

IPAddress laptopIP(192, 168, 4, 2);
const int udpPort = 5050;

struct dataPacket
{
	unsigned int Right_Score;
	unsigned int Left_Score;
	unsigned int Seconds_Remaining;
	unsigned int Minutes_Remaining;
	bool Green_Light;
	bool Red_Light;
	bool White_Green_Light;
	bool White_Red_Light;
	bool Yellow_Green_Light;
	bool Yellow_Red_Light;
	bool Yellow_Card_Green;
	bool Yellow_Card_Red;
	bool Red_Card_Green;
	bool Red_Card_Red;
	bool Priority_Left;
	bool Priority_Right;
};

// bool newData = false;
unsigned int message_pos = 0;

void setup()
{
	Serial.begin(2400);
	delay(1000);
	Serial.println();
	Serial.println();
	Serial.print("Initializing ");
	Serial.println(MY_NAME);
	WiFi.softAP(ssid, password);
	delay(3000);

	udp.begin(udpPort);
	Serial.println("Initialized.");
}

void loop()
{

	dataPacket packet;

	while (Serial.available() > 0)
	{
		static char message[MAX_MESSAGE_LEN];
		static char prev_message[MAX_MESSAGE_LEN];

		char inByte = Serial.read();

		if (inByte == STARTING_BYTE)
		{
			message_pos = 0;
		}
		if (message_pos < (MAX_MESSAGE_LEN - 1))
		{
			message[message_pos++] = inByte;
		}
		else if (message_pos == (MAX_MESSAGE_LEN - 1))
		{
			message[message_pos] = inByte;
			byte checksum = 0;

			for (int i = 0; i < MAX_MESSAGE_LEN; i++)
			{
				if (i == 9)
				{
					checksum = checksum % 256;
				}
				else
				{
					checksum += message[i];
				}
			}
			if (message[9] == checksum)
			{
				COUNTER = 0;
				MACHINE_OFF = false;

				if (message[1] != prev_message[1] || message[2] != prev_message[2] || message[3] != prev_message[3] ||
					message[4] != prev_message[4] || message[5] != prev_message[5] || message[6] != prev_message[6] ||
					message[7] != prev_message[7] || message[8] != prev_message[8])
				{
					Serial.print("The message in HEX is:");
					for (int i = 0; i < MAX_MESSAGE_LEN; i++)
					{
						Serial.print(message[i], HEX);
						Serial.print(",");
					}
					Serial.print("\n");
					// newData = true;

					// assigns values from message to packet
					packet.Green_Light = bitRead(message[5], 3);
					packet.Red_Light = bitRead(message[5], 2);
					packet.White_Green_Light = bitRead(message[5], 1);
					packet.White_Red_Light = bitRead(message[5], 0);
					packet.Yellow_Green_Light = bitRead(message[5], 4);
					packet.Yellow_Red_Light = bitRead(message[5], 5);

					packet.Yellow_Card_Green = bitRead(message[8], 2);
					packet.Yellow_Card_Red = bitRead(message[8], 3);
					packet.Red_Card_Green = bitRead(message[8], 0);
					packet.Red_Card_Red = bitRead(message[8], 1);

					packet.Priority_Right = bitRead(message[6], 2);
					packet.Priority_Left = bitRead(message[6], 3);

					// score and time - has to be converted to an int from hex
					packet.Right_Score = hex_string_to_int(message[1]);
					packet.Left_Score = hex_string_to_int(message[2]);
					packet.Seconds_Remaining = hex_string_to_int(message[3]);
					packet.Minutes_Remaining = hex_string_to_int(message[4]);

					for (int i = 0; i < MAX_MESSAGE_LEN; i++)
					{
						prev_message[i] = message[i];
					}

					message_pos = 0;

					if (Serial.available() > MAX_SERIAL_BUFFER_BYTES)
					{
						Serial.println(".............Clearing the Serial Buffer.............");
						while (Serial.available() > 0)
						{
							char junk = Serial.read();
						}
					}
					// JSON encode
					StaticJsonDocument<MAX_SERIAL_BUFFER_BYTES> doc;
					doc["Right_Score"] = packet.Right_Score;
					doc["Left_Score"] = packet.Left_Score;
					doc["Seconds_Remaining"] = packet.Seconds_Remaining;
					doc["Minutes_Remaining"] = packet.Minutes_Remaining;
					doc["Green_Light"] = packet.Green_Light;
					doc["Red_Light"] = packet.Red_Light;
					doc["White_Green_Light"] = packet.White_Green_Light;
					doc["White_Red_Light"] = packet.White_Red_Light;
					doc["Yellow_Green_Light"] = packet.Yellow_Green_Light;
					doc["Yellow_Red_Light"] = packet.Yellow_Red_Light;
					doc["Yellow_Card_Green"] = packet.Yellow_Card_Green;
					doc["Yellow_Card_Red"] = packet.Yellow_Card_Red;
					doc["Red_Card_Green"] = packet.Red_Card_Green;
					doc["Red_Card_Red"] = packet.Red_Card_Red;
					doc["Priority_Left"] = packet.Priority_Left;
					doc["Priority_Right"] = packet.Priority_Right;

					char buffer[MAX_SERIAL_BUFFER_BYTES];
					size_t len = serializeJson(doc, buffer);

					udp.beginPacket(laptopIP, udpPort);
					udp.write((uint8_t *)buffer, len);
					udp.endPacket();
				}
			}
			else
			{
				Serial.println("Unexpected Message Position, Resetting to zero.");
				message_pos = 0;
			}
		}
		else
		{
			Serial.println("Wrong checksum! Throwing it out.");
			message_pos = 0;
		}
	}
}

unsigned int hex_string_to_int(unsigned char msg)
{
	unsigned int high = msg >> 4;  // upper 4 bits (high nibble)
	unsigned int low = msg & 0x0F; // lower 4 bits (low nibble)

	if (low < 10 && high * 10 + low < 100)
	{
		return high * 10 + low;
	}
	else
	{
		return 0; // fallback for invalid input
	}
}
