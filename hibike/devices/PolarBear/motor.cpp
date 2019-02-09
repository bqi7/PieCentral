#include "TimerOne.h"
#include "motor.h"
#include "pindefs.h"
#include "PolarBear.h"
#include "pid.h"
#include "encoder.h"

//tab to handle all controls issued to the motor including driving and braking

bool motorEnabled = false;
float deadBand = 0.05;

void motorSetup() {
  pinMode(feedback,INPUT);
  pinMode(PWM1, OUTPUT);
  pinMode(PWM2, OUTPUT);
  pinMode(INV, OUTPUT);
  digitalWrite(INV, LOW);

  motorEnable();
  //pinMode(PWM, OUTPUT);
}

void motorEnable() {
  clearFault();
  // pinMode(enable_pin, INPUT); //pin is pulled up, so put in high impedance state instead of writing high
  motorEnabled = true;
}

void motorDisable() {
  // pinMode(enable_pin, OUTPUT);
  // digitalWrite(enable_pin, LOW);
  disablePID();
  resetPID();
  resetEncoder();
  resetPWMInput();
  resetDriveMode();
  motorEnabled = false;
}

bool isMotorEnabled() {
  return motorEnabled;
}

//returns current in amps
float readCurrent() {
  return (analogRead(feedback) / 0.0024); //Number was generated based on a few tests across multiple boards. Valid for majority of good boards
}

//takes a value from -1 to 1 inclusive and writes to the motor and sets the PWM1 and PWM2 pins for direction
void drive(float target) {
  if (target < -deadBand) {
    digitalWrite(PWM2, HIGH);
    digitalWrite(PWM1, LOW);
    Timer1.pwm(PWM1, (int) (-1 * target * 1023));
  } else if (target > deadBand) {
    digitalWrite(PWM1, HIGH);
    digitalWrite(PWM2, LOW);
    Timer1.pwm(PWM2, (int) (target * 1023));
  } else {
    target = 0;
    digitalWrite(PWM1, HIGH);
    digitalWrite(PWM2, HIGH);
  }
}


void clearFault() {
  digitalWrite(PWM1, HIGH);
  digitalWrite(PWM2, HIGH);
}

void setDeadBand(float range) {
  deadBand = range;
}

float readDeadBand() {
  return deadBand;
}
