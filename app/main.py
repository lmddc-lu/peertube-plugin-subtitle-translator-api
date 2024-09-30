from typing import Union
from fastapi import FastAPI, File, UploadFile

from subtitles_translator.available_languages import AvailableLanguages
from subtitles_translator.subtitles import Subtitles
from subtitles_translator.translator import Translator

import uuid
import os

app = FastAPI()


@app.get("/available_languages/{language_code}")
def get_available_languages(language_code: str):
    print(str(AvailableLanguages(language_code)))
    
    return {"language": str(AvailableLanguages(language_code))}

@app.post("/translate_srt/{language_from}/{language_to}")
async def translate_srt(language_from: str, language_to: str, file: UploadFile):
    original_language = AvailableLanguages(language_from)
    target_language = AvailableLanguages(language_to)
    translator = Translator(original_language, target_language)
    content = await file.read()
    content = content.decode('utf-8')  
    subtitles = Subtitles(content.splitlines())
    translator.translate_subtitles(subtitles)
    file_name = f"{uuid.uuid4()}.srt"
    subtitles.save_srt(file_name)
    with open(file_name, "rb") as file:
        translated_srt = file.read()
    os.remove(file_name)
    return {"translated_srt": translated_srt}