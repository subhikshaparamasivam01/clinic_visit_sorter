"""Five basic evaluation tests for Clinic Visit Sorter."""
import unittest
from clinic_sorter import is_valid, raise_priority, remove_diagnosis, contains_red_flag

class ClinicSorterEvaluation(unittest.TestCase):
    def test_valid_json_shape(self):
        result = {"category":"pain","priority":"today","summary":"Reports a headache"}
        self.assertTrue(is_valid(result))

    def test_reject_extra_key(self):
        result = {"category":"pain","priority":"today","summary":"Headache","diagnosis":"flu"}
        self.assertFalse(is_valid(result))

    def test_reject_invalid_priority(self):
        result = {"category":"pain","priority":"urgent","summary":"Reports pain"}
        self.assertFalse(is_valid(result))

    def test_summary_limit(self):
        result = {"category":"other","priority":"today",
                  "summary":"one two three four five six seven eight nine ten eleven twelve thirteen"}
        self.assertFalse(is_valid(result))

    def test_red_flag_raises_priority(self):
        result = {"category":"pain","priority":"routine","summary":"Reports chest pain"}
        self.assertEqual(raise_priority(result, "chest pain")["priority"], "see_now")

if __name__ == "__main__":
    unittest.main(verbosity=2)
