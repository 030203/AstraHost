import unittest

from tools.time_tool import TimeTool


class TimeToolTest(unittest.TestCase):
    def test_returns_current_time_for_timezone(self):
        tool = TimeTool()

        result = tool.execute({"timezone": "Asia/Shanghai"})

        self.assertEqual(result["timezone"], "Asia/Shanghai")
        self.assertTrue(result["date"])
        self.assertTrue(result["time"])
        self.assertTrue(result["iso_datetime"])

    def test_invalid_offset_raises(self):
        tool = TimeTool()

        with self.assertRaises(ValueError):
            tool.execute({"utc_offset": "bad"})


if __name__ == "__main__":
    unittest.main()
