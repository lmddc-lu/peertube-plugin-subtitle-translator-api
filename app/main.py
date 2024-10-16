from typing import Union
from fastapi import FastAPI, File, UploadFile
from pydantic import Field
from typing import Optional

from subtitles_translator.available_languages import AvailableLanguages
from subtitles_translator.subtitles import Subtitles
from subtitles_translator.translator import Translator

import uuid
import time
import os
import requests
import logging
import json

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


app = FastAPI()

#From: https://github.com/UKPLab/EasyNMT?tab=readme-ov-file#opus-mt
# languagePool = ['aav', 'aed', 'af', 'alv', 'am', 'ar', 'art', 'ase', 'az', 'bat', 'bcl', 'be', 'bem', 'ber', 'bg', 'bi', 'bn', 'bnt', 'bzs', 'ca', 'cau', 'ccs', 'ceb', 'cel', 'chk', 'cpf', 'crs', 'cs', 'csg', 'csn', 'cus', 'cy', 'da', 'de', 'dra', 'ee', 'efi', 'el', 'en', 'eo', 'es', 'et', 'eu', 'euq', 'fi', 'fj', 'fr', 'fse', 'ga', 'gaa', 'gil', 'gl', 'grk', 'guw', 'gv', 'ha', 'he', 'hi', 'hil', 'ho', 'hr', 'ht', 'hu', 'hy', 'id', 'ig', 'ilo', 'is', 'iso', 'it', 'ja', 'jap', 'ka', 'kab', 'kg', 'kj', 'kl', 'ko', 'kqn', 'kwn', 'kwy', 'lg', 'ln', 'loz', 'lt', 'lu', 'lua', 'lue', 'lun', 'luo', 'lus', 'lv', 'map', 'mfe', 'mfs', 'mg', 'mh', 'mk', 'mkh', 'ml', 'mos', 'mr', 'ms', 'mt', 'mul', 'ng', 'nic', 'niu', 'nl', 'no', 'nso', 'ny', 'nyk', 'om', 'pa', 'pag', 'pap', 'phi', 'pis', 'pl', 'pon', 'poz', 'pqe', 'pqw', 'prl', 'pt', 'rn', 'rnd', 'ro', 'roa', 'ru', 'run', 'rw', 'sal', 'sg', 'sh', 'sit', 'sk', 'sl', 'sm', 'sn', 'sq', 'srn', 'ss', 'ssp', 'st', 'sv', 'sw', 'swc', 'taw', 'tdt', 'th', 'ti', 'tiv', 'tl', 'tll', 'tn', 'to', 'toi', 'tpi', 'tr', 'trk', 'ts', 'tum', 'tut', 'tvl', 'tw', 'ty', 'tzo', 'uk', 'umb', 'ur', 've', 'vi', 'vsl', 'wa', 'wal', 'war', 'wls', 'xh', 'yap', 'yo', 'yua', 'zai', 'zh', 'zne']
languagePool = ["fr","en", "es", "de", "ru", "ar", "hi", "it", "zh", "nl", "pt"]
  

# @app.get("/existing_language_pairs/cached")
# def get_language_pairs():
#     global lp
#     return lp

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
        logger.info("checking " + base_url)
        response = requests.head(base_url)
        logger.info("response " + str(response.status_code))
        return response.status_code == 200
    except requests.RequestException:
        return False

        
@app.get("/existing_language_pairs")
def get_existing_language_pairs(use_cache : bool = True, delay: float = 0.1):
  """
  Get all existing language pairs from the language pool.

  Args:
  delay (float): Delay between requests to avoid rate limiting.
  use_cache (bool): Whether to use the cached language pairs.

  Returns:
  List[tuple[str, str]]: A list of tuples containing valid language pairs.
  """
  if use_cache:
    try:
      # Check if there is a language pair file
      with open("/code/data/language_pairs.json", "r") as file:
        content = file.read()
        existing_pairs = json.loads(content)
        return existing_pairs
    except FileNotFoundError:
      pass

  existing_pairs = []
  for lang1 in languagePool:
    for lang2 in languagePool:
      if lang1 != lang2 and check_language_pair_exists(lang1, lang2):
        existing_pairs.append((lang1, lang2))
        print("found pair " + lang1 + "-" + lang2)
        time.sleep(delay)
  output = sorted(existing_pairs)
  with open("/code/data/language_pairs.json", "w") as file:
    file.write(json.dumps(output))
  return output

# Helper function to generate all possible pairs
def generate_all_pairs(pool: list[str]) -> list[tuple[str, str]]:
    pairs = []
    for i in range(len(pool)):
      for j in range(i+1, len(pool)):
          pairs.append((pool[i], pool[j]))
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