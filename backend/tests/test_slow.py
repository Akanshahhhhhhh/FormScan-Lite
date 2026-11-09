"""Slow tests: real models and internet. Run with:  python -m pytest --run-slow"""
import pytest

pytestmark = pytest.mark.slow

DIRECTIONS = [
    ("en", "ta"),
    ("en", "bn"),
    ("ta", "en"),
    ("bn", "en"),
    ("bn", "ta"),
    ("ta", "bn"),
]

SAMPLES = {
    "en": "The fee is Rs. 250. Call 1800-11-2345 for help.",
}


@pytest.fixture(scope="module")
def sample_text(client):
    """Make Bengali and Tamil sample sentences by translating the English one."""
    texts = dict(SAMPLES)
    for lang in ("ta", "bn"):
        r = client.post(
            "/api/translate",
            json={"text": SAMPLES["en"], "source_lang": "en", "target_lang": lang},
        )
        assert r.status_code == 200, r.get_data(as_text=True)
        texts[lang] = r.get_json()["translated_text"]
    return texts


@pytest.mark.parametrize("source,target", DIRECTIONS)
def test_translate_direction(client, sample_text, source, target):
    r = client.post(
        "/api/translate",
        json={"text": sample_text[source], "source_lang": source, "target_lang": target},
    )
    assert r.status_code == 200, r.get_data(as_text=True)
    data = r.get_json()
    assert data["translated_text"].strip()
    assert data["source_lang"] == source
    assert data["target_lang"] == target
    assert data["model"].startswith("ai4bharat/indictrans2")


def test_translate_keeps_phone_number(client):
    r = client.post(
        "/api/translate",
        json={"text": SAMPLES["en"], "source_lang": "en", "target_lang": "ta"},
    )
    assert "1800-11-2345" in r.get_json()["translated_text"]


@pytest.mark.parametrize("language", ["en", "bn", "ta"])
def test_tts_makes_audio(client, sample_text, language):
    r = client.post("/api/tts", json={"text": sample_text[language], "language": language})
    assert r.status_code == 200, r.get_data(as_text=True)
    data = r.get_json()
    assert data["audio_url"].startswith("/api/audio/")
    audio = client.get(data["audio_url"])
    assert audio.status_code == 200
    assert audio.mimetype == "audio/mpeg"
    assert len(audio.data) > 1000
