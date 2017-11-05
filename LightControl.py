import serial
import logging
import binascii

logger = logging.getLogger('ArtSunrise.device')


class LightControl:
    CMD_GET_ACTIVE = 1
    CMD_SET = 2

    def __init__(self, app_config):
        self.port = app_config('port')
        self.com = serial.Serial(
            port=self.port,
            baudrate=250000,
            bytesize=serial.EIGHTBITS,
            stopbits=serial.STOPBITS_TWO,
            parity=serial.PARITY_MARK,
            rtscts=False,
            dsrdtr=False,
            timeout=0.5,
            write_timeout=1,
        )

    def set_light(self, warm, cold):
        msg = bytes([LightControl.CMD_SET, warm, cold])
        logger.info('Request: {}'.format(binascii.hexlify(msg)))
        self.com.write(msg)
        ans = self.com.read(8)
        logger.info('Answer: {}'.format(binascii.hexlify(ans)))
        assert ans == bytes([LightControl.CMD_SET, 0]), 'Wrong answer'

    def get_active(self):
        msg = bytes([LightControl.CMD_GET_ACTIVE])
        logger.info('Request: {}'.format(binascii.hexlify(msg)))
        self.com.write(msg)
        ans = self.com.read(8)
        logger.info('Answer: {}'.format(binascii.hexlify(ans)))
        return ans[1]
