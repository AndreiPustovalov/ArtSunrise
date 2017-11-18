import logging
import sys
import traceback
from LightControl import LightControl

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('ArtSunrise')


def main():
    dev = LightControl({'port': 'COM5'})
    while True:
        try:
            l = sys.stdin.readline().strip()
            if l == '':
                break
            elif l == 'get':
                print(dev.get_active())
            else:
                vals = l.split()
                if vals[0] == 'set':
                    dev.set_light(int(vals[1]), int(vals[2]))
                else:
                    dev.com.write(bytes([int(vals[0])]))
        except:
            traceback.print_exc()

if __name__ == '__main__':
    exit(main())
