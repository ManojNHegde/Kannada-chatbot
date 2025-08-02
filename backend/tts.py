import os
from gtts import gTTS
from pydub import AudioSegment
import tempfile

def speak_kannada(text, speed=1.25):
    try:
        text = text.strip()
        if not text:
            print("⚠️ Empty input to TTS")
            return None

        print(f"🔊 TTS Input: {text}")

        # Step 1: Generate MP3 using Google TTS
        tts = gTTS(text=text, lang='kn')
        temp_mp3 = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        tts.save(temp_mp3.name)

        # Step 2: Adjust playback speed (if needed)
        sound = AudioSegment.from_file(temp_mp3.name, format="mp3")
        if speed != 1.0:
            faster_sound = sound._spawn(sound.raw_data, overrides={
                "frame_rate": int(sound.frame_rate * speed)
            }).set_frame_rate(sound.frame_rate)
        else:
            faster_sound = sound

        # Step 3: Save the final audio
        temp_output = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        faster_sound.export(temp_output.name, format="mp3")

        # Step 4: Clean up intermediate file
        os.remove(temp_mp3.name)

        print(f"✅ TTS output saved: {temp_output.name}")
        return temp_output.name

    except Exception as e:
        print("❌ Error in TTS:", e)
        return None
