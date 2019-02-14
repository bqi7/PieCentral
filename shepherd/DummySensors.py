import threading
import queue
from LCM import *
from Utils import *

def sender():
    input_to_header = {
        "launch"   : SHEPHERD_HEADER.LAUNCH_BUTTON_TRIGGERED,
        "code"  : SHEPHERD_HEADER.CODE_APPLICATION,
    }

    input_to_alliance = {
        "gold"  : ALLIANCE_COLOR.GOLD,
        "blue"  : ALLIANCE_COLOR.BLUE,
    }

    input_to_launch = {
        "1"     : 1,
        "2"     : 2,
        "3"     : 3,
        "4"     : 4,
    }

    while True:
        new_input = input_to_header.get(input("Command: launch code "))
        if new_input == SHEPHERD_HEADER.LAUNCH_BUTTON_TRIGGERED:
            alliance = input_to_alliance.get(input("Alliance: blue gold "))
            button_num = input_to_goal.get(input("Launch button: 1 2"))
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
