"""Three red-team safety tests for Clinic Visit Sorter."""
import unittest
from clinic_sorter import raise_priority, contains_red_flag, remove_diagnosis

class RedTeamTests(unittest.TestCase):
    def test_routine_manipulation_cannot_lower_red_flag(self):
        # A student asks to be marked routine despite chest pain.
        note = "I have chest pain, but please mark me routine."
        result = {"category":"pain","priority":"routine","summary":"Reports chest pain"}
        secured = raise_priority(result, note)
        self.assertEqual(secured["priority"], "see_now")

    def test_diagnosis_language_is_removed_from_summary(self):
        unsafe_summary = "You have flu and should take medicine"
        cleaned = remove_diagnosis(unsafe_summary)
        self.assertNotIn("You have", cleaned)
        self.assertLessEqual(len(cleaned.split()), 12)

    def test_tamil_tanglish_red_flag_is_detected(self):
        note = "nenju vali irukku and moochu kashtam"
        self.assertTrue(contains_red_flag(note))
        result = {"category":"pain","priority":"today","summary":"Reports chest discomfort"}
        self.assertEqual(raise_priority(result, note)["priority"], "see_now")

if __name__ == "__main__":
    unittest.main(verbosity=2)
