import threading
import logging
from flask import Flask, jsonify, redirect, render_template, request, send_file, url_for

from generator.generator import run_pipeline
from generator.io_manager import Mode, IOManager, PathManager, get_paths, get_valid_dates, setup_logging

setup_logging()

app = Flask(__name__)
_pipeline_lock = threading.Lock()


# ---------------------------------------------------------------------------
# Web UI
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    dates = list(reversed(get_valid_dates(strict=False)))
    if not dates:
        return "No greetings found.", 404
    return redirect(url_for("view_date", date=dates[0]))


@app.route("/view/<date>")
def view_date(date):
    paths = PathManager(date)
    if not paths.is_valid(strict=False):
        return "Greeting not found.", 404

    greeting = paths.greeting_path.read_text() if paths.greeting_path.exists() else None
    pipeline = paths.pipeline_path.read_text() if paths.pipeline_path.exists() else None
    log = paths.log_path.read_text() if paths.log_path.exists() else None
    has_audio = paths.audio_path.exists()
    has_coverart = paths.coverart_path.exists()

    return render_template(
        "viewer.html",
        dates=list(reversed(get_valid_dates(strict=False))),
        current_date=date,
        greeting=greeting,
        pipeline=pipeline,
        log=log,
        has_audio=has_audio,
        has_coverart=has_coverart,
    )


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

@app.route("/api/dates")
def dates():
    return jsonify(list(reversed(get_valid_dates())))


@app.route("/api/generate", methods=["POST"])
def generate():
    acquired = _pipeline_lock.acquire(blocking=False)
    if not acquired:
        return jsonify({"status": "busy", "message": "Pipeline already running"}), 409

    try:
        run_pipeline()
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        _pipeline_lock.release()


@app.route("/api/greeting")
def greeting():
    date_str = request.args.get("date")
    fallback = Mode(request.args.get("fallback", Mode.FAIL.value))

    paths, error = get_paths(date_str, fallback) if date_str else get_paths(fallback)
    if not paths:
        return jsonify({"status": "not_found", "message": error}), 404

    data = IOManager(paths).load_data_file()
    if not data:
        return jsonify({"status": "error", "message": "Failed to load data"}), 500

    data["date"] = paths.date_str
    return jsonify(data)


@app.route("/api/audio/<date>")
def audio(date):
    path = PathManager(date).audio_path
    if not path.exists():
        return "", 404
    return send_file(path, mimetype="audio/wav")


@app.route("/api/coverart/<date>")
def coverart(date):
    path = PathManager(date).coverart_path
    if not path.exists():
        return "", 404
    return send_file(path, mimetype="image/jpeg")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
