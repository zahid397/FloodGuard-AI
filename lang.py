# lang.py
# FloodGuard-AI Language Module
# Author: Zahid Hasan

from langdetect import detect
import json

def detect_language(text):
    """
    Detects the language of given text input.
    Supports offline detection using langdetect library.
    """
    try:
        lang = detect(text)
        return lang
    except Exception as e:
        return f"Error: {str(e)}"

def flood_message_by_language(text):
    """
    Returns a response related to flood warning in user's language.
    """
    lang = detect_language(text)
    
    responses = {
        'en': "Flood alert! Please move to higher ground immediately.",
        'bn': "বন্যা সতর্কবার্তা! দয়া করে দ্রুত উঁচু স্থানে চলে যান।",
        'hi': "बाढ़ की चेतावनी! कृपया तुरंत ऊँचे स्थान पर जाएँ।"
    }
    
    return responses.get(lang, responses['en'])

if __name__ == "__main__":
    while True:
        user_input = input("Enter message: ")
        if user_input.lower() in ["exit", "quit"]:
            break
        print(flood_message_by_language(user_input))
