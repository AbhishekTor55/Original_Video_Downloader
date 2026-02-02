from flask import Flask, render_template, request, jsonify, send_file
import yt_dlp
import os
import re
import threading
import time

app = Flask(__name__)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

progress_data = {
    "status": "idle",
    "percent": 0
}

last_file = None


# 🔹 Safe filename
def safe_name(name):
    return re.sub(r'[^\w\-_. ]', '_', name)


# 🔹 Progress hook
def progress_hook(d):
    if d["status"] == "downloading":
        total = d.get("total_bytes") or d.get("total_bytes_estimate")
        downloaded = d.get("downloaded_bytes", 0)
        if total:
            progress_data["percent"] = int(downloaded * 100 / total)
            progress_data["status"] = "downloading"

    elif d["status"] == "finished":
        progress_data["percent"] = 100
        progress_data["status"] = "finished"


# 🔥 Auto delete file after delay (seconds)
def delete_file_later(path, delay=180):
    def worker():
        time.sleep(delay)
        try:
            if os.path.exists(path):
                os.remove(path)
                print(f"[AUTO DELETE] Removed: {path}")
        except Exception as e:
            print(f"[AUTO DELETE ERROR] {e}")

    threading.Thread(target=worker, daemon=True).start()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/start", methods=["POST"])
def start_download():
    global last_file

    data = request.json
    url = data.get("url")
    filetype = data.get("type", "mp4")

    progress_data["percent"] = 0
    progress_data["status"] = "starting"
    last_file = None

    # 🔹 YouTube Shorts fix
    if "youtube.com/shorts/" in url:
        vid = url.split("/")[-1].split("?")[0]
        url = f"https://www.youtube.com/watch?v={vid}"

    # 🔹 Extract title safely
    with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
        info = ydl.extract_info(url, download=False)
        title = safe_name(info.get("title", "video"))

    if filetype == "mp3":
        final_path = os.path.join(DOWNLOAD_DIR, f"{title}.mp3")

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": final_path,
            "progress_hooks": [progress_hook],
            "quiet": True,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        }

    else:
        final_path = os.path.join(DOWNLOAD_DIR, f"{title}.mp4")

        ydl_opts = {
            "format": "bestvideo+bestaudio/best",
            "merge_output_format": "mp4",
            "outtmpl": final_path,
            "progress_hooks": [progress_hook],
            "quiet": True,
            "noplaylist": True,
            "user_agent": "Mozilla/5.0",
        }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    last_file = final_path  # 🔥 final file path

    return jsonify({"status": "started"})


@app.route("/progress")
def progress():
    return jsonify(progress_data)


@app.route("/download")
def download():
    if not last_file or not os.path.exists(last_file):
        return "No file available", 404

    response = send_file(last_file, as_attachment=True)

    # 🔥 Auto delete after 3 minutes (180 sec)
    delete_file_later(last_file, delay=180)

    return response


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
