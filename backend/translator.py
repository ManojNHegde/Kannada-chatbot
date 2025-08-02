from deep_translator import GoogleTranslator

def translate_en_to_kn(text):
    try:
        translated = GoogleTranslator(source='en', target='kn').translate(text)
        print(f"🌐 Translated: {text} → {translated}")
        return translated
    except Exception as e:
        print("❌ Translation failed:", e)
        return "ಕ್ಷಮಿಸಿ, ಭಾಷಾಂತರದಲ್ಲಿ ದೋಷವಿದೆ."  # Fallback message in Kannada
