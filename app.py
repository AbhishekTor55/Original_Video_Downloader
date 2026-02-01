from flask import Flask, render_template, request, send_file
import yt_dlp
import os
import sys
from werkzeug.utils import secure_filename

app = Flask(__name__)

# ---------- PATH AUTO-DETECT ----------
def get_video_dir():
    # Termux detection
    if "com.termux" in os.environ.get("PREFIX", ""):
        return "/sdcard/Movies"
    # Linux / PC
    return os.path.join(os.path.expanduser("~"), "Downloads", "video_downloader")


VIDEO_DIR = get_video_dir()
os.makedirs(VIDEO_DIR, exist_ok=True)


# ---------- DOWNLOAD FUNCTION ----------
def download_video(url):
    ydl_opts = {
        "format": "bestvideo+bestaudio/best",
        "merge_output_format": "mp4",
        "outtmpl": os.path.join(VIDEO_DIR, "%(title).200s.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

        filepath = ydl.prepare_filename(info)
        filepath = os.path.splitext(filepath)[0] + ".mp4"

        return {
            "path": filepath,
            "title": info.get("title"),
            "uploader": info.get("uploader"),
            "duration": info.get("duration"),
        }


# ---------- ROUTES ----------
@app.route("/", methods=["GET", "POST"])
def index():
    error = None
    video = None

    if request.method == "POST":
        url = request.form.get("url", "").strip()

        if not url.startswith(("http://", "https://")):
            error = "Invalid URL"
        else:
            try:
                video = download_video(url)
            except Exception as e:
                error = str(e)

    return render_template("index.html", video=video, error=error)


@app.route("/download")
def download():
    path = request.args.get("path")

    if not path or not os.path.exists(path):
        return "File not found", 404

    return send_file(
        path,
        as_attachment=True,
        download_name=secure_filename(os.path.basename(path)),
    )


# ---------- RUN ----------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True)

