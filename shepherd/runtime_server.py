import threading
import json
import time
import queue
import gevent # pylint: disable=import-error
from flask import Flask, render_template, request # pylint: disable=import-error
from flask_socketio import SocketIO, emit, join_room, leave_room, send # pylint: disable=import-error
from Utils import *
from LCM import *

HOST_URL = "0.0.0.0"
PORT = 7001

#TODO work on this, new headers and deprecated headers.
#Utils - Runtime Headers, code_retrieval


app = Flask(__name__)
app.config['SECRET_KEY'] = 'omegalul!'
socketio = SocketIO(app)

@socketio.on('join')
def on_join(data):
    join_room(str(request.remote_addr))

@socketio.on(SHEPHERD_HEADER.CODE_RETRIEVAL)
def ui_to_server_setup_match(data):
    team_number = str(request.remote_addr).split('.')[-1]
    data_dict = json.loads(data)
    data_dict['team_number'] = team_number
    lcm_send(LCM_TARGETS.SHEPHERD, SHEPHERD_HEADER.CODE_RETRIEVAL, data_dict)

def receiver():
    events = gevent.queue.Queue()
    lcm_start_read(str.encode(LCM_TARGETS.RUNTIME), events, put_json=True)

    while True:
        if not events.empty():
            event = events.get_nowait()
            eventDict = json.loads(event)
            print("RECEIVED:", event)
            if eventDict["header"] == RUNTIME_HEADER.SPECIFIC_ROBOT_STATE:
                socketio.emit(RUNTIME_HEADER.SPECIFIC_ROBOT_STATE, event, room=('192.168.128.' + str(eventDict[team_number])))
            elif eventDict["header"] == RUNTIME_HEADER.DECODE:
                socketio.emit(RUNTIME_HEADER.DECODE, event, room=('192.168.128.' + str(eventDict[team_number])))
        socketio.sleep(1)

socketio.start_background_task(receiver)
socketio.run(app, host=HOST_URL, port=PORT)
