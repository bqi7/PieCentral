import fs from 'fs';
import { ipcMain } from 'electron';
import LCM from '../../renderer/utils/lcm_ws_bridge';
import { updateTimer,
        updateHeart,
        updateRobot,
        updateMatch }
        from '../../renderer/actions/FieldActions';
import RendererBridge from '../RendererBridge';

const { app } = require('electron'); // eslint-disable-line global-require

export let stationNumber;
try {
  stationNumber = parseInt(fs.readFileSync(`${app.getPath('Desktop')}/station_number.txt`), 10);
  console.log(`1Station: ${stationNumber}`);
} catch (err) {
  stationNumber = 2;
  console.log(`2Station: ${stationNumber}`);
}

export let bridgeAddress;
try {
  bridgeAddress = fs.readFileSync(`${app.getPath('Desktop')}/bridge_address.txt`);
  console.log(`3Bridge: ${bridgeAddress}`);
} catch (err) {
  bridgeAddress = 'localhost';
  console.log(`4Bridge: ${bridgeAddress}`);
}

class LCMInternals {
  constructor() {
    this.lcm = null;
    this.lcmReady = false;
    this.queuedPublish = null;
    console.log(`Actual Value ${stationNumber}`);
    this.stationNumber = stationNumber;
    this.bridgeAddress = String(bridgeAddress).trim();
    this.init = this.init.bind(this);
    this.quit = this.quit.bind(this);
    this.lcmPublish = this.lcmPublish.bind(this);
    this.updateStatus = this.updateStatus.bind(this);
    // this.changeStationNumber = this.changeStationNumber.bind(this);
    // this.changeBridgeAddress = this.changeBridgeAddress.bind(this);

    ipcMain.on('LCM_STATUS_UPDATE', this.updateStatus);
  }

  init() {
    this.lcm = new LCM(`ws://${this.bridgeAddress}:8000`);
    this.lcm.on_ready(() => {
      this.lcmReady = true;
      if (this.queuedPublish !== null) { // TODO: Why is this here?
        this.lcm.publish(this.queuedPublish[0], this.queuedPublish[1]);
        this.queuedPublish = null;
      }
      this.lcm.subscribe('Timer/Time', 'Time', (msg) => {
        RendererBridge.reduxDispatch(updateTimer(msg));
      });
      this.lcm.subscribe('Heartbeat/Beat', 'Heartbeat', (msg) => {
        RendererBridge.reduxDispatch(updateHeart(msg));
      });
      this.lcm.subscribe(`Robot${this.stationNumber}/RobotControl`, 'RobotControl', (msg) => {
        console.log(msg);
        RendererBridge.reduxDispatch(updateRobot(msg));
      });
      this.lcm.subscribe('Timer/Match', 'Match', (msg) => {
        RendererBridge.reduxDispatch(updateMatch(msg));
      });
    });
    this.lcm.on_close(this.init);
  }

  // TODO: Make clearer protocol on how lights should change
  updateStatus(event, data) {
    const connected = data.connectionStatus;
    const ok = data.runtimeStatus;
    const msg = {
      __type__: 'StatusLight',
      red: false,
      yellow: false,
      green: false,
      buzzer: false,
    };
    if (connected) {
      if (ok) {
        msg.green = true;
      } else {
        msg.red = true;
      }
    } else {
      msg.red = true;
    }
    this.lcmPublish(`StatusLight${stationNumber}/StatusLight`, msg);
  }

  // changeBridgeAddress(newVal) {
  //   this.bridgeAddress = newVal;
  //   bridgeAddress = newVal; // TODO: See if only one needs to be changed
  //   console.log(`Bridge: ${this.bridgeAddress}`);
  //   this.quit();
  //   this.init();
  // }
  //
  // changeStationNumber(newVal) {
  //   this.stationNumber = newVal;
  //   stationNumber = newVal;
  //   console.log(`Station: ${this.bridgeAddress}`);
  //   this.quit();
  //   this.init();
  // }

  lcmPublish(channel, msg) {
    if (this.lcmReady) {
      this.lcm.publish(channel, msg);
    } else {
      console.log('lcm publish queued');
      this.queuedPublish = [channel, msg];
    }
  }

  quit() {
    try {
      this.lcm.ws.close();
    } catch (err) {
      console.log(err);
    }
    this.lcm = null;
  }
}

const LCMObject = {
  LCMInternal: null,
  setup() {
    this.LCMInternal = new LCMInternals();
    this.LCMInternal.init();
  },
};

export default LCMObject;