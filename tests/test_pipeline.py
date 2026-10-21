import pytest

from vmt.config import Config
from vmt.pipeline import Pipeline

from .conftest import FakeSTT, FakeTranslator, make_audio


@pytest.fixture
def clip(tmp_path):
    return make_audio(tmp_path / "v.ogg", [4, 4])


def test_french_is_translated(pipe, clip):
    r = pipe.process(clip)
    assert r.language == "fr" and r.translation == "EN(fr):bonjour tout le monde"


def test_english_skips_translation(cfg, clip):
    p = Pipeline(cfg, FakeSTT(lang="en", text="hello"), FakeTranslator())
    r = p.process(clip)
    assert r.translation is None and "translate" not in r.timings


def test_whistle_used_for_supported_language(clip):
    cfg = Config(stt={"prefer": "whistle"})
    whistle = FakeSTT("whistle", text="salut tout le monde", window=30)
    p = Pipeline(cfg, FakeSTT(), FakeTranslator(), whistle)
    assert p.process(clip).engine == "whistle"


def test_unsupported_language_goes_to_whisper(clip):
    cfg = Config(stt={"prefer": "whistle"})
    p = Pipeline(cfg, FakeSTT(lang="ur", text="x y z"), FakeTranslator(),
                 FakeSTT("whistle", window=30))
    assert p.process(clip).engine == "whisper"


def test_bad_whistle_output_falls_back(tmp_path):
    clip = make_audio(tmp_path / "long.ogg", [12])
    cfg = Config(stt={"prefer": "whistle"})
    p = Pipeline(cfg, FakeSTT(text="une transcription correcte de bonne longueur ici ok"),
                 FakeTranslator(), FakeSTT("whistle", text="", window=30))
    assert p.process(clip).engine == "whisper"


def test_forced_engine_does_not_fall_back(tmp_path):
    clip = make_audio(tmp_path / "long.ogg", [12])
    cfg = Config(stt={"prefer": "whistle"})
    p = Pipeline(cfg, FakeSTT(), FakeTranslator(), FakeSTT("whistle", text="", window=30))
    assert p.process(clip, engine="whistle").engine == "whistle"


def test_long_audio_is_chunked_for_windowed_engine(tmp_path):
    clip = make_audio(tmp_path / "long.ogg", [20, 20, 20, 20])
    cfg = Config(stt={"prefer": "whistle"})
    whistle = FakeSTT("whistle", text="un deux trois quatre cinq six sept huit neuf dix onze douze", window=30)
    r = Pipeline(cfg, FakeSTT(), FakeTranslator(), whistle).process(clip)
    assert len(whistle.calls) >= 3 and r.engine == "whistle"
