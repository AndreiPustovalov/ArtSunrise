import logging
import sys
# from LightControl import LightControl
from flask import Flask
from flask import jsonify
from flask import abort
from flask import make_response
from flask import request
from flask import render_template
from threading import Thread
import datetime
import alarm_db as db
from alarm_service import service

ver = 1

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('ArtSunrise')

app = Flask(__name__)


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


# получить список будильников
@app.route('/alarms', methods=['GET'])
def get_alarms():
    return jsonify(serialize({'alarms': db.get_alarm_list()}))


# получить информацию по конкретному будильнику
@app.route('/alarms/<int:id>', methods=['GET'])
def get_alarm(id):
    alarm = db.get_alarm_by_id(id)
    return jsonify(serialize({'alarm': alarm}))


# вернуть ошибку, если ошибка 404
@app.errorhandler(db.NotFoundError)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


# создание нового будильника
@app.route('/alarms', methods=['POST'])
def create_alarm_request():
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
    created_id = db.create_alarm(*alarm)
    return jsonify(serialize({'alarm': db.get_alarm_by_id(created_id)})), 201


# редактирование будильника
@app.route('/alarms/<int:id>', methods=['PUT'])
def update_alarm_request(id):
    alarm = db.get_alarm_by_id(id)
    if not request.json:
        abort(400)
    if 'alarm_time' in request.json and type(request.json['alarm_time']) != str:
        abort(400)
    if 'sunrise_time' in request.json and type(request.json['sunrise_time']) != int:
        abort(400)
    if 'days' in request.json and type(request.json['days']) != str:
        abort(400)
    alarm = [id, request.json.get('alarm_time', alarm["alarm_time"]),
                 request.json.get('sunrise_time', alarm["sunrise_time"]),
                 request.json.get('days', alarm["days"]),
                 request.json.get('enabled', alarm["enabled"])]
    db.update_alarm(*alarm)
    alarm = db.get_alarm_by_id(id)
    return jsonify(serialize({'alarm': alarm}))


# удаление будильника
@app.route('/alarms/<int:id>', methods=['DELETE'])
def delete_alarm_request(id):
    # db.get_alarm_by_id(id)
    db.delete_alarm(id)
    return jsonify(serialize({'result': True}))


@app.route('/', methods=['GET'])
def root():
    return render_template('index.html')

if __name__ == '__main__':
    alarm_service_thread = Thread(target=service)
    alarm_service_thread.daemon = True
    alarm_service_thread.start()
    app.run(debug=False, host='0.0.0.0')
