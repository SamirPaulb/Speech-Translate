import copy
from ..helper import up_first_case, get_similar_in_list
from whisper.tokenizer import TO_LANGUAGE_CODE
from typing import Dict

from deep_translator import MyMemoryTranslator, GoogleTranslator
from loguru import logger

# * using deep_translator v1.11.1
# * v1.11.4 seems to add weird language code for mymemory

# List of whisper languages convert fromm the keys of TO_LANGUAGE_CODE
WHISPER_LANG_LIST = list(TO_LANGUAGE_CODE.keys())
WHISPER_LANG_LIST.sort()

# List of supported languages by Google TL
GOOGLE_KEY_VAL = copy.deepcopy(GoogleTranslator().get_supported_languages(as_dict=True))
assert isinstance(GOOGLE_KEY_VAL, Dict)
GOOGLE_KEY_VAL["auto detect"] = "auto"
if "filipino" in GOOGLE_KEY_VAL.keys():
    GOOGLE_KEY_VAL["filipino (tagalog)"] = GOOGLE_KEY_VAL.pop("filipino")

# List of supported languages by MyMemoryTranslator
MYMEMORY_KEY_VAL = copy.deepcopy(MyMemoryTranslator().get_supported_languages(as_dict=True))
assert isinstance(MYMEMORY_KEY_VAL, Dict)
if "filipino" in MYMEMORY_KEY_VAL.keys():
    MYMEMORY_KEY_VAL["filipino (tagalog)"] = MYMEMORY_KEY_VAL.pop("filipino")
# remove key that gives error or invalid -> this is get from testing the key in test/test/translate.py
MYMEMORY_KEY_VAL.pop("aymara")
MYMEMORY_KEY_VAL.pop("dogri")
MYMEMORY_KEY_VAL.pop("javanese")
MYMEMORY_KEY_VAL.pop("konkani")
MYMEMORY_KEY_VAL.pop("krio")
MYMEMORY_KEY_VAL.pop("oromo")

# List of supported languages by libreTranslate. Taken from LibreTranslate.com docs v1.5.1
LIBRE_KEY_VAL = {
    "auto detect": "auto",
    "english": "en",
    "albanian": "sq",
    "arabic": "ar",
    "azerbaijani": "az",
    "bengali": "bn",
    "bulgarian": "bg",
    "catalan": "ca",
    "chinese": "zh",
    "chinese (traditional)": "zt",
    "czech": "cs",
    "danish": "da",
    "dutch": "nl",
    "esperanto": "eo",
    "finnish": "fi",
    "french": "fr",
    "german": "de",
    "greek": "el",
    "hebrew": "he",
    "hindi": "hi",
    "hungarian": "hu",
    "indonesian": "id",
    "irish": "ga",
    "italian": "it",
    "japanese": "ja",
    "korean": "ko",
    "latvian": "lv",
    "lithuanian": "lt",
    "malay": "ms",
    "norwegian": "nb",
    "persian": "fa",
    "polish": "pl",
    "portuguese": "pt",
    "romanian": "ro",
    "russian": "ru",
    "serbian": "sr",
    "slovak": "sk",
    "slovenian": "sl",
    "spanish": "es",
    "swedish": "sv",
    "tagalog": "tl",
    "thai": "th",
    "turkish": "tr",
    "ukrainian": "uk",
    "urdu": "ur",
    "vietnamese": "vi",
}


def verify_language_in_key(lang: str, engine: str) -> bool:
    """Verify if the language is in the key of the engine

    Parameters
    ----------
    lang : str
        Language to verify
    engine : str
        Engine to verify

    Returns
    -------
    bool
        True if the language is in the key of the engine

    Raises
    ------
    ValueError
        If the engine is not found

    """
    if engine == "Google Translate":
        return lang in GOOGLE_KEY_VAL.keys()
    elif engine == "LibreTranslate":
        return lang in LIBRE_KEY_VAL.keys()
    elif engine == "MyMemoryTranslator":
        return lang in MYMEMORY_KEY_VAL.keys()
    else:
        raise ValueError("Engine not found")


def get_whisper_key_from_similar(similar: str) -> str:
    """Get whisper key from similar. This is used because we want to keep the original language name for the translation engine
    So everytime we want to set the whisper language, we must call this function first to get the correct whisper key

    Parameters
    ----------
    similar : str
        Similar language

    Returns
    -------
    str
        Whisper key

    Raises
    ------
    ValueError
        If the similar language is not found

    """

    logger.debug("GETTING WHISPER KEY FROM SIMILAR LANGUAGE NAME")
    should_be_there = get_similar_in_list(WHISPER_LANG_LIST, similar.lower())

    if len(should_be_there) != 0:
        logger.debug(f"Found key {should_be_there[0]} while searching for {similar}")
        logger.debug(f"FULL KEY GET {should_be_there}")
        return should_be_there[0]
    else:
        raise ValueError(
            f"Fail to get whisper key from similar while searching for {similar}. Please report this as a bug to https://github.com/Dadangdut33/Speech-Translate/issues"
        )


# * For Target Remove any auto detect from the list
WHISPER_TARGET = ["English"]

GOOGLE_TARGET = list(GOOGLE_KEY_VAL.keys())
GOOGLE_TARGET.remove("auto detect")
GOOGLE_TARGET = [up_first_case(x) for x in GOOGLE_TARGET]
GOOGLE_TARGET.sort()

LIBRE_TARGET = list(LIBRE_KEY_VAL.keys())
LIBRE_TARGET.remove("auto detect")
LIBRE_TARGET = [up_first_case(x) for x in LIBRE_TARGET]
LIBRE_TARGET.sort()

MY_MEMORY_TARGET = list(MYMEMORY_KEY_VAL.keys())
MY_MEMORY_TARGET = [up_first_case(x) for x in MY_MEMORY_TARGET]
MY_MEMORY_TARGET.sort()
# no auto for mymemory

# * FOR TARGET LANGUAGE SELECTION
# for target language, it does not matter wether the target is compatible with whisper or not
# because in this part whisper is used for transcribing the audio only
# for whisper though, it can only translate into english
ENGINE_TARGET_DICT = {
    # selecting whisper as the tl engine
    "Tiny (~32x speed)": WHISPER_TARGET,
    "Base (~16x speed)": WHISPER_TARGET,
    "Small (~6x speed)": WHISPER_TARGET,
    "Medium (~2x speed)": WHISPER_TARGET,
    "Large (v1) (1x speed)": WHISPER_TARGET,
    "Large (v2) (1x speed)": WHISPER_TARGET,
    "Large (v3) (1x speed)": WHISPER_TARGET,
    # selecting TL API as the tl engine
    "Google Translate": GOOGLE_TARGET,
    "LibreTranslate": LIBRE_TARGET,
    "MyMemoryTranslator": MY_MEMORY_TARGET,
}

# * source engine
# For source engine we need to check wether the language is compatible with whisper or not
# if not then we remove it from the list
# we keep the original language name for the translation engine here, so that its easy to pass to the tl engine
# But we must remember that when getting the whisper key we need to use get_whisper_key_from_similar

# --- GOOGLE --- | Filtering
to_remove = []
GOOGLE_WHISPER_COMPATIBLE = GOOGLE_TARGET.copy()
for i, lang in enumerate(GOOGLE_WHISPER_COMPATIBLE):
    is_it_there = get_similar_in_list(WHISPER_LANG_LIST, lang)
    if len(is_it_there) == 0:
        to_remove.append(lang)
GOOGLE_WHISPER_COMPATIBLE = [x for x in GOOGLE_WHISPER_COMPATIBLE if x not in to_remove]

# --- LIBRE --- | Filtering
to_remove = []
LIBRE_WHISPER_COMPATIBLE = LIBRE_TARGET.copy()
for i, lang in enumerate(LIBRE_WHISPER_COMPATIBLE):
    is_it_there = get_similar_in_list(WHISPER_LANG_LIST, lang)
    if len(is_it_there) == 0:
        to_remove.append(lang)
LIBRE_WHISPER_COMPATIBLE = [x for x in LIBRE_WHISPER_COMPATIBLE if x not in to_remove]

# --- MYMEMORY --- | Filtering
to_remove = []
MYMEMORY_WHISPER_COMPATIBLE = MY_MEMORY_TARGET.copy()
for i, lang in enumerate(MYMEMORY_WHISPER_COMPATIBLE):
    is_it_there = get_similar_in_list(WHISPER_LANG_LIST, lang)
    if len(is_it_there) == 0:
        to_remove.append(lang)
MYMEMORY_WHISPER_COMPATIBLE = [x for x in MYMEMORY_WHISPER_COMPATIBLE if x not in to_remove]

# --- SOURCES ---
WHISPER_LIST_UPPED = [up_first_case(x) for x in WHISPER_LANG_LIST]
WHISPER_LIST_UPPED.sort()
WHISPER_SOURCE = ["Auto detect"] + WHISPER_LIST_UPPED

GOOGLE_LIST_UPPED = [up_first_case(x) for x in GOOGLE_WHISPER_COMPATIBLE]
GOOGLE_LIST_UPPED.sort()
GOOGLE_SOURCE = ["Auto detect"] + GOOGLE_LIST_UPPED

LIBRE_LIST_UPPED = [up_first_case(x) for x in LIBRE_WHISPER_COMPATIBLE]
LIBRE_LIST_UPPED.sort()
LIBRE_SOURCE = ["Auto detect"] + LIBRE_LIST_UPPED

MYMEMORY_SOURCE = [up_first_case(x) for x in MYMEMORY_WHISPER_COMPATIBLE]
MYMEMORY_SOURCE.sort()

# FOR SOURCE LANGUAGE SELECTION
# so the basic idea is that
# for whisper, we use the whisper source because every language from whisper can be used as source when translating using whisper
# other than that, we filter the language that is not compatible with whisper to make sure that the language is compatible
# between whisper and the engine
ENGINE_SOURCE_DICT = {
    # selecting whisper as the tl engine
    "Tiny (~32x speed)": WHISPER_SOURCE,
    "Base (~16x speed)": WHISPER_SOURCE,
    "Small (~6x speed)": WHISPER_SOURCE,
    "Medium (~2x speed)": WHISPER_SOURCE,
    "Large (v1) (1x speed)": WHISPER_SOURCE,
    "Large (v2) (1x speed)": WHISPER_SOURCE,
    "Large (v3) (1x speed)": WHISPER_SOURCE,
    # selecting TL API as the tl engine
    "Google Translate": GOOGLE_SOURCE,
    "LibreTranslate": LIBRE_SOURCE,
    "MyMemoryTranslator": MYMEMORY_SOURCE,
}
