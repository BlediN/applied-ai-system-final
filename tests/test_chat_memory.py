import unittest
from unittest.mock import patch

from studybot.answering import Assistant


class ChatMemoryTests(unittest.TestCase):
    def test_follow_up_weather_question_reuses_previous_location(self) -> None:
        with patch("studybot.answering.fetch_weather_summary") as weather_mock:
            weather_mock.return_value = "Weather update for brooklyn: clear sky with 24°C."
            assistant = Assistant("assets/knowledge")

            first = assistant.answer("How is the weather in Brooklyn today?")
            second = assistant.answer("What about tomorrow?")

            self.assertIn("brooklyn", first.response.lower())
            self.assertIn("brooklyn", second.response.lower())
            self.assertGreaterEqual(weather_mock.call_count, 2)
            self.assertIn("brooklyn", weather_mock.call_args_list[1].args[0].lower())


if __name__ == "__main__":
    unittest.main()
