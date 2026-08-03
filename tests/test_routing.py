import tempfile
import unittest
from pathlib import Path

from studybot.answering import Assistant


class RoutingTests(unittest.TestCase):
    def test_coding_question_uses_coding_guidance(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            knowledge_root = Path(temp_dir)
            (knowledge_root / "notes.md").write_text(
                "StudyBot uses retrieval and answer composition to respond to project questions.",
                encoding="utf-8",
            )

            assistant = Assistant(knowledge_root)
            answer = assistant.answer("How do I write a Python function to read a file?")

            self.assertTrue(answer.response.lower().startswith("that looks like a coding question"))
            self.assertIn("python", answer.response.lower())

    def test_general_question_uses_knowledge_base(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            knowledge_root = Path(temp_dir)
            (knowledge_root / "notes.md").write_text(
                "StudyBot is a retrieval-backed assistant for course notes.",
                encoding="utf-8",
            )

            assistant = Assistant(knowledge_root)
            answer = assistant.answer("How does StudyBot answer questions?")

            self.assertIn("retrieval-backed", answer.response.lower())
            self.assertGreater(len(answer.sources), 0)


if __name__ == "__main__":
    unittest.main()
