# pylint: disable=invalid-name
class SHEPHERD_HEADER():
    START_NEXT_STAGE = "start_next_stage"
    RESET_CURRENT_STAGE = "reset_current_stage"
    RESET_MATCH = "reset_match"

    GET_MATCH_INFO = "get_match_info"
    SETUP_MATCH = "setup_match"

    STOP_ROBOT = "stop_robot"

    GET_SCORES = "get_scores"
    SCORE_ADJUST = "score_adjust"

    STAGE_TIMER_END = "stage_timer_end"

    ROBOT_OFF = "robot_off"

    END_EXTENDED_TELEOP = "end_extended_teleop"

    LAUNCH_BUTTON_TRIGGERED = "launch_button_triggered"
    CODE_APPLICATION = "code_application"

    APPLY_PERKS = "apply_perks"
    MASTER_ROBOT = "master_robot"

    FINAL_SCORE = "final_score"
    ASSIGN_TEAMS = "assign_teams"
        # ASSIGN_TEAMS{g1num, g2num, b1num, b2num}
    TEAM_RETRIEVAL = "team_retrieval"
        # TEAM_RETRIEVAL{}
    TRIGGER_OVERDRIVE = "trigger_overdrive"
        #TRIGGER_OVERDRIVE{}

# pylint: disable=invalid-name
class SENSORS_HEADER():
    FAILED_POWERUP = "failed_powerup"

# pylint: disable=invalid-name
class DAWN_HEADER():

    IP_ADDRESS = "ip_address"
    #TODO this^

class RUNTIME_HEADER():
    SPECIFIC_ROBOT_STATE = "specific_robot_state"
        # SPECIFIC_ROBOT_STATE{team_number, autonomous, enabled}
        # robot ip is 192.168.128.teamnumber
    DECODE = "decode"
        # DECODE{alliance, seed}

# pylint: disable=invalid-name
class UI_HEADER():
    TEAMS_INFO = "teams_info"
    SCORES = "scores"

# pylint: disable=invalid-name
class SCOREBOARD_HEADER():
    SCORE = "score"
    TEAMS = "teams"
    STAGE = "stage"
    STAGE_TIMER_START = "stage_timer_start"
    RESET_TIMERS = "reset_timers"
    ALL_INFO = "all_info"

    LAUNCH_BUTTON_TIMER_START = "launch_button_timer_start"
        # LAUNCH_BUTTON_TIMER_START{alliance, button}
    PERKS_SELECTED = "perks_selected"
        # PERKS_SELECTED{alliance, perk_1, perk_2, perk_3}
    APPLIED_EFFECT = "applied_effect"
        # APPLIED_EFFECT{alliance, effect}
    OVERDRIVE_START = "overdrive_start"
        #OVERDRIVE_START{}

class TABLET_HEADER():
    TEAMS = "teams"
    #{b1num, b2num, g1num, g2num}
    CODE = "code"
    #{alliance, code}
    COLLECT_PERKS = "collect_perks"
    #{}
    COLLECT_CODES = "collect_codes"
    #{}
    RESET = "reset"
    #{}

# pylint: disable=invalid-name
class CONSTANTS():
    PERK_SELECTION_TIME = 30
    AUTO_TIME = 30
    TELEOP_TIME = 180
    OVERDRIVE_TIME = 30
    SPREADSHEET_ID = "1F_fRPZ2Whe3f8ssniqh1uWFfc8dU8LfElY51R4EtJDY"
    CSV_FILE_NAME = "Sheets/schedule.csv"
    TAFFY_TIME = 15
    TWIST_CHANCE = .3 #a value 0<x<1

# pylint: disable=invalid-name
class ALLIANCE_COLOR():
    GOLD = "gold"
    BLUE = "blue"

# pylint: disable=invalid-name
class LCM_TARGETS():
    SHEPHERD = "lcm_target_shepherd"
    SCOREBOARD = "lcm_target_scoreboard"
    SENSORS = "lcm_target_sensors"
    UI = "lcm_target_ui"
    DAWN = "lcm_target_dawn"
    RUNTIME = "lcm_target_runtime"

# pylint: disable=invalid-name
class TIMER_TYPES():
    MATCH = {"TYPE":"match", "NEEDS_FUNCTION": True, "FUNCTION":SHEPHERD_HEADER.STAGE_TIMER_END}
    EXTENDED_TELEOP = {"TYPE":"extended_teleop", "NEEDS_FUNCTION": True, "FUNCTION":SHEPHERD_HEADER.END_EXTENDED_TELEOP}
    OVERDRIVE_DELAY = {"TYPE":"overdrive_delay", "NEEDS_FUNCTION": True, "FUNCTION":SHEPHERD_HEADER.TRIGGER_OVERDRIVE}#TODO
    LAUNCH_BUTTON = {"TYPE":"extended_teleop", "NEEDS_FUNCTION": False}

# pylint: disable=invalid-name
class STATE():
    SETUP = "setup"
    PERK_SELCTION = "perk_selection"
    AUTO = "auto"
    WAIT = "wait"
    TELEOP = "teleop"
    END = "end"

class EFFECTS():
    TWIST = "twist"
    SPOILED_CANDY = "spoiled_candy"

class PERKS():
    EMPTY = "empty"
    BUBBLEGUM = "bubblegum"
    DIET = "diet"
    SWEET_SPOT = "sweet_spot"
    TAFFY = "taffy"
    CHOCOLATE_COVERED_ESPRESSO_BEANS = "chocolate_covered_espresso_beans"
    MINTY_FRESH_START = "minty_fresh_start"
    RASPBERRY_COTTON_CANDY = "raspberry_cotton_candy"
    ARTIFICIAL_SWEETENER = "artificial"
    JAWBREAKER = "jawbreaker"
    SOUR_GUMMY_WORMS = "sour_gummy_worms"
    # To be continued TODO
