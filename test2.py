from flask import Flask, render_template, request, jsonify, session, redirect, url_for, Response
from djitellopy import Tello
from ultralytics import YOLO
import cv2
import threading
import time

app = Flask(__name__)
app.secret_key = '1234'  

model = YOLO('yolov8s.pt')
VEHICLE_CLASSES = {"car", "truck", "motorcycle", "bus"}
traffic_light_detected = False
frame_lock = threading.Lock()
frame = None
tello = None

# User authentication
USERS = {'admin': 'password123', 'name': '1234'}


def video_stream():
    global frame, traffic_light_detected, tello

    while tello and tello.stream_on:
        img = tello.get_frame_read().frame
        img = cv2.resize(img, (960, 720))
        results = model(img)

        vehicle_count = 0
        traffic_light_detected = False

        if results and results[0].boxes:
            for box, cls in zip(results[0].boxes.xyxy, results[0].boxes.cls):
                class_name = model.names[int(cls)]
                x1, y1, x2, y2 = map(int, box)
                color = (0, 255, 0) if class_name in VEHICLE_CLASSES else (0, 0, 255)
                label = f'{class_name}'
                cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
                cv2.putText(img, label, (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                if class_name in VEHICLE_CLASSES:
                    vehicle_count += 1
                elif class_name == "traffic light":
                    traffic_light_detected = True

        cv2.putText(img, f'Vehicles: {vehicle_count}', (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        with frame_lock:
            frame = img

        time.sleep(0.05)


def generate_video():
    global frame
    while True:
        with frame_lock:
            if frame is not None:
                _, buffer = cv2.imencode('.jpg', frame)
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        time.sleep(0.05)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/about')
def about():
    return render_template('About.html')


@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/authenticate', methods=['POST'])
def authenticate():
    global tello

    username = request.form.get('username')
    password = request.form.get('password')

    if username in USERS and USERS[username] == password:
        session['user'] = username

        if username == 'admin':
            if tello is None:
                try:
                    tello = Tello()
                    tello.connect()
                    tello.streamon()
                    time.sleep(2)
                    threading.Thread(target=video_stream, daemon=True).start()
                except Exception as e:
                    return jsonify({'success': False, 'error': f'Drone connection failed: {str(e)}'}), 500

            return jsonify({'success': True, 'redirect': url_for('dashboard')})

        return jsonify({'success': True, 'redirect': url_for('viewer')})

    return jsonify({'success': False, 'error': 'Invalid credentials'}), 401


@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    if session['user'] != 'admin':
        return redirect(url_for('viewer'))
    return render_template('dashboard.html')


@app.route('/viewer')
def viewer():
    return render_template('viewer.html')


@app.route('/video_feed')
def video_feed():
    return Response(generate_video(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/drone_status')
def drone_status():
    global tello

    if tello is None:
        return jsonify({'battery': 'N/A', 'vehicle_count': 0})

    try:
        battery = tello.get_battery()
    except Exception:
        battery = 'Error'

    vehicle_count = 0
    with frame_lock:
        if frame is not None:
            results = model(frame)
            vehicle_count = sum(1 for box, cls in zip(results[0].boxes.xyxy, results[0].boxes.cls)
                                if model.names[int(cls)] in VEHICLE_CLASSES)

    return jsonify({'battery': battery, 'vehicle_count': vehicle_count})


@app.route('/command', methods=['POST'])
def command():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    if tello is None:
        return jsonify({'error': 'Drone not connected'}), 400

    cmd = request.json.get('cmd')
    try:
        if cmd == 'takeoff':
            tello.takeoff()
        elif cmd == 'land':
            tello.land()
        elif cmd == 'forward':
            tello.move_forward(30)
        elif cmd == 'backward':
            tello.move_back(30)
        elif cmd == 'left':
            tello.move_left(30)
        elif cmd == 'right':
            tello.move_right(30)
        elif cmd == 'up':
            tello.move_up(30)
        elif cmd == 'down':
            tello.move_down(30)
        elif cmd == 'rotate_left':
            tello.rotate_counter_clockwise(30)
        elif cmd == 'rotate_right':
            tello.rotate_clockwise(30)
        else:
            return jsonify({'error': 'Invalid command'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify({'status': 'ok'})


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
