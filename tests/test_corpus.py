from pathlib import Path
import tempfile
import unittest

from studybot.corpus import load_documents, chunk_documents


class CorpusTests(unittest.TestCase):
    def test_load_documents_requires_knowledge_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(FileNotFoundError):
                load_documents(Path(temp_dir))

    def test_chunk_documents_returns_chunks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            knowledge_root = Path(temp_dir)
            (knowledge_root / "a.md").write_text("First paragraph.\n\nSecond paragraph.", encoding="utf-8")
            documents = load_documents(knowledge_root)
            chunks = chunk_documents(documents)
            self.assertGreaterEqual(len(chunks), 1)
            self.assertEqual(chunks[0].title, "A")


if __name__ == "__main__":
    unittest.main()
