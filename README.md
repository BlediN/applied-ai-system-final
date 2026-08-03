# StudyBot

## Title and Summary
StudyBot is a small AI assistant that answers questions using a local knowledge base, optional live APIs, and a simple chat memory. It matters because it shows how an AI system can combine retrieval, tool use, and guardrails to give more useful answers than a single static prompt.

It now includes a dark-themed Streamlit interface for a more polished chat experience.

**Original project from Modules 1-3:** StudyBot started as a retrieval assistant for class notes. Its original goal was to load markdown or text files, find the most relevant passages for a user question, and respond with grounded evidence instead of guessing.

## What the Project Does
StudyBot now supports several topic types:

- Local project and study questions from files in `assets/knowledge`
- Weather questions through a live weather API
- Definitions through a dictionary API
- General factual questions through Wikipedia-style lookup
- Coding questions with starter examples
- Coding errors with more helpful traceback-style guidance
- Follow-up questions in the same chat session

## Architecture Overview
The system is organized as a small routing pipeline:

1. The user asks a question in the CLI.
2. The assistant decides whether the question looks like coding, weather, definition, news, factual, or knowledge-base content.
3. The app sends the question to the right source: local retrieval, a live API, or a coding-error helper.
4. The answer builder formats the response, adds evidence when available, and keeps a short memory of the conversation.
5. Logging records what happened, and tests check the behavior.

See `diagrams/architecture.mmd` for the Mermaid diagram source.

## Setup Instructions
1. Open a terminal in the project root.
2. Make sure you are using Python 3.11 or newer.
3. Install the Streamlit dependency for the UI:

```bash
pip install -r requirements.txt
```

4. Run the tests once to confirm everything works:

```bash
python -m unittest discover -s tests
```

5. Start the assistant in interactive mode:

```bash
python -m studybot --interactive
```

6. Launch the dark-themed Streamlit UI:

```bash
streamlit run streamlit_app.py
```

7. Type a question, then keep asking follow-ups in the same chat session.
8. To ask one question at a time, run:

```bash
python -m studybot "How does StudyBot answer questions?"
```

No third-party packages are required.

To use the dark-themed UI, install the Streamlit dependency and run:

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Sample Interactions
These examples show the current behavior of the system. Live API answers can vary slightly over time.

The same questions can also be asked from the Streamlit interface, which keeps the conversation in a dark chat layout.

### 1) Weather question
**Input**
```text
How is the weather in Brooklyn today?
```
**Output**
```text
Here’s the latest weather update: Weather update for Brooklyn: overcast with 24.3°C.
```

### 2) Local knowledge question
**Input**
```text
How does StudyBot answer questions?
```
**Output**
```text
Based on your notes, ... StudyBot is a retrieval-backed assistant that answers questions from a local knowledge base. Sources: ai_features.md, project_brief.md.
```

### 3) Coding error question
**Input**
```text
What does a TypeError mean in Python?
```
**Output**
```text
That looks like a coding error. I detected TypeError. This usually means the function or operator got the wrong type or number of arguments. If you paste the full traceback and the code around the failing line, I can narrow it down further.
```

## Design Decisions
I built the app as a local-first assistant so it stays reproducible and easy to run on a laptop. The knowledge-base path uses simple retrieval because it is transparent, easy to test, and works well for project notes; the tradeoff is that it is not as flexible as a large embedded model.

I also added optional live APIs for weather, definitions, and factual lookups so the assistant is not limited to local notes. The tradeoff is that live answers depend on network access and can change over time. Finally, I kept the implementation in the Python standard library so setup stays simple, even though that means the retrieval and language understanding are less advanced than a full production AI stack.

## Testing Summary
The project proves reliability in three ways:

1. Automated tests check the main behaviors.
2. Confidence scores show when the assistant is answering from stronger evidence versus falling back.
3. Logging records requests and errors so failures can be traced.

### Evaluation Results

| Test / Check | What It Measures | Result |
| --- | --- | --- |
| `python -m unittest discover -s tests` | Core functionality across retrieval, APIs, chat memory, and error handling | **12 / 12 tests passed** |
| Grounded answer test | Whether local knowledge is used when relevant | Pass |
| API routing tests | Whether weather, definition, and news questions route to the right source | Pass |
| Follow-up chat test | Whether a short follow-up keeps the previous topic in the same session | Pass |
| Error-handling test | Whether missing evidence returns a safe fallback instead of a broken answer | Pass |

### What Worked

- Retrieval from `assets/knowledge` returns grounded answers with source names.
- Weather, definition, news, and coding-error routes behave differently from the local knowledge path.
- Interactive chat keeps context across follow-up questions.
- The automated tests pass with `python -m unittest discover -s tests`.

### What Did Not Work at First

- The weather lookup originally parsed locations too loosely.
- Some early responses sounded repetitive or too generic.
- The assistant initially treated every question as a standalone request.

### What I Learned

- A useful AI app needs routing, not just a single model response.
- Guardrails matter when live APIs fail or when the assistant is unsure.
- Tests are important because they catch regressions in topic detection and response formatting.

## Reflection
This project taught me that AI problem-solving is mostly about system design: deciding what information to trust, how to route a question, and how to make the result understandable to a user. I also learned that a small, well-tested assistant can feel much smarter when it remembers context and chooses the right tool for the job.

For the graded responsible-AI reflection about collaboration, one helpful AI suggestion, one flawed AI suggestion, and the system’s limitations, see `model_card.md`.
