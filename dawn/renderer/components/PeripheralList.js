import React from 'react';
import _ from 'lodash';
import { Panel, Accordion, ListGroup } from 'react-bootstrap';
import { PeripheralTypes } from '../constants/Constants';
import Peripheral from './Peripheral';

const cleanerNames = {};
cleanerNames[PeripheralTypes.MOTOR_SCALAR] = 'Motors';
cleanerNames[PeripheralTypes.SENSOR_BOOLEAN] = 'Boolean Sensors';
cleanerNames[PeripheralTypes.SENSOR_SCALAR] = 'Numerical Sensors';
cleanerNames[PeripheralTypes.LimitSwitch] = 'Limit Switches';
cleanerNames[PeripheralTypes.LineFollower] = 'Line Followers';
cleanerNames[PeripheralTypes.Potentiometer] = 'Potentiometers';
cleanerNames[PeripheralTypes.Encoder] = 'Encoders';
// cleanerNames[PeripheralTypes.ColorSensor] = 'Color Sensors';
cleanerNames[PeripheralTypes.MetalDetector] = 'Metal Detectors';
cleanerNames[PeripheralTypes.ServoControl] = 'Servo Controllers';


const handleAccordion = (array) => {
  const peripheralGroups = {};
  array.forEach((p) => {
    if (!(p.device_type in peripheralGroups)) {
      peripheralGroups[p.device_type] = [];
    }
    peripheralGroups[p.device_type].push(p);
  });
  return (
      _.map(Object.keys(peripheralGroups), groups => (
        <Accordion style={{ marginBottom: '2px' }} key={`${cleanerNames[groups] || 'Default'}-Accordion`}>
          <Panel header={cleanerNames[groups] || 'Generic'} key={`${cleanerNames[groups] || 'Default'}-Panel`}>
            {
              _.map(peripheralGroups[groups], peripheral => (
                <Peripheral
                  key={String(peripheral.uid.high) + String(peripheral.uid.low)}
                  id={String(peripheral.uid.high) + String(peripheral.uid.low)}
                  device_name={peripheral.device_name}
                  device_type={peripheral.device_type}
                  param={peripheral.param_value}
                />
              ))
            }
          </Panel>
        </Accordion>
      ))
  );
};


const PeripheralList = (props) => {
  let errorMsg = null;
  if (!props.connectionStatus) {
    errorMsg = 'You are currently disconnected from the robot.';
  } else if (!props.runtimeStatus) {
    errorMsg = 'There appears to be some sort of Runtime error. ' +
      'No data is being received.';
  }
  return (
    <Panel
      id="peripherals-panel"
      header="Peripherals"
      bsStyle="primary"
    >
      <ListGroup fill style={{ marginBottom: '5px' }}>
        {
          !errorMsg ? handleAccordion(
            _.sortBy(_.toArray(props.peripherals), ['device_type', 'device_name']))
          : <p className="panelText">{errorMsg}</p>
        }
      </ListGroup>
    </Panel>
  );
};

PeripheralList.propTypes = {
  connectionStatus: React.PropTypes.bool,
  runtimeStatus: React.PropTypes.bool,
  peripherals: React.PropTypes.object,
};

export default PeripheralList;
