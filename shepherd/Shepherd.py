import argparse
import queue
import random
import time
from Alliance import *
from LCM import *
from Timer import *
from Utils import *
import Code
import Sheet

__version__ = (1, 0, 0)

#TODO move comunication of game state and of code stuff directly to runtime
#TODO send dawn robot IPs

###########################################
# Evergreen Methods
###########################################

#TODO send stage to scoreboard
def start():
    '''
    Main loop which processes the event queue and calls the appropriate function
    based on game state and the dictionary of available functions
    '''
    global events
    events = queue.Queue()
    lcm_start_read(LCM_TARGETS.SHEPHERD, events)
    while True:
        print("GAME STATE OUTSIDE: ", game_state)
        time.sleep(0.1)
        payload = events.get(True)
        print(payload)
        if game_state == STATE.SETUP:
            func = setup_functions.get(payload[0])
            if func is not None:
                func(payload[1])
            else:
                print("Invalid Event in Setup")
        elif game_state == STATE.PERK_SELCTION:
            func = perk_selection_functions.get(payload[0])
            if func is not None:
                func(payload[1])
            else:
                print("Invalid Event in Perk_selection")
        elif game_state == STATE.AUTO_WAIT:
            func = auto_wait_functions.get(payload[0])
            if func is not None:
                func(payload[1])
            else:
                print("Invalid Event in Auto_wait")
        elif game_state == STATE.AUTO:
            func = auto_functions.get(payload[0])
            if func is not None:
                func(payload[1])
            else:
                print("Invalid Event in Auto")
        elif game_state == STATE.WAIT:
            func = wait_functions.get(payload[0])
            if func is not None:
                func(payload[1])
            else:
                print("Invalid Event in Wait")
        elif game_state == STATE.TELEOP:
            func = teleop_functions.get(payload[0])
            if func is not None:
                func(payload[1])
            else:
                print("Invalid Event in Teleop")
        elif game_state == STATE.END:
            func = end_functions.get(payload[0])
            if func is not None:
                func(payload[1])
            else:
                print("Invalid Event in End")

def to_setup(args):
    '''
    Move to the setup stage which is should push scores from previous game to spreadsheet,
    load the teams for the upcoming match, reset all state, and send information to scoreboard.
    By the end, should be ready to start match.
    '''
    global match_number
    global game_state

    b1_name, b1_num = args["b1name"], args["b1num"]
    b2_name, b2_num = args["b2name"], args["b2num"]
    g1_name, g1_num = args["g1name"], args["g1num"]
    g2_name, g2_num = args["g2name"], args["g2num"]

    if game_state == STATE.END:
        flush_scores()

    match_number = args["match_num"]

    if alliances[ALLIANCE_COLOR.BLUE] is not None:
        reset()

    code_setup()

    alliances[ALLIANCE_COLOR.BLUE] = Alliance(ALLIANCE_COLOR.BLUE, b1_name,
                                              b1_num, b2_name, b2_num)
    alliances[ALLIANCE_COLOR.GOLD] = Alliance(ALLIANCE_COLOR.GOLD, g1_name,
                                              g1_num, g2_name, g2_num)

    msg = {"b1num":b1_num, "b2num":           b2_num, "g1num":g1_num, "g2num":g2_num}
    lcm_send(LCM_TARGETS.TABLET, TABLET_HEADER.TEAMS, msg)

    lcm_send(LCM_TARGETS.SCOREBOARD, SCOREBOARD_HEADER.TEAMS, {
        "b1name" : b1_name, "b1num" : b1_num,
        "b2name" : b2_name, "b2num" : b2_num,
        "g1name" : g1_name, "g1num" : g1_num,
        "g2name" : g2_name, "g2num" : g2_num,
        "match_num" : match_number})

    game_state = STATE.SETUP
    print("ENTERING SETUP STATE")
    print({"blue_score" : alliances[ALLIANCE_COLOR.BLUE].score,
           "gold_score" : alliances[ALLIANCE_COLOR.GOLD].score})


def to_perk_selection(args):
    global game_state
    game_timer.start_timer(CONSTANTS.PERK_SELECTION_TIME)
    game_state = STATE.PERK_SELCTION
    LCM.send(LCM_TARGETS.TABLET, TABLET_HEADER.COLLECT_PERKS)
    print("ENTERING PERK SELECTION STATE")

def to_auto_wait(args):
    global game_state
    game_state = STATE.AUTO_WAIT
    LCM.send(LCM_TARGETS.TABLET, TABLET_HEADER.COLLECT_CODES)
    print("ENTERING AUTO_WAIT STATE")

def to_auto(args):
    '''
    Move to the autonomous stage where robots should begin autonomously.
    By the end, should be in autonomous state, allowing any function from this
    stage to be called and autonomous match timer should have begun.
    '''
    global game_state
    game_timer.start_timer(CONSTANTS.AUTO_TIME)
    game_state = STATE.AUTO
    enable_robots(True)
    lcm_send(LCM_TARGETS.SCOREBOARD, SCOREBOARD_HEADER.STAGE_TIMER_START,
             {"time" : CONSTANTS.AUTO_TIME})
    print("ENTERING AUTO STATE")

def to_wait(args):
    '''
    Move to the waiting stage, between autonomous and teleop periods.
    By the end, should be in wait state and the robots should be disabled.
    Some years, there might be methods that can be called once in the wait stage
    '''
    global game_state
    game_state = STATE.WAIT
    disable_robots()
    print("ENTERING WAIT STATE")

def to_teleop(args):
    '''
    Move to teleoperated stage where robots are enabled and controlled manually.
    By the end, should be in teleop state and the teleop match timer should be started.
    '''
    global game_state
    game_state = STATE.TELEOP

    Timer.reset_all()
    game_timer.start_timer(CONSTANTS.TELEOP_TIME)
    overdrive_time = random.randint(0,CONSTANTS.TELEOP_TIME -
                                      CONSTANTS.OVERDRIVE_TIME)
    overdrive_timer.start_timer(overdrive_time)
    print("overdrive will happen at " + overdrive_time // 60 + ":" +
          overdrive_time % 60)

    enable_robots(False)
    lcm_send(LCM_TARGETS.SCOREBOARD, SCOREBOARD_HEADER.STAGE_TIMER_START,
             {"time" : CONSTANTS.TELEOP_TIME})
    print("ENTERING TELEOP STATE")

def to_end(args):
    '''
    Move to end stage after the match ends. Robots should be disabled here
    and final score adjustments can be made.
    '''


    global game_state
    lcm_send(LCM_TARGETS.UI, UI_HEADER.SCORES,
             {"blue_score" : math.floor(alliances[ALLIANCE_COLOR.BLUE].score),
              "gold_score" : math.floor(alliances[ALLIANCE_COLOR.GOLD].score)})
    game_state = STATE.END
    disable_robots()
    print("ENTERING END STATE")

def reset(args=None):
    '''
    Resets the current match, moving back to the setup stage but with the current teams loaded in.
    Should reset all state being tracked by Shepherd.
    ****THIS METHOD MIGHT NEED UPDATING EVERY YEAR BUT SHOULD ALWAYS EXIST****
    '''
    global game_state, events
    game_state = STATE.SETUP
    Timer.reset_all()
    events = queue.Queue()
    lcm_start_read(LCM_TARGETS.SHEPHERD, events)
    lcm_send(LCM_TARGETS.SCOREBOARD, SCOREBOARD_HEADER.RESET_TIMERS)
    for alliance in alliances.values():
        if alliance is not None:
            alliance.reset()
    disable_robots()
    buttons['gold_1'] = False
    buttons['gold_2'] = False
    buttons['blue_1'] = False
    buttons['blue_2'] = False
    lcm_send(LCM_TARGETS.TABLET, TABLET_HEADER.RESET)
    print("RESET MATCH, MOVE TO SETUP")

def get_match(args):
    '''
    Retrieves the match based on match number and sends this information to the UI
    '''
    match_num = int(args["match_num"])
    info = Sheet.get_match(match_num)
    info["match_num"] = match_num
    lcm_send(LCM_TARGETS.UI, UI_HEADER.TEAMS_INFO, info)

def score_adjust(args):
    '''
    Allow for score to be changed based on referee decisions
    '''
    blue_score, gold_score = args["blue_score"], args["gold_score"]
    alliances[ALLIANCE_COLOR.BLUE].score = blue_score
    alliances[ALLIANCE_COLOR.GOLD].score = gold_score
    lcm_send(LCM_TARGETS.SCOREBOARD, SCOREBOARD_HEADER.SCORE,
             {"alliance" : alliances[ALLIANCE_COLOR.BLUE].name,
              "score" : math.floor(alliances[ALLIANCE_COLOR.BLUE].score)})
    lcm_send(LCM_TARGETS.SCOREBOARD, SCOREBOARD_HEADER.SCORE,
             {"alliance" : alliances[ALLIANCE_COLOR.GOLD].name,
              "score" : math.floor(alliances[ALLIANCE_COLOR.GOLD].score)})

def get_score(args):
    '''
    Send the current blue and gold score to the UI
    '''
    if alliances[ALLIANCE_COLOR.BLUE] is None:
        lcm_send(LCM_TARGETS.UI, UI_HEADER.SCORES,
                 {"blue_score" : None,
                  "gold_score" : None})
    else:
        lcm_send(LCM_TARGETS.UI, UI_HEADER.SCORES,
                 {"blue_score" : math.floor(alliances[ALLIANCE_COLOR.BLUE].score),
                  "gold_score" : math.floor(alliances[ALLIANCE_COLOR.GOLD].score)})

def flush_scores():
    '''
    Sends the most recent match score to the spreadsheet if connected to the internet
    '''
    if alliances[ALLIANCE_COLOR.BLUE] is not None:
        Sheet.write_scores(match_number, alliances[ALLIANCE_COLOR.BLUE].score,
                           alliances[ALLIANCE_COLOR.GOLD].score)
    return -1

def enable_robots(autonomous):
    '''
    Sends message to Dawn to enable all robots. The argument should be a boolean
    which is true if we are entering autonomous mode
    '''
    msg = {"autonomous": autonomous, "enabled": True}

    lcm_send(LCM_TARGETS.DAWN, DAWN_HEADER.ROBOT_STATE, msg)



def disable_robots():
    '''
    Sends message to Dawn to disable all robots
    '''
    msg = {"autonomous": False, "enabled": False}
    lcm_send(LCM_TARGETS.DAWN, DAWN_HEADER.ROBOT_STATE, msg)



###########################################
# Game Specific Methods
###########################################

def disable_robot(args):
    '''
    Send message to Dawn to disable the robots of team
    '''
    team_number = args["team_number"]
    msg = {"team_number": team_number, "autonomous": False, "enabled": False}
    lcm_send(LCM_TARGETS.DAWN, DAWN_HEADER.SPECIFIC_ROBOT_STATE, msg)

def set_master_robot(args):
    '''
    Set the master robot of the alliance
    '''
    alliance = args["alliance"]
    team_name = args["team_name"]
    if team_name == alliance.team_1_name:
        team_number = alliance.team_1_number
    else:
        team_number = alliance.team_2_number
    msg = {"alliance": alliance, "master": team_number}
    lcm_send(LCM_TARGETS.DAWN, DAWN_HEADER.MASTER, msg)

def next_code():
    if codes_used == []:
       codes_used.append(codes[0])
       return codes[0]
    index = len(codes_used)
    codes_used.append(codes[index])
    return codes[index]

def code_setup():
    '''
    Set up code_solution and code_effect dictionaries
    '''
    global code_solution
    global code_effect
    code_solution = Code.assign_code_solution()
    code_effect = Code.assign_code_effect()
    msg = {"codes_solutions": code_solution}

def bounce_code(args):
    msg = {"alliance":args["alliance"], "result":args["result"]}
    lcm.send(LCM_TARGETS.TABLET, TABLET_HEADER.CODE, msg)

def apply_code(args):
    '''
    Send Scoreboard the effect if the answer is correct
    '''
    alliance = args["alliance"]
    answer = args["answer"]
    if (answer is not None and answer in code_solution.values()):
        code = [k for k, v in code_solution.items() if v == answer][0]
        msg = {"alliance": alliance, "effect": code_effect[code]}
        if code_effect[code] == EFFECTS.TWIST and not alliance.can_twist:
            code_effect[code] = EFFECTS.SPOILED_CANDY
        if code_effect[code] == EFFECTS.TWIST:
            alliance.can_twist = False
        lcm_send(LCM_TARGETS.SCOREBOARD, SCOREBOARD_HEADER.APPLIED_EFFECT, msg)
    else:
        msg = {"alliance": alliance}
        lcm_send(LCM_TARGETS.SENSORS, SENSORS_HEADER.FAILED_POWERUP, msg)


def end_teleop(args):
    blue_robots_disabled = False
    gold_robots_disabled = False
    if PERKS.TAFFY in alliance_perks(alliances[ALLIANCE_COLOR.BLUE]):
        extended_teleop_timer.start_timer(CONSTANTS.TAFFY_TIME)
        blue_robots_disabled = True
    elif PERKS.TAFFY in alliance_perks(alliances[ALLIANCE_COLOR.GOLD]):
        extended_teleop_timer.start_timer(CONSTANTS.TAFFY_TIME)
        gold_robots_disabled = False
    else:
        to_end(args)
    if gold_robots_disabled:
        disable_robot({"team_number":alliances[ALLIANCE_COLOR.GOLD].team_1_number})
        disable_robot({"team_number":alliances[ALLIANCE_COLOR.GOLD].team_2_number})
    if blue_robots_disabled:
        disable_robot({"team_number":alliances[ALLIANCE_COLOR.BLUE].team_1_number})
        disable_robot({"team_number":alliances[ALLIANCE_COLOR.BLUE].team_2_number})

def alliance_perks(alliance):
    return (alliance.perk_1, alliance.perk_2, alliance.perk_3)

def apply_perks(args):
    alliance = args['alliance']
    alliance.perk_1 = args['perk_1']
    alliance.perk_2 = args['perk_2']
    alliance.perk_3 = args['perk_3']

def launch_button_triggered(args):
    '''
    check if allowed once every 30 seconds, give one of the codes to the correct alliance through Dawn,
    update scoreboard
    '''
    alliance = args["alliance"]
    button = args["button"]
    lb = alliance + "_" + str(button)
    if not timer_dictionary[lb].is_running():
        msg = {"alliance": alliance, "button": button}
        code = next_code()
        send_code(alliance, code)
        timer_dictionary[lb].start_timer(CONSTANTS.COOLDOWN)
        lcm_send(LCM_TARGETS.SCOREBOARD, SCOREBOARD_HEADER.LAUNCH_BUTTON_TIMER_START, msg)

def send_code(alliance, code):
    pass

def auto_launch_button_triggered(args):
    ## TODO: add ten score, mark button as dirty, sent to sc (both things)
    alliance = args["alliance"]
    button = args["button"]
    temp_str = alliance + "_" + str(button)
    if not buttons[temp_str]:
        alliance.change_score(10)
        buttons[temp_str] = True
        msg = {"alliance": alliance, "button": button}
        lcm_send(LCM_TARGETS.SCOREBOARD, SCOREBOARD_HEADER.LAUNCH_BUTTON_TIMER_START, msg)


def final_score(args):
    '''
    send shepherd the final score, send score to scoreboard
    '''
    blue_final = args['blue_score']
    gold_final = args['gold_score']
    alliances[ALLIANCE_COLOR.GOLD].score = gold_final
    alliances[ALLIANCE_COLOR.BLUE].score = blue_final
    msg = {"alliance": ALLIANCE_COLOR.GOLD, "amount": gold_final}
    lcm_send(SCOREBOARD_HEADER.SCORE, msg)
    msg = {"alliance": ALLIANCE_COLOR.BLUE, "amount": blue_final}
    lcm_send(SCOREBOARD_HEADER.SCORE, msg)


def overdrive_triggered(args):
    lcm_send(LCM_TARGETS.SCOREBOARD, SCOREBOARD_HEADER.OVERDRIVE_START)
    print("overdrive is active for the next 30 seconds")

###########################################
# Event to Function Mappings for each Stage
###########################################

setup_functions = {
    SHEPHERD_HEADER.SETUP_MATCH: to_setup,
    SHEPHERD_HEADER.GET_MATCH_INFO : get_match,
    SHEPHERD_HEADER.START_NEXT_STAGE: to_perk_selection
}

perk_selection_functions = {
    SHEPHERD_HEADER.RESET_MATCH : reset,
    SHEPHERD_HEADER.APPLY_PERKS: apply_perks,
    SHEPHERD_HEADER.START_NEXT_STAGE: to_auto_wait
}

auto_wait_functions = {
    SHEPHERD_HEADER.RESET_MATCH : reset,
    SHEPHERD_HEADER.SCORE_ADJUST : score_adjust,
    SHEPHERD_HEADER.GET_SCORES : get_score,
    SHEPHERD_HEADER.START_NEXT_STAGE : to_auto
}

auto_functions = {
    SHEPHERD_HEADER.RESET_MATCH : reset,
    SHEPHERD_HEADER.STAGE_TIMER_END : to_wait,
    SHEPHERD_HEADER.LAUNCH_BUTTON_TRIGGERED : auto_launch_button_triggered,
    SHEPHERD_HEADER.CODE_APPLICATION : apply_code,
    SHEPHERD_HEADER.ROBOT_OFF : disable_robot,
    SHEPHERD_HEADER.CODE_RETRIEVAL : bounce_code

    }

wait_functions = {
    SHEPHERD_HEADER.RESET_MATCH : reset,
    SHEPHERD_HEADER.SCORE_ADJUST : score_adjust,
    SHEPHERD_HEADER.GET_SCORES : get_score,
    SHEPHERD_HEADER.START_NEXT_STAGE : to_teleop
}

teleop_functions = {
    SHEPHERD_HEADER.RESET_MATCH : reset,
    SHEPHERD_HEADER.STAGE_TIMER_END : end_teleop,
    SHEPHERD_HEADER.LAUNCH_BUTTON_TRIGGERED : launch_button_triggered,
    SHEPHERD_HEADER.CODE_APPLICATION : apply_code,
    SHEPHERD_HEADER.ROBOT_OFF : disable_robot,
    SHEPHERD_HEADER.END_EXTENDED_TELEOP : to_end,
    SHEPHERD_HEADER.TRIGGER_OVERDRIVE : overdrive_triggered,
    SHEPHERD_HEADER.CODE_RETRIEVAL : bounce_code

}

end_functions = {
    SHEPHERD_HEADER.RESET_MATCH : reset,
    SHEPHERD_HEADER.SCORE_ADJUST : score_adjust,
    SHEPHERD_HEADER.GET_SCORES : get_score,
    SHEPHERD_HEADER.SETUP_MATCH : to_setup,
    SHEPHERD_HEADER.GET_MATCH_INFO : get_match,
    SHEPHERD_HEADER.FINAL_SCORE : final_score
}

###########################################
# Evergreen Variables
###########################################

game_state = STATE.END
game_timer = Timer(TIMER_TYPES.MATCH)
extended_teleop_timer = Timer(TIMER_TYPES.EXTENDED_TELEOP)

match_number = -1
alliances = {ALLIANCE_COLOR.GOLD: None, ALLIANCE_COLOR.BLUE: None}
events = None

###########################################
# Game Specific Variables
###########################################
buttons = {'gold_1': False, 'gold_2': False, 'blue_1': False, 'Blue_2': False}
launch_button_timer_gold_1 = Timer(TIMER_TYPES.EXTENDED_TELEOP)
launch_button_timer_gold_2 = Timer(TIMER_TYPES.EXTENDED_TELEOP)
launch_button_timer_blue_1 = Timer(TIMER_TYPES.EXTENDED_TELEOP)
launch_button_timer_blue_2 = Timer(TIMER_TYPES.EXTENDED_TELEOP)
timer_dictionary = {'gold_1': launch_button_timer_gold_1, 'gold_2': launch_button_timer_gold_2,
             'blue_1': launch_button_timer_blue_1, 'Blue_2': launch_button_timer_blue_2}


overdrive_timer = Timer(TIMER_TYPES.OVERDRIVE_DELAY)
code_solution = {}
code_effect = {}
codes = []
codes_used = []

#nothing


def main():
    parser = argparse.ArgumentParser(description='PiE field control')
    parser.add_argument('--version', help='Prints out the Shepherd version number.',
                        action='store_true')
    flags = parser.parse_args()

    if flags.version:
        print('.'.join(map(str, __version__)))
    else:
        start()



if __name__ == '__main__':
    main()
