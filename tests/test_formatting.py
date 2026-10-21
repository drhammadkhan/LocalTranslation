from vmt.formatting import Result, format_reply, split_message


def test_reply_full():
    r = Result("fr", "French", "whistle", 47, "Bonjour", "Hello", "Call back")
    out = format_reply(r)
    assert out.startswith("🎙 Voicemail · French · 0:47 · whistle")
    assert "🇬🇧 English\nHello" in out and "📌 Summary\nCall back" in out


def test_reply_english_has_no_translation_section():
    out = format_reply(Result("en", "English", "whisper", 5, "Hi"))
    assert "🇬🇧" not in out


def test_split_message_limit():
    parts = split_message("word " * 3000, 4096)
    assert all(len(p) <= 4096 for p in parts) and len(parts) > 1
    assert " ".join(parts).split() == ("word " * 3000).split()
