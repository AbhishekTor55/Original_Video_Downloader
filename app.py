from flask import Flask, render_template, request, jsonify
import yt_dlp
import os
import re

app = Flask(__name__)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

progress_data = {
    "status": "idle",
    "percent": 0
}

def progress_hook(d):
    if d['status'] == 'downloading':
        total = d.get('total_bytes') or d.get('total_bytes_estimate')
        downloaded = d.get('downloaded_bytes', 0)
        if total:
            progress_data["percent"] = int(downloaded * 100 / total)
            progress_data["status"] = "downloading"

    elif d['status'] == 'finished':
        progress_data["percent"] = 100
        progress_data["status"] = "finished"

def safe_filename(s):
    return re.sub(r'[^\w\-_\. ]', '_', s)

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/start", methods=["POST"])
def start_download():
    url = request.json.get("url")
    filetype = request.json.get("type", "mp4")

    progress_data["percent"] = 0
    progress_data["status"] = "starting"

    if "youtube.com/shorts/" in url:
        vid = url.split("/")[-1].split("?")[0]
        url = f"https://www.youtube.com/watch?v={vid}"

    outtmpl = f"{DOWNLOAD_DIR}/%(title)s.%(ext)s"

    if filetype == "mp3":
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": outtmpl,
            "progress_hooks": [progress_hook],
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
            "quiet": True
        }
    else:
        ydl_opts = {
            "format": "bestvideo+bestaudio/best",
            "merge_output_format": "mp4",
            "outtmpl": outtmpl,
            "progress_hooks": [progress_hook],
            "quiet": True
        }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    return jsonify({"status": "started"})

@app.route("/progress")
def progress():
    return jsonify(progress_data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
