import logging
import sys
# from LightControl import LightControl
from flask import Flask
from flask import jsonify
from flask import abort
from flask import make_response
from flask import request
import datetime
import sqlite3

ver = 1

logger = logging.getLogger('ArtSunrise')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler(sys.stdout)
logger.addHandler(ch)

app = Flask(__name__)


class NotFoundError(Exception):
    pass


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


def serialize(obj):
    if isinstance(obj, dict):
        t = {}
        for k in obj:
            if isinstance(obj[k], datetime.datetime) or isinstance(obj[k], datetime.timedelta) or isinstance(obj[k],
                                                                                                             datetime.time):
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


# получить список будильников
@app.route('/alarms', methods=['GET'])
def get_alarms():
    alarms = []
    for e in cur.execute('select * from alarms'):
        alarms.append(e)
    return jsonify(serialize({'alarms': alarms}))


# получить информацию по конкретному будильнику
@app.route('/alarms/<int:id>', methods=['GET'])
def get_alarm(id):
    alarm = get_alarm_by_id(id)
    return jsonify(serialize({'alarm': alarm}))


# вернуть ошибку, если ошибка 404
@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


# вернуть ошибку, если ошибка 404
@app.errorhandler(NotFoundError)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


# создание нового будильника
@app.route('/alarms', methods=['POST'])
def create_alarm():
    if not request.json:
        abort(400)
    alarm = [
        request.json['alarm_time'],
        request.json['sunrise_time'],
        request.json.get('days', ""),
        True,
        False,
        None  # datetime.datetime.now()
    ]
    cur.execute(
        'insert into alarms (alarm_time, sunrise_time, days, enabled, active, disable_time) values(?, ?, ?, ?, ?, ?)',
        alarm)
    conn.commit()
    return jsonify(serialize({'alarm': alarm})), 201


# редактирование будильника
@app.route('/alarms/<int:id>', methods=['PUT'])
def update_alarm(id):
    alarm = get_alarm_by_id(id)
    if not request.json:
        abort(400)
    if 'alarm_time' in request.json and type(request.json['alarm_time']) != str:
        abort(400)
    if 'sunrise_time' in request.json and type(request.json['sunrise_time']) != int:
        abort(400)
    if 'days' in request.json and type(request.json['days']) != str:
        abort(400)
    cur.execute('update alarms '
                'set alarm_time = ?, sunrise_time = ?, days = ?, enabled = ? '
                'where id = ?',
                (request.json.get('alarm_time', alarm["alarm_time"]),
                 request.json.get('sunrise_time', alarm["sunrise_time"]),
                 request.json.get('days', alarm["days"]),
                 request.json.get('enabled', alarm["enabled"]),
                 id))
    conn.commit()
    alarm = get_alarm_by_id(id)
    return jsonify(serialize({'alarm': alarm}))


# удаление будильника
@app.route('/alarms/<int:id>', methods=['DELETE'])
def delete_alarm(id):
    get_alarm_by_id(id)
    cur.execute('delete from alarms '
                'where id = ?', (id,))
    conn.commit()
    return jsonify(serialize({'result': True}))


# функция, которая преобразует запись из базы данных в словарь
def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


if __name__ == '__main__':
    conn = sqlite3.connect('alarms.db', detect_types=sqlite3.PARSE_DECLTYPES, check_same_thread=False)
    conn.row_factory = dict_factory
    cur = conn.cursor()
    init_db(conn)
    app.run(debug=True, host='0.0.0.0')
