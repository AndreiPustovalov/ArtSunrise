import logging
import sys
import traceback
from LightControl import LightControl

logger = logging.getLogger('ArtSunrise')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler(sys.stdout)
logger.addHandler(ch)


def main():
    dev = LightControl({'port': 'COM4'})
    while True:
        try:
            l = sys.stdin.readline().strip()
            if l == '':
                break
            elif l == 'get':
                print(dev.get_active())
            else:
                c, w = l.split()
                dev.set_light(int(c), int(w))
        except:
            traceback.print_exc()

if __name__ == '__main__':
    exit(main())
