from typing import Union, List, Annotated
from fastapi import FastAPI, File, UploadFile, Query
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

# Check if GPU usage is enabled and set GPU as default tensor type if available
if os.environ.get('USE_GPU', 'false') == 'true':
    import torch
    torch.set_default_tensor_type('torch.cuda.FloatTensor')

# Set up logger for logging info and errors
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Initialize FastAPI app
app = FastAPI()

# Language pool from which we will select languages for translation
# (based on Helsinki-NLP models for translation available via Hugging Face)
languagePool = [
    'aav', 'aed', 'af', 'alv', 'am', 'ar', 'art', 'ase', 'az', 'bat', 'bcl', 'be', 'bem', 'ber', 'bg', 
    'bi', 'bn', 'bnt', 'bzs', 'ca', 'cau', 'ccs', 'ceb', 'cel', 'chk', 'cpf', 'crs', 'cs', 'csg', 
    'csn', 'cus', 'cy', 'da', 'de', 'dra', 'ee', 'efi', 'el', 'en', 'eo', 'es', 'et', 'eu', 'euq', 
    'fi', 'fj', 'fr', 'fse', 'ga', 'gaa', 'gil', 'gl', 'grk', 'guw', 'gv', 'ha', 'he', 'hi', 'hil', 
    'ho', 'hr', 'ht', 'hu', 'hy', 'id', 'ig', 'ilo', 'is', 'iso', 'it', 'ja', 'jap', 'ka', 'kab', 
    'kg', 'kj', 'kl', 'ko', 'kqn', 'kwn', 'kwy', 'lg', 'ln', 'loz', 'lt', 'lu', 'lua', 'lue', 'lun', 
    'luo', 'lus', 'lv', 'map', 'mfe', 'mfs', 'mg', 'mh', 'mk', 'mkh', 'ml', 'mos', 'mr', 'ms', 'mt', 
    'mul', 'ng', 'nic', 'niu', 'nl', 'no', 'nso', 'ny', 'nyk', 'om', 'pa', 'pag', 'pap', 'phi', 'pis', 
    'pl', 'pon', 'poz', 'pqe', 'pqw', 'prl', 'pt', 'rn', 'rnd', 'ro', 'roa', 'ru', 'run', 'rw', 'sal', 
    'sg', 'sh', 'sit', 'sk', 'sl', 'sm', 'sn', 'sq', 'srn', 'ss', 'ssp', 'st', 'sv', 'sw', 'swc', 
    'taw', 'tdt', 'th', 'ti', 'tiv', 'tl', 'tll', 'tn', 'to', 'toi', 'tpi', 'tr', 'trk', 'ts', 
    'tum', 'tut', 'tvl', 'tw', 'ty', 'tzo', 'uk', 'umb', 'ur', 've', 'vi', 'vsl', 'wa', 'wal', 'war', 
    'wls', 'xh', 'yap', 'yo', 'yua', 'zai', 'zh', 'zne'
]

def check_language_pair_exists(lang1: str, lang2: str) -> bool:
    """
    Check if a translation model exists for the language pair on Hugging Face.

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
def get_existing_language_pairs(desired_languages: Annotated[Union[list[str], None], Query()] = None, use_cache: bool = True, delay: float = 0.1):
    """
    Get all existing translation language pairs from the language pool.

    Args:
    desired_languages (Optional[List[str]]): List of desired languages to filter the pairs.
    use_cache (Optional[bool]): Whether to use cached language pairs if available.
    delay (Optional[float]): Delay between requests to avoid rate limiting when checking pairs.

    Returns:
    List[tuple[str, str]]: A list of valid language pairs.
    """
    
    print(str(desired_languages))
    if use_cache:
        try:
            # Try to use cached language pairs from a file
            with open("/code/data/language_pairs.json", "r") as file:
                logger.info("using cached language pairs")
                content = file.read()
                existing_pairs = json.loads(content)
                existing_pairs_filtered = []
                if desired_languages:
                    # Filter pairs by desired languages if specified
                    existing_pairs_filtered = [pair for pair in existing_pairs if pair[0] in desired_languages and pair[1] in desired_languages]
                else:
                    existing_pairs_filtered = existing_pairs
                return existing_pairs_filtered
        except FileNotFoundError:
            logger.info("Could not find cached language pairs")
            pass

    # Check all combinations of languages in the pool
    existing_pairs = []
    for lang1 in languagePool:
        for lang2 in languagePool:
            if lang1 != lang2 and check_language_pair_exists(lang1, lang2):
                existing_pairs.append((lang1, lang2))
                print("found pair " + lang1 + "-" + lang2)
                time.sleep(delay)

    # Cache the results in a JSON file
    output = sorted(existing_pairs)
    with open("/code/data/language_pairs.json", "w") as file:
        file.write(json.dumps(output))

    # Filter the pairs based on the desired languages
    filtered_output = []
    if desired_languages:
        filtered_output = [pair for pair in output if pair[0] in desired_languages and pair[1] in desired_languages]
    else:
        filtered_output = output

    return filtered_output

def generate_all_pairs(pool: list[str]) -> list[tuple[str, str]]:
    """
    Generate all possible language pairs from a list of languages.

    Args:
    pool (list[str]): List of language codes.

    Returns:
    list[tuple[str, str]]: List of language pairs.
    """
    pairs = []
    for i in range(len(pool)):
        for j in range(i + 1, len(pool)):
            pairs.append((pool[i], pool[j]))
    return pairs

def filter_existing_pairs(all_pairs: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """
    Filter the list of language pairs to include only those that have an existing translation model.

    Args:
    all_pairs (list[tuple[str, str]]): List of language pairs to check.

    Returns:
    list[tuple[str, str]]: List of existing language pairs.
    """
    existing_pairs = []
    for pair in all_pairs:
        if check_language_pair_exists(pair[0], pair[1]):
            existing_pairs.append(pair)
    return existing_pairs

@app.get("/existing_language_pairs")
def get_existing_language_pairs():
    """
    Get all valid existing language pairs from the language pool.
    
    The first time this endpoint is called, it will check all possible language pairs, so it will take some time.

    Returns:
    List[tuple[str, str]]: List of existing language pairs.
    """
    all_pairs = generate_all_pairs(languagePool)
    return filter_existing_pairs(all_pairs)

@app.post("/translate_srt/{language_from}/{language_to}")
async def translate_srt(language_from: str, language_to: str, file: UploadFile):
    """
    Translate a subtitle file (.srt) from one language to another.

    Args:
    language_from (str): The source language code.
    language_to (str): The target language code.
    file (UploadFile): The subtitle file to translate.

    Returns:
    dict: A dictionary containing the translated subtitle file.
    """
    
    # Initialize translation using provided languages
    original_language = AvailableLanguages(language_from)
    target_language = AvailableLanguages(language_to)
    translator = Translator(original_language, target_language)

    # Read and decode the content of the subtitle file
    content = await file.read()
    content = content.decode('utf-8')

    # Load the subtitles, translate them, and save to a new file
    subtitles = Subtitles(content.splitlines())
    translator.translate_subtitles(subtitles)
    file_name = f"{uuid.uuid4()}.srt"
    subtitles.save_srt(file_name)

    # Return the translated subtitle file and clean up the file
    with open(file_name, "rb") as file:
        translated_srt = file.read()
    os.remove(file_name)
    return {"translated_srt": translated_srt}
