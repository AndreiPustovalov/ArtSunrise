import logging
import sys
#from LightControl import LightControl
from flask import Flask
from flask import jsonify
import datetime
import sqlite3

ver = 1

logger = logging.getLogger('ArtSunrise')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler(sys.stdout)
logger.addHandler(ch)

app = Flask(__name__)


objects = [(0,datetime.time(hour=8, minute=0, second=0),datetime.timedelta(minutes=30), 'mon,tue,wed,thu,fri',True,False,datetime.datetime(2017, 11, 3, hour=7, minute=45, second=0)),
           (1,datetime.time(hour=10, minute=0, second=0),datetime.timedelta(minutes=20),'',True,True,datetime.datetime(2017, 11, 4, hour=9, minute=50, second=0))
]

# Time
def convert_time(s):
    return datetime.datetime.strptime(s.decode(),'%H:%M:%S').time()
# Register the adapter
sqlite3.register_adapter(datetime.time, str)
# Register the converter
sqlite3.register_converter("time", convert_time)

#Timedelta
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


def serialize(obj):
    if isinstance(obj, dict):
        t = {}
        for k in obj:
            if isinstance(obj[k], datetime.datetime) or isinstance(obj[k], datetime.timedelta) or isinstance(obj[k], datetime.time):
                t[k] = str(obj[k])
            elif isinstance(obj[k], dict) or isinstance(obj[k], list):
                t[k] = serialize(obj[k])
            else:
                t[k] = obj[k]
    elif isinstance(obj, list):
        t = [serialize(e) for e in obj]
    else:
        t = obj
    return t


def init_db(cn):
    c = cn.cursor()
    try:
        c.execute('select value from properties where name = "version"')
        v = c.fetchone()["value"]
    except sqlite3.OperationalError:
        v = -1
    if v != ver:
        c.execute('drop table if exists alarms')
        c.execute('create table alarms(id integer primary key, alarm_time time, sunrise_time timedelta, days list, enabled integer, active integer, disable_time datetime)')
        c.execute('create table if not exists properties(name text unique, value text)')
        c.execute('replace into properties values (?, ?)',("version",ver))
        c.executemany('insert into alarms values(?, ?, ?, ?, ?, ?, ?)', objects)
        cn.commit()


@app.route('/alarms', methods=['GET'])
def get_alarms():
    alarms = []
    for e in cur.execute('select * from alarms'):
        alarms.append(e)
    return jsonify(serialize({'alarms': alarms}))


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

if __name__ == '__main__':
    conn = sqlite3.connect('alarms.db',detect_types=sqlite3.PARSE_DECLTYPES, check_same_thread=False)
    conn.row_factory = dict_factory
    cur = conn.cursor()
    init_db(conn)
    app.run(debug=True, host='0.0.0.0')