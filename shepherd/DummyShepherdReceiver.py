import queue
# import random as rand
from LCM import *
from Utils import *

def receiver():
    overdrive = True
    events = queue.Queue()
    lcm_start_read(LCM_TARGETS.SHEPHERD, events)
    while True:
        event = events.get(True)
        print("got event")
        # if event[0] == SHEPHERD_HEADER.GENERATE_RFID:
        #     s = []
        #     for _ in range(6):
        #         s.append(rand.randrange(10))
        #     x = {"RFID_list": s}
        #     lcm_send(LCM_TARGETS.UI, UI_HEADER.RFID_LIST, x)
        #     print("Sent RFIDs")
        if event[0] == SHEPHERD_HEADER.GET_SCORES:
            x = {"blue_score": rand.randrange(100), "gold_score": rand.randrange(100)}
            lcm_send(LCM_TARGETS.UI, UI_HEADER.SCORES, x)
            print("Sent scores")
        if event[0] == SHEPHERD_HEADER.SCORE_ADJUST:
            print(event[1])
        if event[0] == SHEPHERD_HEADER.GET_MATCH_INFO:
            x = {"match_num": rand.randrange(100), "b1name": "- a string1",
                 "b1num": rand.randrange(10), "b2name": "- a string2",
                 "b2num": rand.randrange(10), "g1name": "- a string3",
                 "g1num": rand.randrange(10), "g2name": "- a string4", "g2num": rand.randrange(10)}
            lcm_send(LCM_TARGETS.UI, UI_HEADER.TEAMS_INFO, x)
            print("Sent Team Info")
        # if event[0] == SHEPHERD_HEADER.LAUNCH_BUTTON_TRIGGERED:
        #     lcm_send(LCM_TARGETS.SCOREBOARD, SCOREBOARD_HEADER.LAUNCH_BUTTON_TIMER_START)
        if event[0] == SHEPHERD_HEADER.SETUP_MATCH:
            print(event[1])
        if event[0] == SHEPHERD_HEADER.START_NEXT_STAGE:
            print("starting stage")
        if event[0] == SHEPHERD_HEADER.RESET_CURRENT_STAGE:
            print("reset stage")
        if event[0] == SHEPHERD_HEADER.RESET_MATCH:
            print("reset match")
        if overdrive:
            lcm_send(LCM_TARGETS.SCOREBOARD, SCOREBOARD_HEADER.OVERDRIVE_START, {})
            overdrive = False
        lcm_send(LCM_TARGETS.SCOREBOARD, SCOREBOARD_HEADER.PERKS_SELECTED, {"alliance": ALLIANCE_COLOR.BLUE, "perk_1": PERKS.TAFFY, "perk_2": PERKS.TAFFY, "perk_3": PERKS.TAFFY})
        lcm_send(LCM_TARGETS.SCOREBOARD, SCOREBOARD_HEADER.APPLIED_EFFECT, {"alliance": ALLIANCE_COLOR.BLUE, "effect": EFFECTS.BLACKMAIL})
        lcm_send(LCM_TARGETS.SCOREBOARD, SCOREBOARD_HEADER.LAUNCH_BUTTON_TIMER_START, {"alliance": ALLIANCE_COLOR.BLUE, "button": 1})

if __name__ == "__main__":
    receiver()
