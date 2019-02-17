#include "TimerOne.h"
#include "motor.h"
#include "pindefs.h"
#include "PolarBear.h"
#include "pid.h"
#include "encoder.h"

//tab to handle all controls issued to the motor including driving and braking

bool motorEnabled = false;
float deadBand = 0.05;

void motorSetup() 
{
	pinMode(feedback,INPUT);
	pinMode(PWM1, OUTPUT);
	pinMode(PWM2, OUTPUT);
	pinMode(INV, OUTPUT);
	digitalWrite(INV, LOW);

	motorEnable();
}

void motorEnable() 
{
	clearFault();
	motorEnabled = true;
}

void motorDisable() 
{
	disablePID();
	resetPID();
	resetEncoder();
	resetPWMInput();
	resetDriveMode();
	motorEnabled = false;
}

bool isMotorEnabled() 
{
	return motorEnabled;
}

//returns current in amps
float readCurrent() 
{
	return (analogRead(feedback) / 0.0024); //Number was generated based on a few tests across multiple boards. Valid for majority of good boards
}

//takes a value from -1 to 1 inclusive and writes to the motor and sets the PWM1 and PWM2 pins for direction
void drive(float target) 
{
	if (target < -deadBand) {
		digitalWrite(PWM1, HIGH);
		analogWrite(PWM2, 255 - (int) (-1.0 * target * 255.0));
		// Timer1.pwm(PWM2, (int) (-1 * target * 1023));
	} else if (target > deadBand) {
		digitalWrite(PWM2, HIGH);
		analogWrite(PWM1, 255 - (int) (target * 255.0));
		// Timer1.pwm(PWM1, (int) (target * 1023));
	} else {
		digitalWrite(PWM2, HIGH);
		digitalWrite(PWM1, HIGH);
		target = 0;
	}
}


void clearFault() 
{
	digitalWrite(PWM1, HIGH);
	digitalWrite(PWM2, HIGH);
}

void setDeadBand(float range) 
{
	deadBand = range;
}

float readDeadBand() 
{
	return deadBand;
}
