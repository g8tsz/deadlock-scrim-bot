import unittest

from Tasks import automation_message_key, splitMessage


class ConfigHelperTests(unittest.TestCase):
    def test_automation_message_key_checkin(self):
        self.assertEqual(automation_message_key("checkin"), "scrimCheckin")

    def test_automation_message_key_pickban(self):
        self.assertEqual(automation_message_key("pickban"), "scrimPickBan")

    def test_split_message_scrim_name(self):
        title, body = splitMessage("**{scrim_name} Registration**{}\nSign up now.", 1, "Friday Scrim")
        self.assertIn("Friday Scrim", title)
        self.assertIn("Sign up now.", body)


if __name__ == "__main__":
    unittest.main()
