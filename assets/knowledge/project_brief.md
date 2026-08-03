# StudyBot Project Brief

StudyBot is a retrieval-backed assistant that answers questions from a local knowledge base.
It is designed to support course work, project writeups, coding help, and quick reference checks.

The assistant follows a grounded flow:

1. Load `.md` and `.txt` notes from `assets/knowledge`.
2. Rank the most relevant passages for the user's question.
3. Build the response from those passages and include source filenames.
4. Fall back safely when the notes do not provide enough evidence.

The project is intentionally reproducible: it uses only the Python standard library, logs to `studybot.log`, and includes tests for retrieval behavior.

## Project Goals

- Help users answer questions using local notes rather than guessing.
- Support coding questions with practical starter examples.
- Keep the system explainable by showing the evidence sources used.
- Make it easy to extend with more knowledge files.

## Technical Notes

The app is implemented as a small Python package with separate modules for corpus loading, retrieval, answering, and the command-line interface. The retrieval step uses a lightweight term-based ranking strategy that is simple to understand and easy to run on a laptop or desktop machine.
