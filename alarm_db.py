import sqlite3
import datetime
import logging
import sys

ver = 1

logger = logging.getLogger('ArtSunrise')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler(sys.stdout)
logger.addHandler(ch)


class NotFoundError(Exception):
    pass


# функция, которая преобразует запись из базы данных в словарь
def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


# Time
def convert_time(s):
    return datetime.datetime.strptime(s.decode(), '%H:%M:%S').time()


# Register the adapter
sqlite3.register_adapter(datetime.time, str)
# Register the converter
sqlite3.register_converter("time", convert_time)


# Timedelta
def adapt_timedelta(td):
    return str(td.total_seconds())


def convert_timedelta(s):
    return datetime.timedelta(seconds=int(s.decode()))


# Register the adapter
sqlite3.register_adapter(datetime.timedelta, adapt_timedelta)
# Register the converter
sqlite3.register_converter("timedelta", convert_timedelta)

sqlite3.register_adapter(datetime.datetime, str)
# Register the converter
sqlite3.register_converter("datetime", lambda s: datetime.datetime.strptime(s.decode(), '%Y-%m-%d %H:%M:%S'))


def init_db(cn):
    c = cn.cursor()
    try:
        c.execute('select value from properties where name = "version"')
        v = int(c.fetchone()["value"])
    except sqlite3.OperationalError:
        v = -1
    if v != ver:
        c.execute('drop table if exists alarms')
        c.execute(
            'create table alarms(id integer primary key autoincrement, alarm_time time, sunrise_time timedelta, days list, enabled integer, active integer, disable_time datetime)')
        c.execute('create table if not exists properties(name text unique, value text)')
        c.execute('replace into properties values (?, ?)', ("version", ver))
        cn.commit()


# Функция, которая возвращает запись в базе данных по id
def get_alarm_by_id(alarm_id):
    cur.execute('select * from alarms where id = ?', (alarm_id,))
    alarm = cur.fetchone()
    if alarm is None:
        raise NotFoundError
    return alarm


def get_alarm_list():
    alarms = []
    for e in cur.execute('select * from alarms'):
        alarms.append(e)
    return alarms


def create_alarm(alarm_time, sunrise_time, days, enabled, active, disable_time):
    cur.execute(
        'insert into alarms (alarm_time, sunrise_time, days, enabled, active, disable_time) values(?, ?, ?, ?, ?, ?)',
        [alarm_time, sunrise_time, days, enabled, active, disable_time])
    conn.commit()
    return cur.lastrowid


def update_alarm(id, alarm_time=None, sunrise_time=None, days=None, enabled=None, active=None, disable_time=None):
    kwargs = {
        'alarm_time': alarm_time,
        'sunrise_time': sunrise_time,
        'days': days,
        'enabled': enabled,
        'active': active,
        'disable_time': disable_time
    }
    args_list = [k for k, v in kwargs.items() if v is not None]
    cur.execute('update alarms '
                'set {} '
                'where id = ?'.format(', '.join('{} = ?'.format(k) for k in args_list)),
                ([kwargs[k] for k in args_list] + [id]))
    conn.commit()


def delete_alarm(id):
    cur.execute('delete from alarms '
                'where id = ?', (id,))
    conn.commit()


def singleton(fun):
    global instance
    instance = None

    def get_instance(*args, **kwargs):
        global instance
        if instance is None:
            instance = fun(*args, **kwargs)
        return instance
    return get_instance


@singleton
def connect_to_db():
    conn = sqlite3.connect('alarms.db', detect_types=sqlite3.PARSE_DECLTYPES, check_same_thread=False)
    conn.row_factory = dict_factory
    init_db(conn)
    return conn.cursor(), conn

cur, conn = connect_to_db()