#include <ESP8266WiFi.h>
#include <WiFiUdp.h>
#include <ArduinoJson.h>

#define MY_NAME "PARSER"

int test = 0;

const char *ssid = "replaySystem";
const char *password = "12345678";

const unsigned int MAX_MESSAGE_LEN = 10;
const unsigned int MAX_SERIAL_BUFFER_BYTES = 512;
const char STARTING_BYTE = 512;

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

bool newData = false;
unsigned int mesage_pos = 0;

void setup()
{
	Serial.begin(2400);
	WiFi.softAP(ssid, password);
	delay(3000);

	udp.begin(udpPort);
}

void loop()
{
	test++;
	dataPacket packet;

	// Sample data
	packet.Right_Score = test;
	packet.Left_Score = 0;
	packet.Seconds_Remaining = 0;
	packet.Minutes_Remaining = 0;
	packet.Green_Light = true;
	packet.Red_Light = false;
	packet.White_Green_Light = true;
	packet.White_Red_Light = false;
	packet.Yellow_Green_Light = true;
	packet.Yellow_Red_Light = false;
	packet.Yellow_Card_Green = true;
	packet.Yellow_Card_Red = false;
	packet.Red_Card_Green = false;
	packet.Red_Card_Red = true;
	packet.Priority_Left = true;
	packet.Priority_Right = false;

	// JSON encode
	StaticJsonDocument<512> doc;
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

	char buffer[512];
	size_t len = serializeJson(doc, buffer);

	udp.beginPacket(laptopIP, udpPort);
	udp.write((uint8_t *)buffer, len);
	udp.endPacket();

	delay(15000);
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