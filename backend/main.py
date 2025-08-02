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

from pymongo import MongoClient
import os


MONGO_URL = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URL)
db = client["kannada_bot_db"]  # Database name
feedback_collection = db["feedback"]  # Collection name



# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://kannada-chatbot.vercel.app"],
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
        
        with open(input_path, "wb") as f:
            f.write(await file.read())

        # Step 2: Convert to WAV if needed
        if not input_path.endswith(".wav"):
            wav_path = input_path.replace(f".{ext}", ".wav")
            subprocess.run(["ffmpeg", "-i", input_path, wav_path, "-y"], check=True)
        else:
            wav_path = input_path

        # Step 3: Kannada Speech Recognition
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
           
            user_text = recognizer.recognize_google(audio_data, language="kn-IN")
        
        # Step 4: LLM Response
        
        bot_reply = ask_llama(user_text)
        

        # Step 5: Translate to Kannada
     
        kannada_reply = translate_en_to_kn(bot_reply)
        

        # Step 6: Convert Kannada text to audio
        output_audio_path = os.path.join(AUDIO_OUT_DIR, f"{file_id}.mp3")
        tts = gTTS(kannada_reply, lang='kn')
        tts.save(output_audio_path)
       

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
        
        return JSONResponse({"error": "Could not understand the audio."}, status_code=400)
    except subprocess.CalledProcessError:
        
        return JSONResponse({"error": "Audio conversion failed."}, status_code=500)
    except Exception as e:
      
        traceback.print_exc()
        return JSONResponse({"error": str(e)}, status_code=500)
    

@app.post("/clear_chat")
async def clear_chat():
    try:
        file_path = "conversation_history.txt"
        # Clear contents if file exists
        if os.path.exists(file_path):
            open(file_path, 'w').close()
           
            return JSONResponse({"message": "Chat history cleared successfully."})
        else:
            
            return JSONResponse({"message": "File not found. Nothing to clear."}, status_code=404)
    except Exception as e:
      
        return JSONResponse({"error": "Failed to clear chat history."}, status_code=500)


@app.get("/static/audio/{filename}")
async def get_audio(filename: str):
    path = os.path.join(AUDIO_OUT_DIR, filename)
    if not os.path.exists(path):
      
        return JSONResponse({"error": "File not found"}, status_code=404)
  
    return FileResponse(path)

# def delete_files_in_directory(directory):
#     if not os.path.exists(directory):
#         print(f"[SKIP] Directory does not exist: {directory}")
#         return

#     for filename in os.listdir(directory):
#         file_path = os.path.join(directory, filename)
#         if os.path.isfile(file_path):
#             try:
#                 os.remove(file_path)
#                 print(f"[DELETE] Removed file: {file_path}")
#             except Exception as e:
#                 print(f"[ERROR] Could not delete {file_path}: {e}")
#         else:
#             print(f"[SKIP] Not a file: {file_path}")

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
     
        delete_files_in_directory(UPLOAD_DIR)
        delete_files_in_directory(AUDIO_OUT_DIR)
      
        return JSONResponse({"message": "All temporary files deleted."})
    except Exception as e:
  
        return JSONResponse({"error": "Cleanup failed."}, status_code=500)



from datetime import datetime
import pytz

@app.post("/submit_feedback")
async def save_feedback(request: Request):
    try:
        

        data = await request.json()
        

        feedback = data.get("feedback", "")
        timestamp = data.get("timestamp", "")

        if not feedback:
            return JSONResponse(status_code=400, content={"status": "fail", "message": "No feedback provided"})

        # Convert timestamp to IST
        try:
            utc_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            ist_time = utc_time.astimezone(pytz.timezone("Asia/Kolkata"))
        except Exception as time_error:
            return JSONResponse(status_code=400, content={"status": "fail", "message": "Invalid timestamp"})

       
        feedback_collection.insert_one({
            "message": feedback,
            "timestamp": ist_time.isoformat()
        })

       
        return {"status": "success", "message": "Feedback saved to MongoDB"}

    except Exception as e:
        
        return JSONResponse(status_code=500, content={"status": "error", "message": "Internal Server Error"})



