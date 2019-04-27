import argparse
import queue
import random
import time
from Alliance import *
from LCM import *
from Timer import *
from Utils import *
from Code import *
from audio import *
from runtimeclient import RuntimeClientManager
import Sheet
import bot
import Log

clients = RuntimeClientManager((), ())

__version__ = (1, 0, 0)


###########################################
# Evergreen Methods
###########################################

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
        Log.last_header = payload
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
    global starting_spots

    b1_name, b1_num, b1_starting_spot = args["b1name"], args["b1num"], args["b1_starting_spot"]
    b2_name, b2_num, b2_starting_spot = args["b2name"], args["b2num"], args["b2_starting_spot"]
    g1_name, g1_num, g1_starting_spot = args["g1name"], args["g1num"], args["g1_starting_spot"]
    g2_name, g2_num, g2_starting_spot = args["g2name"], args["g2num"], args["g2_starting_spot"]

    g1_custom_ip = args["g1_custom_ip"] or None
    g2_custom_ip = args["g2_custom_ip"] or None
    b1_custom_ip = args["b1_custom_ip"] or None
    b2_custom_ip = args["b2_custom_ip"] or None

    starting_spots = [b1_starting_spot, b2_starting_spot, g1_starting_spot, g2_starting_spot]

    if game_state == STATE.END:
        flush_scores()

    match_number = args["match_num"]

    if alliances[ALLIANCE_COLOR.BLUE] is not None:
        reset()

    code_setup()

    alliances[ALLIANCE_COLOR.BLUE] = Alliance(ALLIANCE_COLOR.BLUE, b1_name,
                                              b1_num, b2_name, b2_num, b1_custom_ip, b2_custom_ip)
    alliances[ALLIANCE_COLOR.GOLD] = Alliance(ALLIANCE_COLOR.GOLD, g1_name,
                                              g1_num, g2_name, g2_num, g1_custom_ip, g2_custom_ip)

    msg = {"b1num":b1_num, "b2num":           b2_num, "g1num":g1_num, "g2num":g2_num}
    lcm_send(LCM_TARGETS.TABLET, TABLET_HEADER.TEAMS, msg)

    lcm_send(LCM_TARGETS.SCOREBOARD, SCOREBOARD_HEADER.TEAMS, {
        "b1name" : b1_name, "b1num" : b1_num,
        "b2name" : b2_name, "b2num" : b2_num,
        "g1name" : g1_name, "g1num" : g1_num,
        "g2name" : g2_name, "g2num" : g2_num,
        "match_num" : match_number})

    game_state = STATE.SETUP
    lcm_send(LCM_TARGETS.SCOREBOARD, SCOREBOARD_HEADER.STAGE, {"stage": game_state})
    print("ENTERING SETUP STATE")
    print({"blue_score" : alliances[ALLIANCE_COLOR.BLUE].score,
           "gold_score" : alliances[ALLIANCE_COLOR.GOLD].score})


def to_perk_selection(args):
    next_match_info = Sheet.get_match(int(match_number) + 1)
    b1name = next_match_info["b1name"]
    b2name = next_match_info["b2name"]
    g1name = next_match_info["g1name"]
    g2name = next_match_info["g2name"]
    bot.team_names_on_deck(b1name, b2name, g1name, g2name)

    global game_state
    game_timer.start_timer(CONSTANTS.PERK_SELECTION_TIME + 2)
    game_state = STATE.PERK_SELCTION
    lcm_send(LCM_TARGETS.SCOREBOARD, SCOREBOARD_HEADER.STAGE, {"stage": game_state})
    lcm_send(LCM_TARGETS.TABLET, TABLET_HEADER.COLLECT_PERKS)
    lcm_send(LCM_TARGETS.SCOREBOARD, SCOREBOARD_HEADER.STAGE_TIMER_START,
             {"time" : CONSTANTS.PERK_SELECTION_TIME})
    print("ENTERING PERK SELECTION STATE")
    play_perk_music()

def to_auto_wait(args):
    global game_state
    game_state = STATE.AUTO_WAIT
    lcm_send(LCM_TARGETS.SCOREBOARD, SCOREBOARD_HEADER.STAGE, {"stage": game_state})
    lcm_send(LCM_TARGETS.TABLET, TABLET_HEADER.COLLECT_CODES)
    print("ENTERING AUTO_WAIT STATE")

def to_auto(args):
    '''
    Move to the autonomous stage where robots should begin autonomously.
    By the end, should be in autonomous state, allowing any function from this
    stage to be called and autonomous match timer should have begun.
    '''
    global game_state
    global clients
    try:
        alternate_connections = (alliances[ALLIANCE_COLOR.BLUE].team_1_custom_ip,
                             alliances[ALLIANCE_COLOR.BLUE].team_2_custom_ip,
                             alliances[ALLIANCE_COLOR.GOLD].team_1_custom_ip,
                             alliances[ALLIANCE_COLOR.GOLD].team_2_custom_ip)

        clients = RuntimeClientManager((
            int(alliances[ALLIANCE_COLOR.BLUE].team_1_number),
            int(alliances[ALLIANCE_COLOR.BLUE].team_2_number),
        ), (
            int(alliances[ALLIANCE_COLOR.GOLD].team_1_number),
            int(alliances[ALLIANCE_COLOR.GOLD].team_2_number),
        ),*alternate_connections)
        clients.set_master_robots(master_robots[ALLIANCE_COLOR.BLUE],
                                master_robots[ALLIANCE_COLOR.GOLD])
        clients.set_starting_zones(starting_spots)
    except Exception as exc:
        Log.log(exc)
        return
    game_timer.start_timer(CONSTANTS.AUTO_TIME + 2)
    game_state = STATE.AUTO
    lcm_send(LCM_TARGETS.SCOREBOARD, SCOREBOARD_HEADER.STAGE, {"stage": game_state})
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
    lcm_send(LCM_TARGETS.SCOREBOARD, SCOREBOARD_HEADER.STAGE, {"stage": game_state})
    disable_robots()
    print("ENTERING WAIT STATE")

def to_teleop(args):
    '''
    Move to teleoperated stage where robots are enabled and controlled manually.
    By the end, should be in teleop state and the teleop match timer should be started.
    '''
    global game_state
    game_state = STATE.TELEOP
    lcm_send(LCM_TARGETS.SCOREBOARD, SCOREBOARD_HEADER.STAGE, {"stage": game_state})

    Timer.reset_all()
    game_timer.start_timer(CONSTANTS.TELEOP_TIME + 2)
    overdrive_time = random.randint(0,CONSTANTS.TELEOP_TIME -
                                      CONSTANTS.OVERDRIVE_TIME)
    overdrive_timer.start_timer(overdrive_time)
    overdrive_time = CONSTANTS.TELEOP_TIME - overdrive_time
    print("overdrive will happen at " + str(overdrive_time // 60) + ":" +
          str(overdrive_time % 60))

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
    lcm_send(LCM_TARGETS.SCOREBOARD, SCOREBOARD_HEADER.STAGE, {"stage": game_state})
    disable_robots()
    print("ENTERING END STATE")

def reset(args=None):
    '''
    Resets the current match, moving back to the setup stage but with the current teams loaded in.
    Should reset all state being tracked by Shepherd.
    ****THIS METHOD MIGHT NEED UPDATING EVERY YEAR BUT SHOULD ALWAYS EXIST****
    '''
    global game_state, events, clients
    game_state = STATE.SETUP
    Timer.reset_all()
    events = queue.Queue()
    lcm_start_read(LCM_TARGETS.SHEPHERD, events)
    lcm_send(LCM_TARGETS.SCOREBOARD, SCOREBOARD_HEADER.RESET_TIMERS)
    for alliance in alliances.values():
        if alliance is not None:
            alliance.reset()
    send_connections(None)
    starting_spots = ["unknown","unknown","unknown","unknown"]
    clients = RuntimeClientManager((), ())
    disable_robots()
    buttons['gold_1'] = False
    buttons['gold_2'] = False
    buttons['blue_1'] = False
    buttons['blue_2'] = False
    lcm_send(LCM_TARGETS.TABLET, TABLET_HEADER.RESET)
    lcm_send(LCM_TARGETS.DAWN,DAWN_HEADER.RESET)
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
    try:
        clients.set_mode("auto" if autonomous else "teleop")
    except Exception as exc:
        for client in clients.clients:
            try:
                client.set_mode("auto" if autonomous else "teleop")
            except Exception as exc:
                print("A robot failed to be enabled! Big sad :(")
                Log.log(exc)

def disable_robots():
    '''
    Sends message to Dawn to disable all robots
    '''
    try:
        clients.set_mode("idle")
    except Exception as exc:
        for client in clients.clients:
            try:
                client.set_mode("idle")
            except:
                print("a client has disconnected")
        Log.log(exc)
        print(exc)


###########################################
# Game Specific Methods
###########################################
def disable_robot(args):
    '''
    Send message to Dawn to disable the robots of team
    '''
    try:
        team_number = args["team_number"]
        client = clients.clients[int(team_number)]
        if client:
            client.set_mode("idle")
    except Exception as exc:
        Log.log(exc)


def set_master_robot(args):
    '''
    Set the master robot of the alliance
    '''
    alliance = args["alliance"]
    team_number = args["team_num"]
    master_robots[alliance] = team_number
    msg = {"alliance": alliance, "team_number": int(team_number)}
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
    Set up code_solution and code_effect dictionaries and send code_solution to Dawn
    '''
    global code_solution
    global code_effect
    code_solution = assign_code_solution()
    code_effect = assign_code_effect()

def bounce_code(args):
    try:
        student_solutions = clients.get_challenge_solutions()
        print(student_solutions)
        for ss in student_solutions.keys():
            if student_solutions[ss] != None:
                alliance = None
                if int(alliances[ALLIANCE_COLOR.BLUE].team_1_number) == int(ss):
                    alliance = ALLIANCE_COLOR.BLUE
                if int(alliances[ALLIANCE_COLOR.GOLD].team_1_number) == int(ss):
                    alliance = ALLIANCE_COLOR.GOLD
                if int(alliances[ALLIANCE_COLOR.BLUE].team_2_number) == int(ss):
                    alliance = ALLIANCE_COLOR.BLUE
                if int(alliances[ALLIANCE_COLOR.GOLD].team_2_number) == int(ss):
                    alliance = ALLIANCE_COLOR.GOLD
                msg = {"alliance": alliance, "result": student_solutions[ss]}
                lcm_send(LCM_TARGETS.TABLET, TABLET_HEADER.CODE, msg)
    except Exception as exc:
        Log.log(exc)

def auto_apply_code(args):
    '''
    Send Scoreboard the effect if the answer is correct
    '''
    alliance = alliances[args["alliance"]]
    answer = int(args["answer"])
    print('Codegen answers:', answer, code_solution)
    if (answer is not None and answer in code_solution.values()):
        code = [k for k, v in code_solution.items() if v == answer][0]
        alliance.change_score(10)
    else:
        msg = {"alliance": alliance.name}
        lcm_send(LCM_TARGETS.SENSORS, SENSORS_HEADER.FAILED_POWERUP, msg)

def apply_code(args):
    '''
    Send Scoreboard the new score if the answer is correct #TODO
    '''
    alliance = alliances[args["alliance"]]
    answer = int(args["answer"])
    if (answer is not None and answer in code_solution.values()):
        code = [k for k, v in code_solution.items() if v == answer][0]
        if code_effect[code] == EFFECTS.TWIST:
            if alliance.name == ALLIANCE_COLOR.BLUE:
                msg = {"alliance": ALLIANCE_COLOR.GOLD, "effect": code_effect[code]}
            else:
                msg = {"alliance": ALLIANCE_COLOR.BLUE, "effect": code_effect[code]}
        else:
            msg = {"alliance": alliance.name, "effect": code_effect[code]}
        lcm_send(LCM_TARGETS.SCOREBOARD, SCOREBOARD_HEADER.APPLIED_EFFECT, msg)
    else:
        msg = {"alliance": alliance.name}
        lcm_send(LCM_TARGETS.SENSORS, SENSORS_HEADER.FAILED_POWERUP, msg)


def end_teleop(args):
    blue_robots_disabled = False
    gold_robots_disabled = False
    if PERKS.TAFFY not in alliance_perks(alliances[ALLIANCE_COLOR.BLUE]):
        blue_robots_disabled = True
    if PERKS.TAFFY not in alliance_perks(alliances[ALLIANCE_COLOR.GOLD]):
        gold_robots_disabled = True
    if PERKS.TAFFY in alliance_perks(alliances[ALLIANCE_COLOR.BLUE]) or PERKS.TAFFY in alliance_perks(alliances[ALLIANCE_COLOR.GOLD]):
        extended_teleop_timer.start_timer(CONSTANTS.TAFFY_TIME)
        lcm_send(LCM_TARGETS.SCOREBOARD, SCOREBOARD_HEADER.STAGE_TIMER_START,
                 {"time" : CONSTANTS.TAFFY_TIME})
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
    alliance = alliances[args['alliance']]
    alliance.perk_1 = args['perk_1']
    alliance.perk_2 = args['perk_2']
    alliance.perk_3 = args['perk_3']
    msg = {"alliance": args['alliance'], "perk_1":args['perk_1'], "perk_2":args['perk_2'], "perk_3":args['perk_3']}
    lcm_send(LCM_TARGETS.SCOREBOARD, SCOREBOARD_HEADER.PERKS_SELECTED, msg)

def launch_button_triggered(args):
    '''
    check if allowed once every 30 seconds, give one of the codes to the correct alliance through Dawn,
    update scoreboard
    '''
    try:
        alliance = alliances[args['alliance']]
        button = args["button"]
        lb = alliance.name + "_" + str(button)
        if not timer_dictionary[lb].is_running():
            msg = {"alliance": alliance.name, "button": button}
            code = next_code()
            client = clients.clients[int(master_robots[alliance.name])]
            if client:
                client.run_challenge(code)
            student_decode_timer.start_timer(CONSTANTS.STUDENT_DECODE_TIME)
            timer_dictionary[lb].start_timer(CONSTANTS.COOLDOWN)
            lcm_send(LCM_TARGETS.SCOREBOARD, SCOREBOARD_HEADER.LAUNCH_BUTTON_TIMER_START, msg)
    except Exception as exc:
        Log.log(exc)

def auto_launch_button_triggered(args):
    ##  mark button as dirty, sent to sc (both things)
    ## Isn't this already done in auto_apply_code?
    try:
        alliance = alliances[args['alliance']]
        button = args["button"]
        temp_str = alliance.name + "_" + str(button)
        if not buttons[temp_str]:
            msg = {"alliance": alliance.name, "button": button}
            code = next_code()
            client = clients.clients[int(master_robots[alliance.name])]
            if client:
                client.run_challenge(code, timeout=1)

            student_decode_timer.start_timer(CONSTANTS.STUDENT_DECODE_TIME)
            buttons[temp_str] = True
            msg = {"alliance": alliance.name, "button": button}
            lcm_send(LCM_TARGETS.SCOREBOARD, SCOREBOARD_HEADER.LAUNCH_BUTTON_TIMER_START, msg)
    except Exception as exc:
        Log.log(exc)


def final_score(args):
    '''
    send shepherd the final score, send score to scoreboard
    '''
    blue_final = args['blue_score']
    gold_final = args['gold_score']
    alliances[ALLIANCE_COLOR.GOLD].score = gold_final
    alliances[ALLIANCE_COLOR.BLUE].score = blue_final
    msg = {"alliance": ALLIANCE_COLOR.GOLD, "amount": gold_final}
    lcm_send(LCM_TARGETS.SCOREBOARD, SCOREBOARD_HEADER.SCORE, msg)
    msg = {"alliance": ALLIANCE_COLOR.BLUE, "amount": blue_final}
    lcm_send(LCM_TARGETS.SCOREBOARD, SCOREBOARD_HEADER.SCORE, msg)


def overdrive_triggered(args):
    size = random.choice(CONSTANTS.CRATE_SIZES)
    msg = {"size": size}
    lcm_send(LCM_TARGETS.SCOREBOARD, SCOREBOARD_HEADER.OVERDRIVE_START,msg)
    print("overdrive is active for the next 30 seconds for "+size+" size crates.")
    play_horn()

def set_connections(args):
    team = args["team_number"]
    connection = boolean(args["connection"])
    dirty = False
    for alliance in alliances.values:
        if team == alliance.team_1_number:
            if alliance.team_1_connection != connection:
                alliance.team_1_connection = connection
                dirty = True
        if team == alliance.team_2_number:
            if alliance.team_2_connection != connection:
                alliance.team_2_connection = connection
                dirty = True
    if dirty:
        send_connections(None)

def send_connections(args):
    msg = {"g_1_connection" : alliances[ALLIANCE_COLOR.GOLD].team_1_connection,
           "g_2_connection" : alliances[ALLIANCE_COLOR.GOLD].team_2_connection,
           "b_1_connection" : alliances[ALLIANCE_COLOR.BLUE].team_1_connection,
           "b_2_connection" : alliances[ALLIANCE_COLOR.BLUE].team_2_connection}
    lcm_send(LCM_TARGETS.UI, UI_HEADER.CONNECTIONS, msg)

###########################################
# Event to Function Mappings for each Stage
###########################################

setup_functions = {
    SHEPHERD_HEADER.SETUP_MATCH: to_setup,
    SHEPHERD_HEADER.SCORE_ADJUST : score_adjust,
    SHEPHERD_HEADER.GET_MATCH_INFO : get_match,
    SHEPHERD_HEADER.START_NEXT_STAGE: to_perk_selection,
    SHEPHERD_HEADER.ROBOT_CONNECTION_STATUS: set_connections,
    SHEPHERD_HEADER.REQUEST_CONNECTIONS: send_connections
}

perk_selection_functions = {
    SHEPHERD_HEADER.RESET_MATCH : reset,
    SHEPHERD_HEADER.APPLY_PERKS: apply_perks,
    SHEPHERD_HEADER.MASTER_ROBOT: set_master_robot,
    SHEPHERD_HEADER.STAGE_TIMER_END: to_auto_wait,
    SHEPHERD_HEADER.ROBOT_CONNECTION_STATUS: set_connections,
    SHEPHERD_HEADER.REQUEST_CONNECTIONS: send_connections
}

auto_wait_functions = {
    SHEPHERD_HEADER.RESET_MATCH : reset,
    SHEPHERD_HEADER.SCORE_ADJUST : score_adjust,
    SHEPHERD_HEADER.APPLY_PERKS: apply_perks,
    SHEPHERD_HEADER.MASTER_ROBOT: set_master_robot,
    SHEPHERD_HEADER.CODE_APPLICATION : auto_apply_code,
    SHEPHERD_HEADER.GET_SCORES : get_score,
    SHEPHERD_HEADER.START_NEXT_STAGE : to_auto,
    SHEPHERD_HEADER.ROBOT_CONNECTION_STATUS: set_connections,
    SHEPHERD_HEADER.REQUEST_CONNECTIONS: send_connections
}

auto_functions = {
    SHEPHERD_HEADER.RESET_MATCH : reset,
    SHEPHERD_HEADER.STAGE_TIMER_END : to_wait,
    SHEPHERD_HEADER.LAUNCH_BUTTON_TRIGGERED : auto_launch_button_triggered,
    SHEPHERD_HEADER.CODE_APPLICATION : auto_apply_code,
    SHEPHERD_HEADER.ROBOT_OFF : disable_robot,
    SHEPHERD_HEADER.CODE_RETRIEVAL : bounce_code,
    SHEPHERD_HEADER.ROBOT_CONNECTION_STATUS: set_connections,
    SHEPHERD_HEADER.REQUEST_CONNECTIONS: send_connections

    }

wait_functions = {
    SHEPHERD_HEADER.RESET_MATCH : reset,
    SHEPHERD_HEADER.SCORE_ADJUST : score_adjust,
    SHEPHERD_HEADER.GET_SCORES : get_score,
    SHEPHERD_HEADER.START_NEXT_STAGE : to_teleop,
    SHEPHERD_HEADER.ROBOT_CONNECTION_STATUS: set_connections,
    SHEPHERD_HEADER.REQUEST_CONNECTIONS: send_connections
}

teleop_functions = {
    SHEPHERD_HEADER.RESET_MATCH : reset,
    SHEPHERD_HEADER.STAGE_TIMER_END : end_teleop,
    SHEPHERD_HEADER.LAUNCH_BUTTON_TRIGGERED : launch_button_triggered,
    SHEPHERD_HEADER.CODE_APPLICATION : apply_code,
    SHEPHERD_HEADER.ROBOT_OFF : disable_robot,
    SHEPHERD_HEADER.END_EXTENDED_TELEOP : to_end,
    SHEPHERD_HEADER.TRIGGER_OVERDRIVE : overdrive_triggered,
    SHEPHERD_HEADER.CODE_RETRIEVAL : bounce_code,
    SHEPHERD_HEADER.ROBOT_CONNECTION_STATUS: set_connections,
    SHEPHERD_HEADER.REQUEST_CONNECTIONS: send_connections

}

end_functions = {
    SHEPHERD_HEADER.RESET_MATCH : reset,
    SHEPHERD_HEADER.SCORE_ADJUST : score_adjust,
    SHEPHERD_HEADER.GET_SCORES : get_score,
    SHEPHERD_HEADER.SETUP_MATCH : to_setup,
    SHEPHERD_HEADER.GET_MATCH_INFO : get_match,
    SHEPHERD_HEADER.FINAL_SCORE : final_score,
    SHEPHERD_HEADER.ROBOT_CONNECTION_STATUS: set_connections,
    SHEPHERD_HEADER.REQUEST_CONNECTIONS: send_connections
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
buttons = {'gold_1': False, 'gold_2': False, 'blue_1': False, 'blue_2': False}
starting_spots = ["unknown","unknown","unknown","unknown"]
launch_button_timer_gold_1 = Timer(TIMER_TYPES.LAUNCH_BUTTON)
launch_button_timer_gold_2 = Timer(TIMER_TYPES.LAUNCH_BUTTON)
launch_button_timer_blue_1 = Timer(TIMER_TYPES.LAUNCH_BUTTON)
launch_button_timer_blue_2 = Timer(TIMER_TYPES.LAUNCH_BUTTON)
timer_dictionary = {'gold_1': launch_button_timer_gold_1, 'gold_2': launch_button_timer_gold_2,
             'blue_1': launch_button_timer_blue_1, 'blue_2': launch_button_timer_blue_2}
master_robots = {ALLIANCE_COLOR.BLUE: None, ALLIANCE_COLOR.GOLD: None}

student_decode_timer = Timer(TIMER_TYPES.STUDENT_DECODE)

overdrive_timer = Timer(TIMER_TYPES.OVERDRIVE_DELAY)
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
