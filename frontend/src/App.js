import React, { useEffect, useRef, useState } from 'react';
import './App.css';
import axios from "axios";

const App = () => {
  const [chat, setChat] = useState([]);
  const [status, setStatus] = useState("▶️ ಆರಂಭಿಸಲು ಸ್ಟಾರ್ಟ್‌ ಬಟನ್‌ ಒತ್ತಿ");
  const [appState, setAppState] = useState("idle");
  const [showFeedback, setShowFeedback] = useState(false);
  const [feedbackText, setFeedbackText] = useState("");
  const [hasInteracted, setHasInteracted] = useState(false);

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const isRunningRef = useRef(false);
  const silenceTimerRef = useRef(null);
  const audioContextRef = useRef(null);
  const sourceRef = useRef(null);
  const analyserRef = useRef(null);
  const dataArrayRef = useRef(null);
  const volumeHistory = useRef([]);

  const startRecording = async () => {
    setShowFeedback(false);
    setFeedbackText("");
    setHasInteracted(true);

    setAppState("listening");
    setStatus("🎤 ಧ್ವನಿಯನ್ನು ಕೇಳುತ್ತಿದೆ...");
    isRunningRef.current = true;
    audioChunksRef.current = [];
    volumeHistory.current = [];

    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    audioContextRef.current = new AudioContext();
    sourceRef.current = audioContextRef.current.createMediaStreamSource(stream);
    analyserRef.current = audioContextRef.current.createAnalyser();
    sourceRef.current.connect(analyserRef.current);
    dataArrayRef.current = new Uint8Array(analyserRef.current.fftSize);

    detectSilence();

    const recorder = new MediaRecorder(stream);
    mediaRecorderRef.current = recorder;

    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) {
        audioChunksRef.current.push(e.data);
      }
    };

    recorder.start();
  };

  const handleSilentSubmit = async () => {
    if (!mediaRecorderRef.current || mediaRecorderRef.current.state !== "recording") return;

    mediaRecorderRef.current.stop();

    mediaRecorderRef.current.onstop = async () => {
      isRunningRef.current = false;

      if (audioChunksRef.current.length === 0) return;

      const avgVolume = volumeHistory.current.reduce((a, b) => a + b, 0) / volumeHistory.current.length;
      if (avgVolume < 5) {
        setStatus("⚠️ ಧ್ವನಿ ಪತ್ತೆಯಾಗಿಲ್ಲ.");
        setAppState("idle");
        return;
      }

      const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
      const formData = new FormData();
      formData.append('file', blob, 'audio.webm');

      setAppState("processing");
      setStatus("🔄 ಪ್ರಕ್ರಿಯೆ ನಡೆಯುತ್ತಿದೆ...");

      try {
        const res = await fetch("https://kannada-chatbot.onrender.com/voice", {
          method: 'POST',
          body: formData,
        });

        const data = await res.json();
        setChat((prev) => [...prev, { user: data.user_text, bot: data.bot_text }]);

        setAppState("speaking");
        setStatus("🤖 ಉತ್ತರ ನೀಡುತ್ತಿದೆ...");

        const audio = new Audio(data.audio_url);
        audio.play();

        audio.onended = () => {
          setStatus("🎤 ಮತ್ತೆ ಕೇಳುತ್ತಿದೆ...");
          startRecording(); // auto-restart
        };
      } catch (err) {
        console.error('❌ Backend error:', err);
        setStatus("❌ ದೋಷವಾಯಿತು.");
        setAppState("idle");
      }
    };
  };

  const stopRecording = async (shouldClear = true) => {
    setAppState("idle");
    setStatus("🛑 ಧ್ವನಿ ನಿಲ್ಲಿಸಲಾಗಿದೆ...");
    isRunningRef.current = false;
    setShowFeedback(true);

    if (mediaRecorderRef.current?.state === "recording") {
      mediaRecorderRef.current.stop();
    }

    if (audioContextRef.current && audioContextRef.current.state !== "closed") {
      try {
        await audioContextRef.current.close();
        audioContextRef.current = null;
      } catch (err) {
        console.warn("⚠️ AudioContext close error:", err.message);
      }
    }

    clearTimeout(silenceTimerRef.current);

    if (shouldClear) {
      try {
        const res = await axios.post("https://kannada-chatbot.onrender.com/clear_chat");
        console.log("[CLEAR] Response from server:", res.data);
      } catch (err) {
        console.error("[CLEAR] Failed to clear chat history:", err);
      }
    }
  };

  const detectSilence = () => {
    const checkSilence = () => {
      if (!analyserRef.current) return;

      analyserRef.current.getByteTimeDomainData(dataArrayRef.current);
      const maxVolume = Math.max(...dataArrayRef.current);
      const normalized = Math.abs(maxVolume - 128);
      volumeHistory.current.push(normalized);

      if (normalized < 5) {
        if (!silenceTimerRef.current) {
          silenceTimerRef.current = setTimeout(() => {
            handleSilentSubmit(); // ✅ only process, don't show feedback or clear chat
          }, 2000);
        }
      } else {
        if (silenceTimerRef.current) {
          clearTimeout(silenceTimerRef.current);
          silenceTimerRef.current = null;
        }
      }

      if (isRunningRef.current) {
        requestAnimationFrame(checkSilence);
      }
    };

    requestAnimationFrame(checkSilence);
  };

  useEffect(() => {
    return () => {
      if (mediaRecorderRef.current?.state === "recording") {
        mediaRecorderRef.current.stop();
      }
      if (audioContextRef.current && audioContextRef.current.state !== "closed") {
        audioContextRef.current.close().catch(err =>
          console.warn("AudioContext close error on unmount:", err)
        );
      }
      clearTimeout(silenceTimerRef.current);
    };
  }, []);

  const renderStatusAnimation = () => {
    switch (appState) {
      case "listening":
        return <div className="status-box listening">🎤 ಕೇಳುತ್ತಿದೆ...</div>;
      case "processing":
        return <div className="status-box processing">🔄 ಪ್ರಕ್ರಿಯೆ ನಡೆಯುತ್ತಿದೆ...</div>;
      case "speaking":
        return <div className="status-box speaking">🗣️ ಉತ್ತರ ನೀಡುತ್ತಿದೆ...</div>;
      default:
        return <div className="status-box idle">▶️ ಮಾತನಾಡಲು ಪ್ರಾರಂಭಿಸಿ ಬಟನ್ ಒತ್ತಿ</div>;
    }
  };

  return (
    <div className="app-container">
      <div className="caution-footer">
        ⚠️ ಎಚ್ಚರಿಕೆ: ಈ ಚಾಟ್‌ಬಾಟ್ ಉತ್ತರಗಳು ಯಾವಾಗಲೂ ನಿಖರವಾಗಿಲ್ಲ. ತಪ್ಪಾದ ಮಾಹಿತಿ ಸಾಧ್ಯ. ದಯವಿಟ್ಟು ಖಚಿತಪಡಿಸಿಕೊಳ್ಳಿ.
      </div>

      <div className="sticky-top">
        {renderStatusAnimation()}
        <div className="btn-group">
          <button onClick={startRecording}>▶️ ಪ್ರಾರಂಭಿಸಿ</button>
          <button onClick={stopRecording}>🟥 ನಿಲ್ಲಿಸಿ</button>
        </div>
      </div>

      <div className="chat-container">
        {chat.map((item, i) => (
          <div key={i} className="chat-bubble">
            <p><b>🙋‍♂️ ನೀವು:</b> {item.user}</p>
            <p><b>🤖 ಜಿಪಿಟಿ:</b> {item.bot}</p>
          </div>
        ))}
      </div>

      {hasInteracted && appState === "idle" && showFeedback && (
        <div className="feedback-overlay">
          <div className="feedback-popup">
            <h3>💬 ನಿಮ್ಮ ಅಭಿಪ್ರಾಯವನ್ನು ನಮಗೆ ತಿಳಿಸಿ:</h3>
            <textarea
              rows={4}
              placeholder="ಇಲ್ಲಿ ನಿಮ್ಮ ಅಭಿಪ್ರಾಯವನ್ನು ಬರೆಯಿರಿ..."
              value={feedbackText}
              onChange={(e) => setFeedbackText(e.target.value)}
            />
            <div className="feedback-buttons">
              <button
                onClick={async () => {
                  if (!feedbackText.trim()) return;
                  try {
                    await axios.post("https://kannada-chatbot.onrender.com/submit_feedback", {
                      feedback: feedbackText,
                      timestamp: new Date().toISOString(),
                    });
                  
                    alert("🙏 ಧನ್ಯವಾದಗಳು! ನಿಮ್ಮ ಅಭಿಪ್ರಾಯವನ್ನು ಪಡೆದುಕೊಂಡೆವು.");
                    setFeedbackText("");
                    setShowFeedback(false);
                  } catch (err) {
                    alert("❌ ಅಭಿಪ್ರಾಯ ಕಳುಹಿಸುವಲ್ಲಿ ದೋಷವಾಯಿತು.");
                    console.error("Feedback error:", err);
                  }
                }}
              >
                ✉️ ಕಳುಹಿಸಿ
              </button>
              <button onClick={() => setShowFeedback(false)}>❌ ಮುಚ್ಚು</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default App;
