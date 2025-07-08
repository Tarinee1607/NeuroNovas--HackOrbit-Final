from googletrans import Translator

translator = Translator()

def detect_lang(text):
    try:
        return translator.detect(text).lang
    except:
        return 'en'  # default to English

def translate_english(text):
    return translator.translate(text, src='auto', dest='en').text

def translate_hindi(text):
    return translator.translate(text, src='en', dest='hi').text
