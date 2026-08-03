from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
import re

from .corpus import chunk_documents, load_documents, sentence_split, tokenize
from .external import (
    fetch_definition_summary,
    fetch_news_summary,
    fetch_weather_summary,
    fetch_wikipedia_summary,
)
from .retrieval import RetrievalResult, Retriever


@dataclass(frozen=True)
class Answer:
    question: str
    response: str
    sources: list[str]
    evidence: list[str]
    confidence: float


@dataclass(frozen=True)
class Turn:
    question: str
    topic: str
    focus: str | None
    response: str


@dataclass
class ConversationMemory:
    turns: list[Turn] = field(default_factory=list)
    last_question: str | None = None
    last_topic: str | None = None
    last_focus: str | None = None


class Assistant:
    def __init__(self, knowledge_root: Path | str, memory_limit: int = 6) -> None:
        root = Path(knowledge_root)
        documents = load_documents(root)
        chunks = chunk_documents(documents)
        self._retriever = Retriever(chunks)
        self._memory = ConversationMemory()
        self._memory_limit = max(1, memory_limit)

    def answer(self, question: str, top_k: int = 3) -> Answer:
        normalized_question = question.strip()
        if not normalized_question:
            raise ValueError("Question cannot be empty.")

        routed_question, follow_up = self._contextualize_question(normalized_question)
        topic = self._detect_topic(routed_question)
        if follow_up and self._memory.last_topic and topic in {"knowledge", "factual"}:
            topic = self._memory.last_topic

        response, sources, evidence, confidence, focus = self._generate_response(topic, normalized_question, routed_question, top_k)
        self._remember(normalized_question, topic, focus, response)

        if follow_up:
            response = self._make_follow_up_response(response)

        return Answer(
            question=normalized_question,
            response=response,
            sources=sources,
            evidence=evidence,
            confidence=confidence,
        )

    def _generate_response(
        self,
        topic: str,
        original_question: str,
        routed_question: str,
        top_k: int,
    ) -> tuple[str, list[str], list[str], float, str | None]:
        if topic == "coding_error":
            focus = self._extract_error_focus(original_question)
            return self._build_coding_error_response(original_question), [], [], 0.82, focus

        if topic == "coding":
            focus = self._extract_coding_focus(original_question)
            return self._build_coding_response(original_question), [], [], 0.75, focus

        if topic == "weather":
            try:
                summary = fetch_weather_summary(routed_question)
                focus = self._extract_location_hint(routed_question)
                return (
                    f"Here’s the latest weather update: {summary}",
                    ["weather-api"],
                    [summary],
                    0.92,
                    focus,
                )
            except Exception:
                return (
                    "I could not reach the weather source just now. Try again in a moment or ask me about a specific location.",
                    [],
                    [],
                    0.0,
                    self._extract_location_hint(routed_question),
                )

        if topic == "news":
            try:
                summary = fetch_news_summary(routed_question)
                focus = self._extract_news_focus(routed_question)
                return (
                    f"Here are a few recent headlines: {summary}",
                    ["news-rss"],
                    [summary],
                    0.88,
                    focus,
                )
            except Exception:
                return (
                    "I could not reach a live news source just now. Try asking for a narrower topic like 'news about AI'.",
                    [],
                    [],
                    0.0,
                    self._extract_news_focus(routed_question),
                )

        if topic == "definition":
            focus = self._extract_definition_focus(routed_question)
            try:
                summary = fetch_definition_summary(routed_question)
                return (
                    f"Here’s a concise definition: {summary}",
                    ["dictionary-api"],
                    [summary],
                    0.86,
                    focus,
                )
            except Exception:
                try:
                    summary = fetch_wikipedia_summary(routed_question)
                    return (
                        f"Here’s a broader explanation: {summary}",
                        ["wikipedia"],
                        [summary],
                        0.72,
                        focus,
                    )
                except Exception:
                    return (
                        "I could not find a definition source right now. Try rephrasing the term or asking for a broader explanation.",
                        [],
                        [],
                        0.0,
                        focus,
                    )

        if topic == "factual":
            focus = self._extract_general_focus(routed_question)
            try:
                summary = fetch_wikipedia_summary(routed_question)
                return (
                    f"Here’s what I found: {summary}",
                    ["wikipedia"],
                    [summary],
                    0.8,
                    focus,
                )
            except Exception:
                pass

        results = self._retriever.search(routed_question, top_k=top_k)
        if not results or results[0].score < 0.08:
            return (
                "I could not find enough evidence in the knowledge base to answer that confidently. Try rephrasing the question or add a more relevant note to assets/knowledge.",
                [],
                [],
                0.0,
                self._extract_general_focus(routed_question),
            )

        evidence_sentences = self._extract_evidence(routed_question, results)
        sources = self._format_sources(results)
        confidence = round(min(1.0, sum(result.score for result in results[:top_k]) / max(1, top_k)), 3)
        response = self._compose_response(routed_question, evidence_sentences, sources)
        return response, sources, evidence_sentences, confidence, self._extract_general_focus(routed_question)

    def _detect_topic(self, question: str) -> str:
        lower = question.lower()
        if self._looks_like_coding_error_question(lower):
            return "coding_error"
        if self._looks_like_coding_question(lower):
            return "coding"
        if self._looks_like_weather_question(lower):
            return "weather"
        if self._looks_like_news_question(lower):
            return "news"
        if self._looks_like_definition_question(lower):
            return "definition"
        if self._looks_like_factual_question(lower):
            return "factual"
        return "knowledge"

    def _contextualize_question(self, question: str) -> tuple[str, bool]:
        if not self._memory.last_topic or not self._is_follow_up_question(question):
            return question, False

        focus = self._memory.last_focus or self._extract_general_focus(self._memory.last_question or "")
        last_question = self._memory.last_question or question
        last_topic = self._memory.last_topic

        if last_topic == "weather" and focus:
            return f"{question} in {focus}", True
        if last_topic == "news" and focus:
            return f"news about {focus}", True
        if last_topic == "definition" and focus:
            return f"what does {focus} mean", True
        if last_topic == "coding_error":
            return f"{question}\nPrevious issue: {last_question}", True
        if focus:
            return f"{focus}. {question}", True
        return f"{last_question} {question}", True

    def _remember(self, question: str, topic: str, focus: str | None, response: str) -> None:
        self._memory.last_question = question
        self._memory.last_topic = topic
        self._memory.last_focus = focus
        self._memory.turns.append(Turn(question=question, topic=topic, focus=focus, response=response))
        if len(self._memory.turns) > self._memory_limit:
            self._memory.turns = self._memory.turns[-self._memory_limit :]

    def _make_follow_up_response(self, response: str) -> str:
        if response.lower().startswith("here’s") or response.lower().startswith("here is"):
            return response
        return f"Picking up from your earlier question, {response[0].lower() + response[1:] if response else response}"

    def _looks_like_coding_question(self, question: str) -> bool:
        coding_keywords = [
            "python",
            "function",
            "class",
            "code",
            "debug",
            "bug",
            "syntax",
            "import",
            "module",
            "loop",
            "variable",
            "file",
            "json",
            "api",
            "git",
            "package",
            "exception",
            "return",
            "def ",
            "for ",
            "while ",
            "try",
            "except",
            "stack trace",
            "traceback",
        ]
        return any(keyword in question for keyword in coding_keywords)

    def _looks_like_coding_error_question(self, question: str) -> bool:
        error_keywords = [
            "error",
            "traceback",
            "exception",
            "stack trace",
            "typeerror",
            "valueerror",
            "nameerror",
            "indexerror",
            "keyerror",
            "syntaxerror",
            "attributeerror",
            "modulenotfounderror",
            "importerror",
            "why does my code fail",
            "won't run",
            "does not work",
        ]
        return any(keyword in question for keyword in error_keywords)

    def _looks_like_weather_question(self, question: str) -> bool:
        return any(keyword in question for keyword in ["weather", "temperature", "forecast", "rain", "snow", "sunny", "cloudy"])

    def _looks_like_news_question(self, question: str) -> bool:
        return any(keyword in question for keyword in ["news", "headline", "headlines", "latest", "update"])

    def _looks_like_definition_question(self, question: str) -> bool:
        return bool(
            re.match(r"^(what is|what's|define|explain|meaning of|what does .+ mean)", question, flags=re.IGNORECASE)
        )

    def _looks_like_factual_question(self, question: str) -> bool:
        if self._looks_like_coding_question(question):
            return False
        return any(keyword in question for keyword in ["who is", "what is", "where is", "when did", "why does", "tell me about", "explain"])

    def _is_follow_up_question(self, question: str) -> bool:
        lower = question.lower().strip()
        short = len(lower.split()) <= 4
        follow_up_phrases = (
            "what about",
            "how about",
            "and tomorrow",
            "and today",
            "any updates",
            "what next",
            "tell me more",
            "more detail",
            "more about that",
            "what about that",
            "what about it",
            "how about it",
            "what else",
            "and then",
        )
        if short:
            return True
        return lower.startswith(follow_up_phrases) or any(phrase in lower for phrase in ["that one", "this one", "there too", "same thing", "it too"])

    def _build_coding_response(self, question: str) -> str:
        lower = question.lower()
        if "read" in lower and "file" in lower:
            snippet = 'with open("data.txt", "r", encoding="utf-8") as handle:\n    content = handle.read()'
        elif "json" in lower:
            snippet = 'import json\nwith open("data.json", "r", encoding="utf-8") as handle:\n    data = json.load(handle)'
        else:
            snippet = 'def greet(name):\n    return f"Hello, {name}!"'

        return (
            "That looks like a coding question. A practical starter example in Python is:\n"
            f"```python\n{snippet}\n```\n"
            "If you share the exact language, error message, or goal, I can make this more specific."
        )

    def _build_coding_error_response(self, question: str) -> str:
        exception_name = self._extract_exception_name(question)
        if exception_name == "TypeError":
            explanation = "This usually means the function or operator got the wrong type or number of arguments."
        elif exception_name == "NameError":
            explanation = "This usually means a variable or function name is not defined in the current scope."
        elif exception_name == "IndexError":
            explanation = "This usually means a list, string, or array index is out of range."
        elif exception_name == "KeyError":
            explanation = "This usually means a dictionary key is missing."
        elif exception_name == "SyntaxError":
            explanation = "This usually means there is a punctuation, indentation, or formatting problem in the code."
        elif exception_name == "AttributeError":
            explanation = "This usually means the object does not have the attribute or method you tried to use."
        elif exception_name == "ModuleNotFoundError":
            explanation = "This usually means Python cannot find the package or module in the current environment."
        elif exception_name == "ValueError":
            explanation = "This usually means the input value has the right type but the wrong content or shape."
        else:
            explanation = "The traceback likely points to a mismatch in the code, input, or environment."

        parts = ["That looks like a coding error."]
        if exception_name:
            parts.append(f"I detected {exception_name}.")
        parts.append(explanation)
        parts.append("If you paste the full traceback and the code around the failing line, I can narrow it down further.")
        return " ".join(parts)

    def _extract_exception_name(self, question: str) -> str | None:
        patterns = [
            r"\b(TypeError|NameError|IndexError|KeyError|SyntaxError|AttributeError|ModuleNotFoundError|ImportError|ValueError|RuntimeError)\b",
            r"\b([A-Z][A-Za-z]+Error)\b",
        ]
        for pattern in patterns:
            match = re.search(pattern, question)
            if match:
                return match.group(1)
        return None

    def _extract_coding_focus(self, question: str) -> str | None:
        lowered = question.lower()
        if "python" in lowered:
            return "python"
        if "json" in lowered:
            return "json"
        if "file" in lowered:
            return "file handling"
        return None

    def _extract_error_focus(self, question: str) -> str | None:
        exception_name = self._extract_exception_name(question)
        if exception_name:
            return exception_name
        return self._extract_coding_focus(question)

    def _extract_location_hint(self, question: str) -> str | None:
        lower = question.lower()
        for marker in [" in ", "for ", "at ", "around "]:
            if marker in lower:
                start = lower.find(marker) + len(marker)
                remainder = question[start:].strip().split("?")[0].strip()
                words = remainder.split()
                stop_words = {"today", "now", "right", "tomorrow", "tonight", "currently", "please", "weather", "forecast"}
                filtered = [word for word in words if word.lower() not in stop_words]
                if filtered:
                    return " ".join(filtered)
        return None

    def _extract_definition_focus(self, question: str) -> str | None:
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
        return None

    def _extract_news_focus(self, question: str) -> str | None:
        text = question.strip().rstrip("?!.")
        patterns = [
            r"^(?:news about|news on|latest on|updates on|what's new with|what is happening with|tell me the news about)\s+(.+)$",
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
            return cleaned or None
        return None

    def _extract_general_focus(self, question: str) -> str | None:
        focus = self._extract_definition_focus(question)
        if focus:
            return focus
        focus = self._extract_news_focus(question)
        if focus:
            return focus
        focus = self._extract_location_hint(question)
        if focus:
            return focus
        focus = self._extract_coding_focus(question)
        if focus:
            return focus
        cleaned = re.sub(r"^(what|who|where|when|why|how|is|are|do|does|tell me about|explain)\b", "", question, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"[?!.]$", "", cleaned).strip()
        return cleaned or None

    def _extract_evidence(self, question: str, results: list[RetrievalResult]) -> list[str]:
        question_terms = Counter(tokenize(question))
        scored_sentences: list[tuple[float, str]] = []
        seen: set[str] = set()

        for result in results:
            for sentence in sentence_split(result.chunk.text):
                normalized = sentence.strip()
                if not normalized or normalized in seen:
                    continue
                seen.add(normalized)
                sentence_terms = Counter(tokenize(normalized))
                overlap = sum(min(question_terms[term], sentence_terms[term]) for term in question_terms if term in sentence_terms)
                if overlap == 0:
                    continue
                score = overlap + result.score
                scored_sentences.append((score, normalized))

        scored_sentences.sort(key=lambda item: item[0], reverse=True)
        return [sentence for _, sentence in scored_sentences[:3]]

    def _format_sources(self, results: list[RetrievalResult]) -> list[str]:
        sources: list[str] = []
        seen: set[str] = set()
        for result in results:
            source = result.chunk.document_path.name
            if source in seen:
                continue
            seen.add(source)
            sources.append(source)
        return sources

    def _compose_response(self, question: str, evidence: list[str], sources: list[str]) -> str:
        if not evidence:
            return (
                f"Based on the available notes, I can only confirm the source files related to '{question}', "
                f"but I do not have enough direct evidence to summarize the answer. Sources: {', '.join(sources)}."
            )

        summary = " ".join(evidence)
        source_text = ", ".join(sources)
        return f"Based on your notes, {summary} Sources: {source_text}."
