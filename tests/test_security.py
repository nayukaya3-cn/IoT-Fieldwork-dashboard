"""保護：秘密の入力欄がない・外へ通信しない・設定・.gitignore"""
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = [*ROOT.glob("*.py"), *(ROOT / "views").glob("*.py")]


def test_no_password_inputs_or_network():
    for p in SOURCES:
        s = p.read_text(encoding="utf-8")
        assert 'type="password"' not in s, p.name                          # 鍵・パスワードの入力欄を置かない
        for mod in ("requests", "urllib.request", "http.client", "socket", "smtplib"):
            assert not re.search(rf"^\s*(import|from)\s+{re.escape(mod)}\b", s, re.M), (p.name, mod)


def test_html_is_escaped():
    ui = (ROOT / "ui.py").read_text(encoding="utf-8")
    assert ui.count("html.escape") >= 5


def test_server_config():
    cfg = tomllib.loads((ROOT / ".streamlit/config.toml").read_text(encoding="utf-8"))
    assert cfg["server"]["enableXsrfProtection"] and not cfg["server"]["enableStaticServing"]
    assert cfg["server"]["maxUploadSize"] == 1 and cfg["client"]["showErrorDetails"] == "none"


def test_gitignore_blocks_secrets_and_photos():
    gi = (ROOT / ".gitignore").read_text(encoding="utf-8").split()
    for pat in (".env", "secrets.toml", "service_account*.json", "token*.json", "*.pem", "*.jpg", "data/"):
        assert pat in gi, pat


def test_actions_are_pinned():
    for wf in (ROOT / ".github/workflows").glob("*.yml"):
        for line in wf.read_text(encoding="utf-8").splitlines():
            if "uses:" in line:
                assert re.search(r"@[0-9a-f]{40}", line), (wf.name, line)
