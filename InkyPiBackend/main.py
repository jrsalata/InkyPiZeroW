import os
import io
import subprocess
import tempfile
from pathlib import Path

from flask import Flask, abort, jsonify, request, send_file
from werkzeug.utils import secure_filename
from PIL import Image

# We are expecting only HTML files
ALLOWED_EXTENSIONS = {'html'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.getenv("UPLOAD_FOLDER", ".")

CHROMIUM_BIN = os.getenv("CHROMIUM_BIN", "chromium")
CHROMIUM_TIMEOUT_SECONDS = int(os.getenv("CHROMIUM_TIMEOUT_SECONDS", "45"))


@app.route('/')
def hello():
    return "The server is up!"


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _render_target_to_png(target, width, height, img_file_path):
    command = [
        CHROMIUM_BIN,
        "--headless",
        f"--screenshot={img_file_path}",
        f"--window-size={width},{height}",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--use-gl=swiftshader",
        "--hide-scrollbars",
        "--in-process-gpu",
        "--js-flags=--jitless",
        "--disable-zero-copy",
        "--disable-gpu-memory-buffer-compositor-resources",
        "--disable-extensions",
        "--disable-plugins",
        "--mute-audio",
        "--renderer-process-limit=1",
        "--no-zygote",
        "--no-sandbox",
        target,
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        check=False,
        timeout=CHROMIUM_TIMEOUT_SECONDS,
    )

    if result.returncode != 0 or not os.path.exists(img_file_path):
        app.logger.error("Chromium render failed: %s", result.stderr.decode("utf-8", errors="ignore"))
        abort(500)


def _send_png(img_file_path):
    with Image.open(img_file_path) as img:
        image = io.BytesIO()
        img.save(image, 'PNG')
        image.seek(0)
    return send_file(image, mimetype="image/png")


@app.route('/upload/<int:width>/<int:height>', methods=['POST'])
def upload_file(width, height):
    if 'file' not in request.files:
        abort(400)

    file = request.files['file']
    filename = secure_filename(file.filename or "render.html")
    if not allowed_file(filename):
        abort(400)

    with tempfile.TemporaryDirectory() as temp_dir:
        html_path = os.path.join(temp_dir, filename)
        png_path = os.path.join(temp_dir, "render.png")
        file.save(html_path)

        html_target = Path(html_path).resolve().as_uri()
        _render_target_to_png(html_target, width, height, png_path)
        return _send_png(png_path)


@app.route('/screenshot/<int:width>/<int:height>', methods=['POST'])
def screenshot_url(width, height):
    data = request.get_json(silent=True) or {}
    target_url = (data.get("url") or "").strip()

    if not target_url:
        abort(400)

    if not target_url.startswith(("http://", "https://", "file://")):
        return jsonify({"error": "url must start with http://, https://, or file://"}), 400

    with tempfile.TemporaryDirectory() as temp_dir:
        png_path = os.path.join(temp_dir, "screenshot.png")
        _render_target_to_png(target_url, width, height, png_path)
        return _send_png(png_path)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)