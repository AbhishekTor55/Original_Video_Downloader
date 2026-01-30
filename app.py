from flask import Flask, render_template, request, send_from_directory
import yt_dlp
import os

app = Flask(__name__)

VIDEO_DIR = "/sdcard/Movies"
os.makedirs(VIDEO_DIR, exist_ok=True)

@app.route("/", methods=["GET", "POST"])
def index():
    video_info = None
    filename = None

    if request.method == "POST":
        url = request.form.get("url")

        if not url:
            return render_template("index.html", error="URL empty hai")

        ydl_opts = {
            "format": "bestvideo+bestaudio/best",
            "merge_output_format": "mp4",
            "outtmpl": os.path.join(VIDEO_DIR, "%(title)s.%(ext)s"),
            "quiet": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            video_info = {
                "title": info.get("title"),
                "uploader": info.get("uploader"),
                "duration": info.get("duration"),
            }

    return render_template(
        "index.html",
        video=video_info,
        file=filename
    )


@app.route("/download/<path:filename>")
def download(filename):
    return send_from_directory(VIDEO_DIR, os.path.basename(filename), as_attachment=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
