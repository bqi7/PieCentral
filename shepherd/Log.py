import Shepherd
import datetime
from Utils import *

last_header = None

def log(Exception):
    global last_header
    if Shepherd.match_number <= 0:
        return
    now = datetime.datetime.now()
    filename = now.month + "-" + now.day + "-" + now.year + "-match-"+Shepherd.match_number+".txt"
    file = open("logs/"+filename, "a+")
    file.write("========================================")
    file.write("a normaly fatal exception occured.")
    file.write("all relevant data may be found below.")
    file.write("match: " + Shepherd.match_number)
    file.write("game state: " + Shepherd.game_state)
    file.write("gold alliance: " + Shepherd.alliances[CONSTANTS.GOLD])
    file.write("blue alliance: " + Shepherd.alliances[CONSTANTS.BLUE])
    file.write("game timer running?: " + Shepherd.game_timer.is_running())
    file.write("extended teleop timer running?: " + Shepherd.extended_teleop_timer.is_running())
    file.write("launch button timers running(g1 g2 b1 b2)?: " +
               Shepherd.launch_button_timer_gold_1.is_running() + " " + Shepherd.launch_button_timer_gold_2.is_running() + " " +
               Shepherd.launch_button_timer_blue_1.is_running() + " " + Shepherd.launch_button_timer_blue_2.is_running())
    file.write("overdrive timer active?: " + Shepherd.overdrive_timer.is_running())
    file.write("the last received header was:" + last_header)
    file.write("a stacktrace of the error may be found below.")
    file.write(Exception)
    file.close()
