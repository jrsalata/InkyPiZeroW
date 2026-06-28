import os
import io
import subprocess
from flask import Flask,flash, request, redirect, url_for, send_file
from werkzeug.utils import secure_filename
from pathlib import Path
from PIL import Image
# We are expecting only HTML files
ALLOWED_EXTENSIONS = {'html'}
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = "."
@app.route('/')
def hello():
    
    return f"The server is up!"
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
@app.route('/upload/<int:width>/<int:height>', methods=['POST'])
def upload_file(width, height):
    if request.method == 'POST':
        
        # check if the post request has the file part
        if 'file' not in request.files:
            return redirect(request.url)
        
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            img_file_path = filepath.replace(".html",".png")
            file.save(filepath)
            command = [
                "chromium",
                filepath,
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
                "--no-sandbox"
            ]
            result = subprocess.run(command, capture_output=True, check=False)
            print(result.stdout)
            print(result.stderr)
            # Check if the process failed or the output file is missing
            if result.returncode != 0 or not os.path.exists(img_file_path):
                return abort(500)
            # Load the image using PIL
            with Image.open(img_file_path) as img:
                image = io.BytesIO()
                img.save(image, 'PNG')
                image.seek(0)
            # Remove image and html files
            # os.remove(img_file_path)
            # os.remove(filepath)
            print(image)
            return send_file(image, mimetype="image/png")
    return abort(400)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)