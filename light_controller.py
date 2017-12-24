import serial
import logging
import binascii
import json

logger = logging.getLogger('ArtSunrise.device')


def load_config(name='config.json'):
    return json.load(open(name))


class LightControl:
    CMD_GET_ACTIVE = 2
    CMD_SET = 1

    def __init__(self, app_config=None):
        if app_config is None:
            self.app_config = load_config()
        self.port = self.app_config['port']
        self.com = serial.Serial(
            port=self.port,
            baudrate=9600,
            bytesize=serial.EIGHTBITS,
            stopbits=serial.STOPBITS_ONE,
            # parity=serial.PARITY_MARK,
            rtscts=False,
            dsrdtr=False,
            timeout=0.5,
            inter_byte_timeout=0.1,
            write_timeout=1,
        )

    def set_light(self, cold, warm):
        msg = bytes([LightControl.CMD_SET, cold, warm, 0])
        logger.info('Request: {}'.format(binascii.hexlify(msg)))
        self.com.write(msg)
        ans = self.com.read(8)
        logger.info('Answer: {}'.format(binascii.hexlify(ans)))
        assert ans == bytes([LightControl.CMD_SET, 0]), 'Wrong answer'

    def get_active(self):
        msg = bytes([LightControl.CMD_GET_ACTIVE, 0])
        logger.info('Request: {}'.format(binascii.hexlify(msg)))
        self.com.write(msg)
        ans = self.com.read(8)
        logger.info('Answer: {}'.format(binascii.hexlify(ans)))
        return ans[2]


def init(port='/dev/ttyUSB0'):
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    return LightControl({'port': port})
