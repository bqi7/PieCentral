import Shepherd
import datetime
from Utils import *

last_header = None

def log(Exception):
    global last_header
    # if Shepherd.match_number <= 0:
    #     return
    now = datetime.datetime.now()
    filename = str(now.month) + "-" + str(now.day) + "-" + str(now.year) + "-match-"+ str(Shepherd.match_number) +".txt"
    print("a normally fatal exception occured, but Shepherd will continue to run")
    print("all known details are logged to logs/"+filename)
    file = open("logs/"+filename, "a+")
    file.write("========================================")
    file.write("a normally fatal exception occured.")
    file.write("all relevant data may be found below.")
    file.write("match: " + str(Shepherd.match_number))
    file.write("game state: " + str(Shepherd.game_state))
    file.write("gold alliance: " + str(Shepherd.alliances[CONSTANTS.GOLD]))
    file.write("blue alliance: " + str(Shepherd.alliances[CONSTANTS.BLUE]))
    file.write("game timer running?: " + str(Shepherd.game_timer.is_running()))
    file.write("extended teleop timer running?: " + str(Shepherd.extended_teleop_timer.is_running()))
    file.write("launch button timers running(g1 g2 b1 b2)?: " +
               str(Shepherd.launch_button_timer_gold_1.is_running()) + " " + str(Shepherd.launch_button_timer_gold_2.is_running()) + " " +
               str(Shepherd.launch_button_timer_blue_1.is_running()) + " " + str(Shepherd.launch_button_timer_blue_2.is_running()))
    file.write("overdrive timer active?: " + str(Shepherd.overdrive_timer.is_running()))
    file.write("the last received header was:" + str(last_header))
    file.write("a stacktrace of the error may be found below.")
    file.write(str(Exception))
    file.close()
