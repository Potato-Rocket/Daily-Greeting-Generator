import threading
from flask import Flask, jsonify

from generator.generator import run_pipeline

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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
