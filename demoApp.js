// tennis_ball_machine.js

const bleno = require('bleno');
const BlenoCharacteristic = bleno.Characteristic;

const MOTOR_SERVICE_UUID = 'ff00';
const SERVO_CHAR_UUID = 'fff1';
const DC_MOTOR1_CHAR_UUID = 'fff2';
const DC_MOTOR2_CHAR_UUID = 'fff3';

class MotorCharacteristic extends BlenoCharacteristic {
  constructor(uuid, name) {
    super({
      uuid: uuid,
      properties: ['write'],
      descriptors: [
        new bleno.Descriptor({
          uuid: '2901',
          value: name
        })
      ]
    });
    this.name = name;
  }

  onWriteRequest(data, offset, withoutResponse, callback) {
    const speed = data.readInt8(0);
    console.log(`${this.name} speed set to ${speed}`);
    callback(this.RESULT_SUCCESS);
  }
}

const servoCharacteristic = new MotorCharacteristic(SERVO_CHAR_UUID, 'Servo Motor');
const dcMotor1Characteristic = new MotorCharacteristic(DC_MOTOR1_CHAR_UUID, 'DC Motor 1');
const dcMotor2Characteristic = new MotorCharacteristic(DC_MOTOR2_CHAR_UUID, 'DC Motor 2');

const motorService = new bleno.PrimaryService({
  uuid: MOTOR_SERVICE_UUID,
  characteristics: [
    servoCharacteristic,
    dcMotor1Characteristic,
    dcMotor2Characteristic
  ]
});

bleno.on('stateChange', (state) => {
  console.log(`BLE State changed to ${state}`);
  if (state === 'poweredOn') {
    bleno.startAdvertising('TennisBallMachine', [MOTOR_SERVICE_UUID], (err) => {
      if (err) {
        console.error(`Advertising start error: ${err}`);
      } else {
        console.log('Advertising started...');
      }
    });
  } else {
    bleno.stopAdvertising();
    console.log('Advertising stopped');
  }
});

bleno.on('advertisingStart', (error) => {
  if (!error) {
    console.log('Setting up services...');
    bleno.setServices([motorService], (err) => {
      if (err) {
        console.error(`Set services error: ${err}`);
      } else {
        console.log('Services set successfully');
      }
    });
  } else {
    console.error(`Advertising start error: ${error}`);
  }
});

bleno.on('accept', (clientAddress) => {
  console.log(`Accepted connection from address: ${clientAddress}`);
});

bleno.on('disconnect', (clientAddress) => {
  console.log(`Disconnected from address: ${clientAddress}`);
});

process.on('SIGINT', () => {
  bleno.stopAdvertising();
  bleno.disconnect();
  console.log('\nBLE Peripheral terminated');
  process.exit(0);
});
