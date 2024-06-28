from flask import Flask, request, send_file
from flask_cors import CORS
import cv2
import numpy as np
import io
import tempfile
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
import json

app = Flask(__name__)
CORS(app)

def apply_zoom(frame, center, zoom_factor):
    h, w = frame.shape[:2]
    center_y, center_x = center
    M = cv2.getRotationMatrix2D((center_x, center_y), 0, zoom_factor)
    zoomed = cv2.warpAffine(frame, M, (w, h))
    return zoomed

def process_frame(frame, zoom_points, current_time):
    if not zoom_points:
        return frame

    for point in zoom_points:
        if point['startTime'] <= current_time <= point['endTime']:
            progress = (current_time - point['startTime']) / (point['endTime'] - point['startTime'])
            current_zoom = point['startZoom'] + (point['endZoom'] - point['startZoom']) * progress
            return apply_zoom(frame, (int(point['y']), int(point['x'])), current_zoom)

    return frame

def add_zoom(input_video, zoom_points):
    with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_input:
        temp_input.write(input_video.read())

    cap = cv2.VideoCapture(temp_input.name)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_output:
        fourcc = cv2.VideoWriter_fourcc(*'VP80')
        out = cv2.VideoWriter(temp_output.name, fourcc, fps, (width, height))

        for frame_count in range(total_frames):
            ret, frame = cap.read()
            if not ret:
                break

            current_time = frame_count / fps
            processed = process_frame(frame, zoom_points, current_time)
            out.write(processed)

        cap.release()
        out.release()

    with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_webm:
        ffmpeg_command = [
            'ffmpeg',
            '-y',
            '-i', temp_output.name,
            '-c:v', 'libvpx-vp9',
            '-crf', '30',
            '-b:v', '0',
            '-b:a', '128k',
            '-c:a', 'libopus',
            '-threads', '4',
            temp_webm.name
        ]

        subprocess.run(ffmpeg_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        with open(temp_webm.name, 'rb') as f:
            edited_video = f.read()

    os.unlink(temp_input.name)
    os.unlink(temp_output.name)
    os.unlink(temp_webm.name)

    return edited_video

@app.route('/edit_video', methods=['POST'])
def edit_video():
    if 'video' not in request.files:
        return 'Aucun fichier vidéo trouvé', 400

    video = request.files['video']
    zoom_points = json.loads(request.form.get('zoomPoints', '[]'))

    try:
        edited_video = add_zoom(video, zoom_points)
        return send_file(
            io.BytesIO(edited_video),
            mimetype='video/webm',
            as_attachment=True,
            download_name='edited_video.webm'
        )
    except Exception as e:
        app.logger.error(f"Erreur lors de l'édition de la vidéo : {str(e)}")
        return "Erreur lors de l'édition de la vidéo", 500

if __name__ == '__main__':
    app.run(debug=True)
