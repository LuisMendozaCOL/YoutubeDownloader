# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_socketio import SocketIO
import os
import yt_dlp
import sys

app = Flask(__name__)
socketio = SocketIO(app)

# Obtiene la carpeta "Descargas" del usuario
DOWNLOAD_FOLDER = os.path.join(os.path.expanduser("~"), "Downloads")
AUDIO_DOWNLOAD_DIR = os.path.join(DOWNLOAD_FOLDER, "Audio")
VIDEO_DOWNLOAD_DIR = os.path.join(DOWNLOAD_FOLDER, "Videos")

# Asegurar que los directorios de descarga existen
os.makedirs(AUDIO_DOWNLOAD_DIR, exist_ok=True)
os.makedirs(VIDEO_DOWNLOAD_DIR, exist_ok=True)


def YoutubeDownload(video_url, audio_only=True):
    try:
        ydl_opts = {
            'format': 'bestaudio/best' if audio_only else 'bestvideo+bestaudio',
            'outtmpl': os.path.join(AUDIO_DOWNLOAD_DIR if audio_only else VIDEO_DOWNLOAD_DIR, '%(title)s.%(ext)s'),
            'progress_hooks': [download_progress],
        }

        if audio_only:
            ydl_opts['postprocessors'] = [
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }
            ]

        # Ubicación específica de FFmpeg
        ydl_opts['ffmpeg_location'] = r'C:\Users\luis_\OneDrive - Universidad Nacional de Colombia\3 - Python Projects\2 - Youtube Downloader\Scripts\ffmpeg\bin'

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])

        socketio.emit("download_complete", {
            "message": f"{'Audio' if audio_only else 'Video'} descargado correctamente en la carpeta {'Audio' if audio_only else 'Videos'} dentro de la carpeta Descargas del computador."
        })

    except Exception as e:
        socketio.emit("download_complete", {
                      "message": f"Error al descargar: {e}"})


def download_progress(d):
    if d['status'] == 'downloading':
        progress = d['_percent_str'].replace('%', '')  # Limpiar el porcentaje
        # Enviar progreso al frontend
        socketio.emit("progress_update", {"progress": progress})
    elif d['status'] == 'finished':
        # Enviar progreso completo
        socketio.emit("progress_update", {"progress": "100"})


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/download", methods=["POST"])
def download():
    video_url = request.form.get("video_url")
    action = request.form.get("action")

    if action == "video":
        YoutubeDownload(video_url, audio_only=False)
    else:
        YoutubeDownload(video_url, audio_only=True)

    return jsonify({"message": "Descarga iniciada"})


if __name__ == "__main__":
    socketio.run(app, debug=True)
