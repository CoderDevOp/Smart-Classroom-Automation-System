from flask import Flask, render_template, jsonify, Response, send_file
from pathlib import Path
import subprocess
import sys
import os
import json
import time


PROJECT_ROOT = Path(__file__).resolve().parents[1]

ZONE_CONFIGURATOR = (
    PROJECT_ROOT
    / "src"
    / "vision"
    / "zone_configurator.py"
)

AUTOMATION_MAIN = (
    PROJECT_ROOT
    / "src"
    / "automation"
    / "main.py"
)

ZONE_CONFIG = (
    PROJECT_ROOT
    / "config"
    / "zones.json"
)

DATABASE_PATH = (
    PROJECT_ROOT
    / "data"
    / "classroom.db"
)

LIVE_FRAME_PATH = (
    PROJECT_ROOT
    / "data"
    / "live_camera.jpg"
)


app = Flask(__name__)

automation_process = None


def get_zone_data():

    if not ZONE_CONFIG.exists():

        return {
            "saved": False,
            "count": 0,
            "zones": []
        }

    try:

        with open(
            ZONE_CONFIG,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        zones = data.get(
            "zones",
            []
        )

        return {
            "saved": len(zones) >= 2,
            "count": len(zones),
            "zones": [
                zone.get(
                    "name",
                    f"Zone {index + 1}"
                )
                for index, zone in enumerate(zones)
            ]
        }

    except Exception:

        return {
            "saved": False,
            "count": 0,
            "zones": []
        }


def automation_is_running():

    global automation_process

    if automation_process is None:

        return False

    if automation_process.poll() is None:

        return True

    automation_process = None

    return False


def generate_video():

    while True:

        if not LIVE_FRAME_PATH.exists():

            time.sleep(0.1)

            continue

        try:

            frame = LIVE_FRAME_PATH.read_bytes()

        except Exception:

            time.sleep(0.05)

            continue

        if frame:

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n"
                + frame
                + b"\r\n"
            )

        time.sleep(0.05)


@app.route("/")
def dashboard():

    return render_template(
        "dashboard.html"
    )


@app.route(
    "/configure_zones",
    methods=["POST"]
)
def configure_zones():

    if not ZONE_CONFIGURATOR.exists():

        return jsonify({
            "success": False,
            "message": "Zone configurator not found."
        }), 404

    try:

        creation_flags = 0

        if os.name == "nt":

            creation_flags = (
                subprocess.CREATE_NEW_CONSOLE
            )

        subprocess.Popen(
            [
                sys.executable,
                str(ZONE_CONFIGURATOR)
            ],
            cwd=str(PROJECT_ROOT),
            creationflags=creation_flags
        )

        return jsonify({
            "success": True,
            "message": (
                "Zone configurator opened. "
                "Save the zones, then refresh "
                "the dashboard."
            )
        })

    except Exception as error:

        return jsonify({
            "success": False,
            "message": str(error)
        }), 500


@app.route("/zone_status")
def zone_status():

    return jsonify(
        get_zone_data()
    )


@app.route(
    "/start_automation",
    methods=["POST"]
)
def start_automation():

    global automation_process

    if automation_is_running():

        return jsonify({
            "success": False,
            "message": (
                "Automation is already running."
            )
        })

    zone_data = get_zone_data()

    if not zone_data["saved"]:

        return jsonify({
            "success": False,
            "message": (
                "Configure at least 2 zones first."
            )
        })

    try:

        if LIVE_FRAME_PATH.exists():

            LIVE_FRAME_PATH.unlink()

    except Exception:

        pass

    try:

        creation_flags = 0

        if os.name == "nt":

            creation_flags = (
                subprocess.CREATE_NEW_CONSOLE
            )

        automation_process = subprocess.Popen(
            [
                sys.executable,
                str(AUTOMATION_MAIN)
            ],
            cwd=str(PROJECT_ROOT),
            creationflags=creation_flags
        )

        return jsonify({
            "success": True,
            "message": "Automation started."
        })

    except Exception as error:

        automation_process = None

        return jsonify({
            "success": False,
            "message": str(error)
        }), 500


@app.route(
    "/stop_automation",
    methods=["POST"]
)
def stop_automation():

    global automation_process

    if not automation_is_running():

        return jsonify({
            "success": True,
            "message": (
                "Automation is already stopped."
            )
        })

    try:

        automation_process.terminate()

        try:

            automation_process.wait(
                timeout=5
            )

        except subprocess.TimeoutExpired:

            automation_process.kill()

            automation_process.wait(
                timeout=2
            )

        automation_process = None

        return jsonify({
            "success": True,
            "message": "Automation stopped."
        })

    except Exception as error:

        return jsonify({
            "success": False,
            "message": str(error)
        }), 500


@app.route("/automation_status")
def automation_status():

    return jsonify({
        "running": automation_is_running()
    })


@app.route("/video_feed")
def video_feed():

    return Response(
        generate_video(),
        mimetype=(
            "multipart/x-mixed-replace;"
            " boundary=frame"
        )
    )


@app.route("/camera_snapshot")
def camera_snapshot():

    if not LIVE_FRAME_PATH.exists():

        return (
            "Camera not running",
            404
        )

    return send_file(
        LIVE_FRAME_PATH,
        mimetype="image/jpeg"
    )


@app.route("/system_status")
def system_status():

    running = automation_is_running()

    zones = get_zone_data()

    return jsonify({

        "camera": (
            "Running"
            if running
            else "Stopped"
        ),

        "yolo": (
            "Running"
            if running
            else "Stopped"
        ),

        "arduino": (
            "Running"
            if running
            else "Stopped"
        ),

        "database": "Ready",

        "zones": (
            "Ready"
            if zones["saved"]
            else "Not Configured"
        ),

        "automation": (
            "Running"
            if running
            else "Stopped"
        )

    })


if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
        use_reloader=False
    )