import React, { useRef, useState } from "react";
import ToggleSwitch from "./ToggleSwitch";

const ScreenRecorder: React.FC = () => {
  const screenRecording = useRef<HTMLVideoElement>(null);
  const [recorder, setRecorder] = useState<MediaRecorder | null>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);

  const [haveAudio, setHaveAudio] = useState<boolean>(false);
  const [editedVideoUrl, setEditedVideoUrl] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);

  const [fps, setFps] = useState<number>(30);
  const [resolution, setResolution] = useState<string>("1920x1080");
  const [bitrate, setBitrate] = useState<number>(6000000);

  const startScreenRecording = async () => {
    const [width, height] = resolution.split("x").map(Number);
    const mediaStream = await navigator.mediaDevices.getDisplayMedia({
      audio: haveAudio,
      video: {
        width: { ideal: width },
        height: { ideal: height },
        frameRate: { ideal: fps },
      },
    });

    const options = {
      mimeType: "video/webm;codecs=vp9,opus",
      videoBitsPerSecond: bitrate,
    };

    const mediaRecorder = new MediaRecorder(mediaStream, options);
    setRecorder(mediaRecorder);
    setStream(mediaStream);

    const chunks: Blob[] = [];
    mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) {
        chunks.push(e.data);
      }
    };

    mediaRecorder.onstop = () => {
      const blob = new Blob(chunks, { type: "video/webm" });
      const url = URL.createObjectURL(blob);
      if (screenRecording.current) {
        screenRecording.current.src = url;
      }
      stopScreenSharing();
    };

    mediaRecorder.start();
  };

  const stopScreenSharing = () => {
    if (stream) {
      stream.getTracks().forEach((track) => {
        if (track.readyState === "live" && track.kind === "video") {
          track.stop();
        }
      });
      setStream(null);
    }
  };

  function handleCheckAudio(checked: boolean) {
    setHaveAudio(checked);
  }

  const editVideo = async () => {
    if (screenRecording.current && screenRecording.current.src) {
      setIsEditing(true);
      try {
        const response = await fetch(screenRecording.current.src);
        const blob = await response.blob();
        const formData = new FormData();
        formData.append("video", blob, "screen_recording.webm");
        const editResponse = await fetch("http://127.0.0.1:5000/edit_video", {
          method: "POST",
          body: formData,
        });
        if (editResponse.ok) {
          const editedBlob = await editResponse.blob();
          const editedUrl = URL.createObjectURL(editedBlob);
          setEditedVideoUrl(editedUrl);
        } else {
          const errorText = await editResponse.text();
          console.error("Erreur lors de l'édition de la vidéo:", errorText);
        }
      } catch (error) {
        console.error("Erreur :", error);
      } finally {
        setIsEditing(false);
      }
    }
  };

  return (
    <>
      <div className="mb-4">
        <h1 className="text-2xl font-semibold mb-2">Paramètres</h1>
        <div className="flex flex-col space-y-2">
          <ToggleSwitch
            label="Audio"
            checked={haveAudio}
            onChange={handleCheckAudio}
          />
          <div>
            <label htmlFor="fps" className="mr-2">
              FPS:
            </label>
            <select
              id="fps"
              value={fps}
              onChange={(e) => setFps(Number(e.target.value))}
              className="border rounded p-1"
            >
              <option value={24}>24</option>
              <option value={30}>30</option>
              <option value={60}>60</option>
            </select>
          </div>
          <div>
            <label htmlFor="resolution" className="mr-2">
              Résolution:
            </label>
            <select
              id="resolution"
              value={resolution}
              onChange={(e) => setResolution(e.target.value)}
              className="border rounded p-1"
            >
              <option value="1280x720">720p</option>
              <option value="1920x1080">1080p</option>
              <option value="2560x1440">1440p</option>
              <option value="3840x2160">4K</option>
            </select>
          </div>
          <div>
            <label htmlFor="bitrate" className="mr-2">
              Bitrate (kbps):
            </label>
            <input
              id="bitrate"
              type="number"
              value={bitrate / 1000}
              onChange={(e) => setBitrate(Number(e.target.value) * 1000)}
              className="border rounded p-1 w-24"
              min="1000"
              max="8000"
              step="500"
            />
          </div>
        </div>
      </div>
      <div className="mb-4">
        <button
          className="bg-green-500 text-white text-2xl px-4 py-2 rounded"
          onClick={startScreenRecording}
        >
          Démarrer l'enregistrement
        </button>
        <button
          className="bg-red-500 text-white text-2xl px-4 py-2 rounded ml-4"
          onClick={() => recorder?.stop()}
        >
          Arrêter l'enregistrement
        </button>
      </div>
      <div className=" flex">
        <div className="mb-4">
          {editedVideoUrl && (
            <h2 className="text-xl font-semibold mb-2">Vidéo original :</h2>
          )}
          <video ref={screenRecording} height={300} width={600} controls />
        </div>
        <div className="mb-4">
          <button
            className="bg-purple-500 text-white text-2xl px-4 py-2 rounded"
            onClick={editVideo}
            disabled={isEditing}
          >
            {isEditing ? "Édition en cours..." : "Éditer la vidéo"}
          </button>
        </div>
        {editedVideoUrl && (
          <div>
            <h2 className="text-xl font-semibold mb-2">Vidéo éditée :</h2>
            <video src={editedVideoUrl} height={300} width={600} controls />
          </div>
        )}
      </div>
    </>
  );
};

export default ScreenRecorder;
