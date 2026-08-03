import unittest
from unittest.mock import patch

from studybot.answering import Assistant
from studybot.external import fetch_definition_summary, fetch_news_summary, fetch_weather_summary


class ExternalKnowledgeTests(unittest.TestCase):
    def test_weather_question_uses_external_api_when_available(self) -> None:
        with patch("studybot.answering.fetch_weather_summary") as weather_mock:
            weather_mock.return_value = "It is 72°F and sunny in Brooklyn."
            assistant = Assistant("assets/knowledge")
            answer = assistant.answer("How is the weather in Brooklyn today?")

            self.assertIn("weather", answer.response.lower())
            self.assertIn("brooklyn", answer.response.lower())
            self.assertGreaterEqual(answer.confidence, 0.6)

    def test_general_question_uses_local_notes_for_project_help(self) -> None:
        assistant = Assistant("assets/knowledge")
        answer = assistant.answer("How does StudyBot answer questions?")

        self.assertIn("retrieval-backed", answer.response.lower())
        self.assertGreater(len(answer.sources), 0)

    def test_definition_question_uses_dictionary_api(self) -> None:
        with patch("studybot.answering.fetch_definition_summary") as definition_mock:
            definition_mock.return_value = "Polymorphism: the ability of different objects to respond in different ways."
            assistant = Assistant("assets/knowledge")
            answer = assistant.answer("What is polymorphism?")

            self.assertIn("concise definition", answer.response.lower())
            self.assertIn("polymorphism", answer.response.lower())

    def test_news_question_uses_news_api(self) -> None:
        with patch("studybot.answering.fetch_news_summary") as news_mock:
            news_mock.return_value = "AI: headline one; headline two"
            assistant = Assistant("assets/knowledge")
            answer = assistant.answer("Latest news on AI")

            self.assertIn("recent headlines", answer.response.lower())
            self.assertIn("ai", answer.response.lower())

    def test_weather_lookup_strips_time_words_from_location(self) -> None:
        with patch("studybot.external._load_json") as load_json_mock:
            load_json_mock.side_effect = [
                {"results": [{"latitude": 40.7, "longitude": -74.0, "name": "Brooklyn"}]},
                {"current": {"temperature_2m": 24, "weather_code": 0}},
            ]

            summary = fetch_weather_summary("How is the weather in Brooklyn today?")

            self.assertIn("Brooklyn", summary)
            self.assertIn("clear sky", summary.lower())


if __name__ == "__main__":
    unittest.main()
