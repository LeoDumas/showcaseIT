from flask import Flask, request, send_file, after_this_request
from flask_cors import CORS
import cv2
import numpy as np
import os
import uuid
import time

app = Flask(__name__)
CORS(app)

def add_zoom(input_path, output_path, zoom_factor=1.5):
    cap = cv2.VideoCapture(input_path)

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        h, w = frame.shape[:2]
        zh = int(h / zoom_factor)
        zw = int(w / zoom_factor)

        top = (h - zh) // 2
        left = (w - zw) // 2

        zoomed = frame[top:top+zh, left:left+zw]
        zoomed = cv2.resize(zoomed, (w, h))

        out.write(zoomed)

    cap.release()
    out.release()

@app.route('/edit_video', methods=['POST'])
def edit_video():
    if 'video' not in request.files:
        return 'Aucun fichier vidéo trouvé', 400

    video = request.files['video']
    input_path = f'input_video_{uuid.uuid4()}.webm'
    output_path = f'output_video_{uuid.uuid4()}.mp4'

    video.save(input_path)

    try:
        add_zoom(input_path, output_path)

        @after_this_request
        def remove_files(response):
            try:
                os.remove(input_path)
            except Exception as e:
                app.logger.error(f"Erreur lors de la suppression du fichier d'entrée : {str(e)}")

            def delete_output():
                for _ in range(5):  # Essayer 5 fois
                    try:
                        os.remove(output_path)
                        break
                    except Exception as e:
                        app.logger.error(f"Erreur lors de la suppression du fichier de sortie : {str(e)}")
                        time.sleep(1)  # Attendre 1 seconde avant de réessayer

            response.call_on_close(delete_output)
            return response

        return send_file(output_path, as_attachment=True)
    except Exception as e:
        app.logger.error(f"Erreur lors de l'édition de la vidéo : {str(e)}")
        return "Erreur lors de l'édition de la vidéo", 500

if __name__ == '__main__':
    app.run(debug=True)
