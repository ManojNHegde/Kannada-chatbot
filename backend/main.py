from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid
import subprocess
import traceback
import speech_recognition as sr
from gtts import gTTS
from qa_chain import ask_llama  # Your custom QA function
from translator import translate_en_to_kn  # English to Kannada translation
from fastapi import  BackgroundTasks
import time
from fastapi import  Request
import json
from datetime import datetime


app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware




# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://your-frontend.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directories
UPLOAD_DIR = "uploads"
AUDIO_OUT_DIR = "static/audio"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(AUDIO_OUT_DIR, exist_ok=True)
print("Hi startes")
@app.post("/voice")
async def handle_voice(file: UploadFile = File(...)):
    input_path = None
    wav_path = None
    output_audio_path = None
    try:
        # Step 1: Save uploaded audio
        ext = file.filename.split('.')[-1]
        file_id = str(uuid.uuid4())
        input_path = os.path.join(UPLOAD_DIR, f"{file_id}.{ext}")
        print(f"[UPLOAD] Saving file as: {input_path}")
        with open(input_path, "wb") as f:
            f.write(await file.read())

        # Step 2: Convert to WAV if needed
        if not input_path.endswith(".wav"):
            wav_path = input_path.replace(f".{ext}", ".wav")
            print(f"[CONVERT] Converting to WAV: {wav_path}")
            subprocess.run(["ffmpeg", "-i", input_path, wav_path, "-y"], check=True)
        else:
            wav_path = input_path
        print("[CONVERT] Conversion done.")

        # Step 3: Kannada Speech Recognition
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
            print("[SPEECH] Performing recognition...")
            user_text = recognizer.recognize_google(audio_data, language="kn-IN")
        print(f"[SPEECH] User said: {user_text}")

        # Step 4: LLM Response
        print("[LLM] Sending to LLaMA/LLM...")
        bot_reply = ask_llama(user_text)
        print(f"[LLM] English reply: {bot_reply}")

        # Step 5: Translate to Kannada
        print("[TRANSLATE] Translating to Kannada...")
        kannada_reply = translate_en_to_kn(bot_reply)
        print(f"[TRANSLATE] Kannada reply: {kannada_reply}")

        # Step 6: Convert Kannada text to audio
        output_audio_path = os.path.join(AUDIO_OUT_DIR, f"{file_id}.mp3")
        tts = gTTS(kannada_reply, lang='kn')
        tts.save(output_audio_path)
        print(f"[AUDIO] Saved to: {output_audio_path}")

        # Step 7: Prepare response before deleting
        response_data = {
            "user_text": user_text,
            "bot_text": kannada_reply,
            "audio_url": f"https://kannada-chatbot.onrender.com/static/audio/{file_id}.mp3"
        }

        # Delay return to ensure frontend can fetch the audio before deletion
        # Optional: Wait a bit (like 2 seconds) if needed by frontend design

        return JSONResponse(response_data)

    except sr.UnknownValueError:
        print("[ERROR] Could not understand audio.")
        return JSONResponse({"error": "Could not understand the audio."}, status_code=400)
    except subprocess.CalledProcessError:
        print("[ERROR] Audio conversion failed.")
        return JSONResponse({"error": "Audio conversion failed."}, status_code=500)
    except Exception as e:
        print("[ERROR] Exception occurred:")
        traceback.print_exc()
        return JSONResponse({"error": str(e)}, status_code=500)
    

@app.post("/clear_chat")
async def clear_chat():
    try:
        file_path = "conversation_history.txt"
        # Clear contents if file exists
        if os.path.exists(file_path):
            open(file_path, 'w').close()
            print("[CLEAR] conversation_history.txt cleared.")
            return JSONResponse({"message": "Chat history cleared successfully."})
        else:
            print("[CLEAR] File does not exist. Nothing to clear.")
            return JSONResponse({"message": "File not found. Nothing to clear."}, status_code=404)
    except Exception as e:
        print(f"[ERROR] Failed to clear chat history: {str(e)}")
        return JSONResponse({"error": "Failed to clear chat history."}, status_code=500)


@app.get("/static/audio/{filename}")
async def get_audio(filename: str):
    path = os.path.join(AUDIO_OUT_DIR, filename)
    if not os.path.exists(path):
        print(f"[404] Audio file not found: {filename}")
        return JSONResponse({"error": "File not found"}, status_code=404)
    print(f"[200] Serving audio file: {filename}")
    return FileResponse(path)

def delete_files_in_directory(directory):
    if not os.path.exists(directory):
        print(f"[SKIP] Directory does not exist: {directory}")
        return

    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            try:
                os.remove(file_path)
                print(f"[DELETE] Removed file: {file_path}")
            except Exception as e:
                print(f"[ERROR] Could not delete {file_path}: {e}")
        else:
            print(f"[SKIP] Not a file: {file_path}")

# @app.post("/clear_chat")
# async def clear_chat():
#     try:
#         history_file = "conversation_history.txt"
#         if os.path.exists(history_file):
#             with open(history_file, 'w') as f:
#                 f.truncate(0)
#             print(f"[CLEAR] {history_file} cleared.")
#         else:
#             print(f"[CLEAR] {history_file} does not exist.")

#         for dir_path in [UPLOAD_DIR, AUDIO_OUT_DIR]:
#             if os.path.exists(dir_path):
#                 print(f"[CLEANUP] Looking inside: {dir_path}")
#                 for filename in os.listdir(dir_path):
#                     file_path = os.path.join(dir_path, filename)
#                     if os.path.isfile(file_path):
#                         try:
#                             os.remove(file_path)
#                             print(f"[CLEANUP] Deleted file: {file_path}")
#                         except Exception as e:
#                             print(f"[CLEANUP ERROR] Failed to delete {file_path}: {e}")
#                     else:
#                         print(f"[SKIP] Not a file: {file_path}")
#             else:
#                 print(f"[CLEANUP] Directory does not exist: {dir_path}")

#         return JSONResponse({"message": "Chat history and audio files cleared successfully."})

#     except Exception as e:
#         print(f"[ERROR] Failed to clear chat/audio: {str(e)}")
#         return JSONResponse({"error": "Failed to clear chat/audio."}, status_code=500)


def delete_files_in_directory(directory):
    if not os.path.exists(directory):
        print(f"[SKIP] Directory does not exist: {directory}")
        return

    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            try:
                os.remove(file_path)
                print(f"[DELETE] Removed file: {file_path}")
            except Exception as e:
                print(f"[ERROR] Could not delete {file_path}: {e}")
        else:
            print(f"[SKIP] Not a file: {file_path}")

@app.post("/force_cleanup")
async def force_cleanup():
    try:
        print("[START] Cleaning files from uploads and static/audio...")
        delete_files_in_directory(UPLOAD_DIR)
        delete_files_in_directory(AUDIO_OUT_DIR)
        print("[DONE] Cleanup successful.")
        return JSONResponse({"message": "All temporary files deleted."})
    except Exception as e:
        print(f"[ERROR] Cleanup failed: {e}")
        return JSONResponse({"error": "Cleanup failed."}, status_code=500)


@app.post("/submit_feedback")
async def submit_feedback(request: Request):
    data = await request.json()
    feedback = data.get("feedback")
    timestamp = data.get("timestamp")

    entry = {
        "feedback": feedback,
        "timestamp": timestamp or str(datetime.now())
    }

    with open("feedback.txt", "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return {"message": "Feedback saved"}