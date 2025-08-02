import speech_recognition as sr
from deep_translator import GoogleTranslator
from pydub import AudioSegment
import os

def get_kannada_voice_input(audio_file_path):
    recognizer = sr.Recognizer()

    try:
        # Convert MP3 to WAV if needed
        if audio_file_path.endswith(".mp3"):
            audio = AudioSegment.from_mp3(audio_file_path)
            wav_path = audio_file_path.replace(".mp3", ".wav")
            audio.export(wav_path, format="wav")
            audio_file_path = wav_path

        # Read audio
        with sr.AudioFile(audio_file_path) as source:
            audio_data = recognizer.record(source)

        # Step 1: Speech-to-Text (Kannada)
        kannada_text = recognizer.recognize_google(audio_data, language="kn-IN")
        print("🗣️ Recognized Kannada Text:", kannada_text)

        # Step 2: Translate Kannada → English
        english_text = GoogleTranslator(source='kn', target='en').translate(kannada_text)
        print("🌐 Translated English Text:", english_text)

        return english_text, kannada_text

    except sr.UnknownValueError:
        print("⚠️ Could not understand audio.")
    except sr.RequestError as e:
        print("❌ API request error:", e)
    except Exception as e:
        print("❌ Unexpected error:", e)

    return None, None
