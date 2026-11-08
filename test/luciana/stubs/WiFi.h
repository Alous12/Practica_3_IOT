#pragma once
struct WiFiMock { int RSSI() { return -55; } };
extern WiFiMock WiFi;
