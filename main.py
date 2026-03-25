import threading
from flask import Flask, jsonify, request, send_file

from generator.generator import run_pipeline
from generator.io_manager import Mode, IOManager, PathManager, get_paths, setup_logging

setup_logging()

app = Flask(__name__)
_pipeline_lock = threading.Lock()


@app.route("/generate", methods=["POST"])
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


@app.route("/greeting")
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


@app.route("/audio/<date>")
def audio(date):
    path = PathManager(date).audio_path
    if not path.exists():
        return "", 404
    return send_file(path, mimetype="audio/wav")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
