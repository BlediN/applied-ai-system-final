from pathlib import Path
import tempfile
import unittest

from studybot.answering import Assistant


class AssistantTests(unittest.TestCase):
    def test_answer_uses_grounded_sources(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            knowledge_root = Path(temp_dir)
            (knowledge_root / "notes.md").write_text(
                "StudyBot retrieves relevant passages before answering. It logs requests and falls back safely.",
                encoding="utf-8",
            )

            assistant = Assistant(knowledge_root)
            answer = assistant.answer("How does StudyBot answer questions?")

            self.assertGreater(answer.confidence, 0.0)
            self.assertIn("retrieval-backed assistant", answer.response.lower())
            self.assertTrue(answer.sources)

    def test_answer_refuses_without_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            knowledge_root = Path(temp_dir)
            (knowledge_root / "notes.md").write_text(
                "This file discusses bicycle maintenance and gardening.",
                encoding="utf-8",
            )

            assistant = Assistant(knowledge_root)
            answer = assistant.answer("What retrieval behavior is implemented?")

            self.assertEqual(answer.confidence, 0.0)
            self.assertEqual(answer.sources, [])
            self.assertIn("could not find enough evidence", answer.response.lower())


if __name__ == "__main__":
    unittest.main()
