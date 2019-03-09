import threading
import queue
from LCM import *
from Utils import *

def sender():
    input_to_header = {
        "launch"    : SHEPHERD_HEADER.LAUNCH_BUTTON_TRIGGERED,
        "code"      : SHEPHERD_HEADER.CODE_APPLICATION,
        "overdrive" : SCOREBOARD_HEADER.OVERDRIVE_START,
        "effect"    : SCOREBOARD_HEADER.APPLIED_EFFECT,
        "timer"     : SCOREBOARD_HEADER.STAGE_TIMER_START
    }

    input_to_alliance = {
        "gold"  : ALLIANCE_COLOR.GOLD,
        "blue"  : ALLIANCE_COLOR.BLUE,
    }

    input_to_launch = {
        "1"     : 1,
        "2"     : 2,
    }

    input_to_effect = {
        "twist" : EFFECTS.BLACKMAIL,
        "spoil" : EFFECTS.SPOILED_CANDY
    }

    while True:
        new_input = input_to_header.get(input("Command: {launch, code, effect, overdrive, timer} "))
        if new_input == SHEPHERD_HEADER.LAUNCH_BUTTON_TRIGGERED:
            alliance = input_to_alliance.get(input("Alliance: blue gold "))
            button_num = input_to_launch.get(input("Launch button: 1 2 "))
            if button_num is None or alliance is None:
                print("Invalid input")
                continue
            lcm_send(LCM_TARGETS.SHEPHERD, new_input, {"alliance" : alliance, "button" : button_num})

        elif new_input == SHEPHERD_HEADER.CODE_APPLICATION: # {alliance, result}
            alliance = input_to_alliance.get(input("Alliance: blue gold "))
            code = input("Code: ")
            if alliance is None or code is None:
                print("Invalid input")
                continue
            lcm_send(LCM_TARGETS.SHEPHERD, new_input, {"alliance" : alliance,
                                                       "result" : code})

        elif new_input == SCOREBOARD_HEADER.APPLIED_EFFECT: # {alliance, result}
            alliance = input_to_alliance.get(input("Alliance: blue gold "))
            effect = input_to_effect.get(input("Effect: twist spoil "))
            if alliance is None or effect is None:
                print("Invalid input")
                continue
            lcm_send(LCM_TARGETS.SCOREBOARD, new_input, {"alliance" : alliance, "effect" : effect})

        elif new_input == SCOREBOARD_HEADER.OVERDRIVE_START:
            lcm_send(LCM_TARGETS.SCOREBOARD, new_input, {})

        elif new_input == SCOREBOARD_HEADER.STAGE_TIMER_START:
            try:
                time = int(input("Time (s): "))
            except (ValueError, TypeError):
                print("Invalid input")
                continue
            lcm_send(LCM_TARGETS.SCOREBOARD, new_input, {"time": time})

        # elif new_input == SCOREBOARD_HEADER.APPLIED_EFFECT
        #     alliance = input_to_alliance.get(input("Alliance: blue gold "))
        #     button_num = input_to_launch.get(input("Launch button: 1 2"))
        #     if button_num is None or alliance is None:
        #         print("Invalid input")
        #         continue
        #     lcm_send(LCM_TARGETS.SHEPHERD, new_input, {"alliance" : alliance, "button" : button_num})
        else:
            print("Invalid input")

def receiver():
    events = queue.Queue()
    lcm_start_read(LCM_TARGETS.SENSORS, events)
    while True:
        event = events.get(True)
        print(event)

if __name__ == "__main__":
    sender_thread = threading.Thread(target=sender, name="DummySensorSender")
    recv_thread = threading.Thread(target=receiver, name="DummySensorReceiver")
    sender_thread.start()
    recv_thread.start()
