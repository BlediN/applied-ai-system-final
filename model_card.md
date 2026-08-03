# StudyBot Model Card

## System Overview
StudyBot is a local-first AI assistant that answers questions using retrieval over project notes, optional live APIs, and a short conversation memory. It supports study questions, coding help, definitions, weather, news, and follow-up questions in the same chat session.

## Limitations and Biases
- The retrieval system only knows what is stored in `assets/knowledge`, so it can miss facts that are not in the notes.
- Wikipedia, dictionary, weather, and news responses depend on live services, so they can change over time or fail when the network is unavailable.
- The topic router uses keyword and pattern matching, which means it can misclassify ambiguous questions.
- The assistant is English-centric and may be less accurate for non-English questions or region-specific slang.
- The coding help is intentionally lightweight and gives starter guidance, not full code review or formal debugging.

## Misuse Potential and Safeguards
This system could be misused if someone treats it as an authoritative source without checking the evidence or source freshness. It could also be used to generate overly confident answers about topics it only partially understands.

To reduce misuse, I added these safeguards:
- The assistant shows source names or a safe fallback when evidence is weak.
- Confidence scoring helps signal when an answer is more grounded versus more tentative.
- The app logs requests and errors so failures can be traced.
- The assistant refuses to invent answers when the knowledge base does not support a question.

## Reliability and Evaluation
I tested the system with automated unit tests and direct CLI runs.

| Check | Result |
| --- | --- |
| `python -m unittest discover -s tests` | 12 / 12 tests passed |
| Grounded retrieval on local notes | Passed |
| Weather API routing | Passed |
| Definition and news routing | Passed |
| Follow-up chat memory | Passed |
| Coding-error explanations | Passed |
| Missing-evidence fallback | Passed |

What surprised me while testing was how much the response quality improved once the assistant stopped using one generic path for every question. The biggest reliability issue was not the retrieval code itself, but the routing layer: if a question was classified poorly, the answer quality dropped quickly even when the underlying tools were working.

## Collaboration With AI
I used AI as a coding partner for idea generation, debugging, and iteration.

### Helpful AI Suggestion
One helpful suggestion was to add a retrieval-first design for local notes instead of relying only on a generic response. That made the project more grounded and easier to explain in the README.

### Flawed or Incorrect AI Suggestion
One flawed suggestion was to treat weather as the central purpose of the app. That would have narrowed the project too much and ignored the assignment goal of building a broader useful AI system. Another incorrect assumption was that a single question/answer flow was enough; in practice, follow-up memory and topic routing were needed.

### How I Used AI Responsibly
I used AI to speed up implementation ideas, but I checked the output with tests, manual runs, and code review before trusting it. I also revised AI suggestions when they made the app too narrow, too generic, or less aligned with the assignment requirements.

## Reflection on the Project
This project showed me that making an AI system useful is about balancing capability, clarity, and safety. A small assistant can feel much smarter when it routes questions correctly, keeps short-term context, and admits uncertainty instead of guessing.

## Known Failure Modes
- Very short or vague follow-up questions can still be routed incorrectly.
- Live APIs can fail or return changing results.
- Questions outside the note collection may receive a partial answer or a safe fallback.
- The assistant is not a substitute for expert advice in medicine, law, finance, or other high-stakes areas.
