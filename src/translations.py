from deep_translator import GoogleTranslator

def translate_text(text, dest_lang='en', src_lang='auto'):
    """
    Translate text to the specified language using Google Translate.
    
    Args:
        text (str): The text to translate
        dest_lang (str): The target language code (e.g., 'es' for Spanish)
        src_lang (str): The source language code (default: 'auto' for auto-detection)
        
    Returns:
        str: The translated text or original text if translation fails
    """
    if not text or not isinstance(text, str):
        return text
        
    try:
        translator = GoogleTranslator(source=src_lang, target=dest_lang)
        translation = translator.translate(text)
        return translation
    except Exception as e:
        print(f"Translation error: {e}")
        # Return the original text if translation fails
        return text
