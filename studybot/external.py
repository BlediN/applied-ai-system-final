from __future__ import annotations

from html import unescape
import json
import re
import xml.etree.ElementTree as ElementTree
from urllib.parse import quote
from urllib.request import urlopen


def fetch_weather_summary(question: str) -> str:
    location = _extract_location(question)
    if not location:
        raise ValueError("No location found in weather question")

    geo_url = (
        "https://geocoding-api.open-meteo.com/v1/search?"
        f"name={quote(location)}&count=1&language=en&format=json"
    )
    geo_data = _load_json(geo_url)
    results = geo_data.get("results") or []
    if not results:
        raise ValueError(f"Could not resolve location: {location}")

    place = results[0]
    lat = place["latitude"]
    lon = place["longitude"]

    forecast_url = (
        "https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}&current=temperature_2m,weather_code&timezone=auto"
    )
    forecast_data = _load_json(forecast_url)
    current = forecast_data.get("current") or {}
    weather_code = current.get("weather_code", 0)
    temperature = current.get("temperature_2m")

    weather_text = _weather_code_to_text(weather_code)
    temp_text = "unknown temperature" if temperature is None else f"{temperature}°C"
    return f"Weather update for {location}: {weather_text} with {temp_text}."


def fetch_wikipedia_summary(question: str) -> str:
    topic = _clean_topic(question)
    if not topic:
        raise ValueError("No topic found for wikipedia lookup")

    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(topic)}"
    payload = _load_json(url)
    if not payload:
        raise ValueError("Wikipedia lookup returned no data")

    title = payload.get("title") or topic.title()
    extract = payload.get("extract") or "No summary available."
    return f"{title}: {extract}"


def fetch_definition_summary(question: str) -> str:
    term = _extract_definition_term(question)
    if not term:
        raise ValueError("No term found for definition lookup")

    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{quote(term)}"
    payload = _load_json(url)
    if not isinstance(payload, list) or not payload:
        raise ValueError(f"No dictionary entry found for: {term}")

    entry = payload[0] or {}
    word = entry.get("word") or term
    meanings = entry.get("meanings") or []
    first_meaning = meanings[0] if meanings else {}
    definitions = first_meaning.get("definitions") or []
    first_definition = definitions[0] if definitions else {}
    definition_text = first_definition.get("definition") or "No definition available."
    part_of_speech = first_meaning.get("partOfSpeech")
    example = first_definition.get("example")

    parts = [f"{word}: {definition_text}"]
    if part_of_speech:
        parts.append(f"Part of speech: {part_of_speech}.")
    if example:
        parts.append(f"Example: {example}.")
    return " ".join(parts)


def fetch_news_summary(question: str) -> str:
    topic = _extract_news_topic(question)
    if not topic:
        raise ValueError("No news topic found")

    url = f"https://news.google.com/rss/search?q={quote(topic)}&hl=en-US&gl=US&ceid=US:en"
    root = _load_xml(url)
    items = root.findall(".//item")[:3]
    if not items:
        raise ValueError(f"No news results found for: {topic}")

    headlines: list[str] = []
    for item in items:
        title = unescape((item.findtext("title") or "").strip())
        description = unescape((item.findtext("description") or "").strip())
        if title and description:
            headlines.append(f"{title} — {description}")
        elif title:
            headlines.append(title)

    if not headlines:
        raise ValueError(f"No readable news results found for: {topic}")

    return f"Latest news for {topic}: {'; '.join(headlines)}"


def _extract_location(question: str) -> str | None:
    lower = question.lower()
    for marker in ["in ", "for ", "at ", "around "]:
        if marker in lower:
            start = lower.find(marker) + len(marker)
            remainder = question[start:].strip()
            if remainder:
                remainder = remainder.split("?")[0].strip()
                words = remainder.split()
                stop_words = {"today", "now", "right", "now", "tomorrow", "tonight", "currently", "please"}
                filtered = [word for word in words if word.lower() not in stop_words]
                if filtered:
                    return " ".join(filtered)
    return None


def _extract_definition_term(question: str) -> str | None:
    text = question.strip().rstrip("?!.")
    patterns = [
        r"^(?:what is|what's|define|explain|meaning of)\s+(.+)$",
        r"^(?:what does)\s+(.+?)\s+mean$",
        r"^(?:what is the meaning of)\s+(.+)$",
    ]
    for pattern in patterns:
        match = re.match(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return text if text else None


def _extract_news_topic(question: str) -> str | None:
    text = question.strip().rstrip("?!.")
    patterns = [
        r"^(?:news about|news on|latest on|updates on|what's new with|what is happening with|what's happening with|tell me the news about)\s+(.+)$",
        r"^(?:latest news on|latest news about|news for)\s+(.+)$",
    ]
    for pattern in patterns:
        match = re.match(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()

    lower = text.lower()
    if "news" in lower:
        cleaned = re.sub(r"\bnews\b", "", text, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"^(?:on|about|for|regarding)\s+", "", cleaned, flags=re.IGNORECASE).strip()
        return cleaned or "world"
    return None


def _clean_topic(question: str) -> str:
    normalized = re.sub(r"^(what|who|where|when|why|how|is|are|do|does|tell me about|explain)\b", "", question, flags=re.IGNORECASE).strip()
    normalized = re.sub(r"[?!.]$", "", normalized)
    return normalized.replace(" about", "").strip()


def _weather_code_to_text(code: int) -> str:
    mapping = {
        0: "clear sky",
        1: "mainly clear",
        2: "partly cloudy",
        3: "overcast",
        45: "foggy",
        48: "depositing rime fog",
        51: "light drizzle",
        53: "moderate drizzle",
        55: "dense drizzle",
        61: "slight rain",
        63: "moderate rain",
        65: "heavy rain",
        71: "slight snow",
        73: "moderate snow",
        75: "heavy snow",
        95: "thunderstorm",
        96: "thunderstorm with hail",
        99: "heavy thunderstorm with hail",
    }
    return mapping.get(code, "varied conditions")


def _load_json(url: str) -> dict:
    try:
        with urlopen(url, timeout=8) as response:
            return json.load(response)
    except Exception as exc:
        raise RuntimeError(str(exc)) from exc


def _load_xml(url: str) -> ElementTree.Element:
    try:
        with urlopen(url, timeout=8) as response:
            return ElementTree.fromstring(response.read())
    except Exception as exc:
        raise RuntimeError(str(exc)) from exc
