# AI Features

This project demonstrates a practical Retrieval-Augmented Generation style workflow.
The retrieval step is integrated into the main application logic, so the answer depends on the retrieved evidence rather than generic language output.

## Key AI Features

- Retrieval-Augmented Generation: the assistant searches local notes before answering.
- Guardrails: if the knowledge base does not contain enough support, the assistant avoids making up facts.
- Logging: requests and errors are written to `studybot.log`.
- Testing: the project includes automated tests for retrieval and grounded answer generation.

## How the System Behaves

When a user asks a question, the app first checks whether the question looks like a coding question. Coding questions receive a starter example in Python, while general topic questions use the retrieval pipeline to find relevant notes and summarize them. A strong answer names the source notes and explains the key facts from them instead of repeating the user's wording.

## Example Questions

- What is the project trying to do?
- How does the assistant decide what information to use?
- How does the app handle questions that are not covered by the notes?
