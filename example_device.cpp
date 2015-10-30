#include "example_device.h"

message_t hibikeRecieveBuff;
const hibike_uid_t UID = {
  0,        // Device Type
  0,        // Year
  123456789,    // ID
};

uint64_t prevTime, currTime, heartbeat;
uint16_t subDelay;
uint8_t data, reading_offset;
bool led_enabled;

void setup() {
  Serial.begin(115200);
  prevTime = millis();
  subDelay = 0;

  // Setup Error LED
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  led_enabled = false;

  // Setup sensor input
  pinMode(IN_PIN, INPUT);

}

void loop() {
  // Read sensor
  data = digitalRead(IN_PIN);
  currTime = millis();

  // Check for Hibike packets
  if (Serial.available()) {
    if (read_message(&hibikeRecieveBuff) == -1) {
      toggleLED();
    } else {
      switch (hibikeRecieveBuff.messageID) {
        case SUBSCRIPTION_REQUEST:
          // change subDelay and send SUB_RESP
          subDelay = payload_to_uint16(hibikeRecieveBuff.payload);
          send_subscription_response(*UID, subDelay);
          break;

        case SUBSCRIPTION_RESPONSE:
          // Unsupported packet
          while (Serial.available() > 0) {
            Serial.read();
          }
          toggleLED();
          break;

        case DATA_UPDATE:
          // Unsupported packet
          while (Serial.available() > 0) {
            Serial.read();
          }
          toggleLED();
          break;

        default:
          // Uh oh...
          while (Serial.available() > 0) {
            Serial.read();
          }
          toggleLED();
      }
    }
  }

  if (currTime - heartbeat >= 1000) {
    heartbeat = currTime;
    toggleLED();
  }

  //Send data update
  currTime = millis();
  if (subDelay != 0 && currTime - prevTime >= subDelay) {
    prevTime = currTime;
    // data_update(&hibikeSendBuff, &data, 1);
    send_data_update(&data, 1);
  }
}





void toggleLED() {
  if (led_enabled) {
    digitalWrite(LED_PIN, LOW);
    led_enabled = false;
  } else {
    digitalWrite(LED_PIN, HIGH);
    led_enabled = true;
  }
}