# StudyBot

StudyBot is a small local RAG-style assistant for course/project notes. It reads markdown or text files from `assets/knowledge`, retrieves the most relevant passages for a user question, and then answers with grounded evidence and source names.

## What it does

- Retrieves relevant passages from local knowledge files before answering.
- Uses optional external APIs for weather and general factual questions when available.
- Remembers the previous question in an interactive chat session so short follow-ups stay on topic.
- Handles definitions, news, weather, and coding errors more intelligently.
- Builds a concise answer from the retrieved evidence instead of responding generically.
- Logs each request, the retrieved sources, and errors to `studybot.log`.
- Includes tests that verify retrieval, grounding, and API-backed behavior.

## Requirements

- Python 3.11 or newer

## Setup

1. Clone or open this repository.
2. Put your reference notes in `assets/knowledge` as `.md` or `.txt` files.
3. Run the app from the repository root.

No third-party packages are required.

## Run

Answer a question directly:

```bash
python -m studybot "What does the assistant do?"
```

Start interactive mode:

```bash
python -m studybot --interactive
```

Interactive mode keeps the same assistant instance alive, so you can ask a follow-up like "What about tomorrow?" after a weather question.

Use a different knowledge folder:

```bash
python -m studybot --knowledge-root assets/knowledge
```

## Test

```bash
python -m unittest discover -s tests
```

## How it works

1. The CLI loads documents from `assets/knowledge`.
2. The retriever scores each passage against the question.
3. The answer builder summarizes the best evidence and cites the source files.
4. If the system cannot find enough support, it falls back to a safe "not enough evidence" response.

## Diagram

See `diagrams/architecture.mmd` for the Mermaid source diagram.
