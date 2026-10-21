from vmt import audio

from .conftest import make_audio


def test_plan_chunks_short_is_single():
    assert audio.plan_chunks(20, [], 28) == [(0.0, 20)]


def test_plan_chunks_cuts_at_silence_and_respects_max():
    chunks = audio.plan_chunks(70, [10, 25, 27, 50, 55], 28)
    assert all(b - a <= 28 for a, b in chunks)
    assert chunks[0][1] >= 27 and chunks[-1][1] == 70


def test_plan_chunks_hard_split_without_silence():
    chunks = audio.plan_chunks(100, [], 28)
    assert all(b - a <= 28 + 1e-9 for a, b in chunks)
    assert chunks[-1][1] == 100


def test_join_transcripts_removes_overlap():
    assert audio.join_transcripts(["je vous appelle pour", "appelle pour le rendez-vous"]) == \
        "je vous appelle pour le rendez-vous"


def test_join_keeps_non_overlapping():
    assert audio.join_transcripts(["a b c", "d e f"]) == "a b c d e f"


def test_convert_duration_and_silence(tmp_path):
    src = make_audio(tmp_path / "v.ogg", [3, 3])
    wav = audio.to_wav(src, tmp_path / "v.wav")
    assert 6 < audio.duration(wav) < 8
    sil = audio.find_silences(wav)
    assert any(2.9 < s < 3.9 for s in sil)


def test_limits(tmp_path):
    import pytest
    src = make_audio(tmp_path / "v.ogg", [3])
    with pytest.raises(audio.AudioError):
        audio.check_limits(src, max_minutes=0.01, max_mb=25)
    with pytest.raises(audio.AudioError):
        audio.check_limits(src, max_minutes=10, max_mb=0.000001)


def test_bad_file(tmp_path):
    import pytest
    bad = tmp_path / "x.ogg"
    bad.write_bytes(b"not audio")
    with pytest.raises(audio.AudioError):
        audio.to_wav(bad, tmp_path / "x.wav")
