import time
import logging
from light_controller import LightControl
import datetime as dt
import alarm_db as db

logger = logging.getLogger('alarm_service')


class FakeLightControl:
    def set_light(self, cold, warm):
        logging.info("Set cold: {}, warm: {}".format(cold, warm))

    def get_active(self):
        return 0


def calculate(start: dt.datetime, duration: dt.timedelta, now: dt.datetime):
    time_from_start = now - start
    i = float(time_from_start.seconds)
    t = float(duration.seconds)
    c = 255. * i**2 / t**2
    w = (255. * i * t - 255 * i**2) / t**2
    return int(c), int(w)


def service():
    control = LightControl()
    while True:
        alarms = db.get_alarm_list()
        now = dt.datetime.now()
        for alarm in alarms:
            today_alarm = dt.datetime.combine(now.date(), alarm['alarm_time'])
            if today_alarm + alarm['sunrise_time'] > now >= today_alarm > alarm['disable_time']:
                if alarm['active'] != 1:
                    db.update_alarm(alarm['id'], active=1)
                else:
                    if 2 != control.get_active():
                        db.update_alarm(alarm['id'], disable_time=now)
                        continue
                c, w = calculate(today_alarm, alarm['sunrise_time'], now)
                control.set_light(c, w)
            elif now > today_alarm:
                db.update_alarm(alarm['id'], active=0)
            logger.info('Check: {}, {}, {}, {}'.format(now, today_alarm, today_alarm + alarm['sunrise_time'],
                                                                 alarm['disable_time']))
        time.sleep(5)
