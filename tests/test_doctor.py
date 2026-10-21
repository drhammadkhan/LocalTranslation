import httpx

from vmt.config import Config, Secrets
from vmt.doctor import FAIL, OK, render, run_checks


def client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def by_name(checks, prefix):
    return next(c for c in checks if c.name.startswith(prefix))


def test_telegram_ok_and_token_never_in_output():
    s = Secrets(telegram_bot_token="SECRET123", telegram_allowed_user_ids="5")
    h = lambda req: httpx.Response(200, json={"ok": True, "result": {"username": "mybot"}})
    checks = run_checks(Config(), s, client(h))
    assert by_name(checks, "telegram token").status == OK
    assert "SECRET123" not in render(checks)


def test_telegram_failure_is_reported_without_token():
    s = Secrets(telegram_bot_token="SECRET123", telegram_allowed_user_ids="5")
    def h(req):
        raise httpx.ConnectError("boom for https://api.telegram.org/botSECRET123")
    out = render(run_checks(Config(), s, client(h)))
    assert "telegram reachable" in out and "SECRET123" not in out


def test_missing_model_and_allowlist_fail(tmp_path):
    cfg = Config(stt={"models_dir": str(tmp_path)}, translate={"nllb_model_dir": str(tmp_path / "x")})
    checks = run_checks(cfg, Secrets(telegram_bot_token="", telegram_allowed_user_ids=""),
                        client(lambda r: httpx.Response(200, json={})))
    assert by_name(checks, "whisper model").status == FAIL
    assert by_name(checks, "NLLB").status == FAIL
    assert by_name(checks, "telegram token").status == FAIL
    assert by_name(checks, "telegram allowlist").status == FAIL


def test_model_found(tmp_path):
    d = tmp_path / "models--Systran--faster-whisper-medium" / "snapshots" / "abc"
    d.mkdir(parents=True)
    (d / "model.bin").write_bytes(b"x")
    nl = tmp_path / "nllb"
    nl.mkdir()
    (nl / "model.bin").write_bytes(b"x")
    cfg = Config(stt={"models_dir": str(tmp_path)}, translate={"nllb_model_dir": str(nl)})
    checks = run_checks(cfg, Secrets(telegram_bot_token="t", telegram_allowed_user_ids="1"),
                        client(lambda r: httpx.Response(200, json={"ok": True, "result": {"username": "b"}})))
    assert by_name(checks, "whisper model").status == OK and by_name(checks, "NLLB").status == OK
