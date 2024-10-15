from typing import Union
from fastapi import FastAPI, File, UploadFile

from subtitles_translator.available_languages import AvailableLanguages
from subtitles_translator.subtitles import Subtitles
from subtitles_translator.translator import Translator

import uuid
import time
import os
import requests

app = FastAPI()

languagePool = ["fr","en", "es", "de", "ru", "ar", "hi", "it", "zh", "nl", "pt"]
    
lp = [
  [
    "ar",
    "de"
  ],
  [
    "ar",
    "en"
  ],
  [
    "ar",
    "es"
  ],
  [
    "ar",
    "fr"
  ],
  [
    "ar",
    "it"
  ],
  [
    "ar",
    "ru"
  ],
  [
    "de",
    "ar"
  ],
  [
    "de",
    "en"
  ],
  [
    "de",
    "es"
  ],
  [
    "de",
    "fr"
  ],
  [
    "de",
    "it"
  ],
  [
    "de",
    "nl"
  ],
  [
    "de",
    "zh"
  ],
  [
    "en",
    "ar"
  ],
  [
    "en",
    "de"
  ],
  [
    "en",
    "es"
  ],
  [
    "en",
    "fr"
  ],
  [
    "en",
    "hi"
  ],
  [
    "en",
    "it"
  ],
  [
    "en",
    "nl"
  ],
  [
    "en",
    "ru"
  ],
  [
    "en",
    "zh"
  ],
  [
    "es",
    "ar"
  ],
  [
    "es",
    "de"
  ],
  [
    "es",
    "en"
  ],
  [
    "es",
    "fr"
  ],
  [
    "es",
    "it"
  ],
  [
    "es",
    "nl"
  ],
  [
    "es",
    "ru"
  ],
  [
    "fr",
    "ar"
  ],
  [
    "fr",
    "de"
  ],
  [
    "fr",
    "en"
  ],
  [
    "fr",
    "es"
  ],
  [
    "fr",
    "ru"
  ],
  [
    "hi",
    "en"
  ],
  [
    "it",
    "ar"
  ],
  [
    "it",
    "de"
  ],
  [
    "it",
    "en"
  ],
  [
    "it",
    "es"
  ],
  [
    "it",
    "fr"
  ],
  [
    "nl",
    "en"
  ],
  [
    "nl",
    "es"
  ],
  [
    "nl",
    "fr"
  ],
  [
    "ru",
    "ar"
  ],
  [
    "ru",
    "en"
  ],
  [
    "ru",
    "es"
  ],
  [
    "ru",
    "fr"
  ],
  [
    "zh",
    "de"
  ],
  [
    "zh",
    "en"
  ],
  [
    "zh",
    "it"
  ],
  [
    "zh",
    "nl"
  ]
]

@app.get("/existing_language_pairs/cached")
def get_language_pairs():
    global lp
    return lp

def check_language_pair_exists(lang1: str, lang2: str) -> bool:
    """
    Check if a language pair exists on the Hugging Face page.

    Args:
    lang1 (str): The source language code.
    lang2 (str): The target language code.

    Returns:
    bool: True if the language pair exists, False otherwise.
    """
    base_url = "https://huggingface.co/Helsinki-NLP/opus-mt-{}-{}".format(lang1.lower(), lang2.lower())
    
    try:
        response = requests.get(base_url)
        return response.status_code == 200
    except requests.RequestException:
        return False

        
@app.get("/existing_language_pairs")
def get_existing_language_pairs(delay = 1.0):
    """
    Get all existing language pairs from the language pool.

    Returns:
    List[tuple[str, str]]: A list of tuples containing valid language pairs.
    """
    existing_pairs = []
    for lang1 in languagePool:
        for lang2 in languagePool:
            if lang1 != lang2 and check_language_pair_exists(lang1, lang2):
                existing_pairs.append((lang1, lang2))
                print("found pair" + lang1 + "-" + lang2)
                time.sleep(delay)
    return sorted(existing_pairs)

# Helper function to generate all possible pairs
def generate_all_pairs(pool: list[str]) -> list[tuple[str, str]]:
    pairs = []
    for i in range(len(pool)):
        for j in range(i+1, len(pool)):
            pairs.append((pool[i], pool[j]))
            print("pool")
    return pairs

# Helper function to filter existing pairs
def filter_existing_pairs(all_pairs: list[tuple[str, str]]) -> list[tuple[str, str]]:
    existing_pairs = []
    for pair in all_pairs:
        if check_language_pair_exists(pair[0], pair[1]):
            existing_pairs.append(pair)
    return existing_pairs

# Update the existing_language_pairs route
@app.get("/existing_language_pairs")
def get_existing_language_pairs():
    all_pairs = generate_all_pairs(languagePool)
    return filter_existing_pairs(all_pairs)

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