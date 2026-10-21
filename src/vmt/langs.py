from __future__ import annotations

# ISO 639-1 -> (English name, NLLB-200 code)
LANGS: dict[str, tuple[str, str]] = {
    "en": ("English", "eng_Latn"), "fr": ("French", "fra_Latn"), "es": ("Spanish", "spa_Latn"),
    "de": ("German", "deu_Latn"), "it": ("Italian", "ita_Latn"), "nl": ("Dutch", "nld_Latn"),
    "pl": ("Polish", "pol_Latn"), "pt": ("Portuguese", "por_Latn"), "ro": ("Romanian", "ron_Latn"),
    "ar": ("Arabic", "arb_Arab"), "ur": ("Urdu", "urd_Arab"), "hi": ("Hindi", "hin_Deva"),
    "bn": ("Bengali", "ben_Beng"), "pa": ("Punjabi", "pan_Guru"), "fa": ("Persian", "pes_Arab"),
    "tr": ("Turkish", "tur_Latn"), "ru": ("Russian", "rus_Cyrl"), "uk": ("Ukrainian", "ukr_Cyrl"),
    "zh": ("Chinese", "zho_Hans"), "ja": ("Japanese", "jpn_Jpan"), "ko": ("Korean", "kor_Hang"),
    "so": ("Somali", "som_Latn"), "sw": ("Swahili", "swh_Latn"), "ta": ("Tamil", "tam_Taml"),
    "gu": ("Gujarati", "guj_Gujr"), "el": ("Greek", "ell_Grek"), "bg": ("Bulgarian", "bul_Cyrl"),
    "sv": ("Swedish", "swe_Latn"), "da": ("Danish", "dan_Latn"), "no": ("Norwegian", "nob_Latn"),
    "fi": ("Finnish", "fin_Latn"), "cs": ("Czech", "ces_Latn"), "hu": ("Hungarian", "hun_Latn"),
}


def language_name(code: str) -> str:
    return LANGS.get(code, (code,))[0]


def nllb_code(code: str) -> str:
    try:
        return LANGS[code][1]
    except KeyError:
        raise ValueError(f"No NLLB mapping for language '{code}'; use the ollama backend") from None
