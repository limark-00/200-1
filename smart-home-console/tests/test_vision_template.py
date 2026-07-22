from __future__ import annotations

import os
import unittest


PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_PATH = os.path.join(PROJECT_DIR, "templates", "index.html")


class VisionTemplateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(TEMPLATE_PATH, encoding="utf-8") as template_file:
            cls.html = template_file.read()

    def test_dashboard_contains_vision_monitor_elements(self):
        for element_id in (
            "visionPanel",
            "visionStream",
            "visionStateDot",
            "visionStateText",
            "visionPeopleCount",
            "visionFps",
            "visionModelName",
            "visionCameraIndex",
            "visionError",
            "visionReconnectButton",
        ):
            self.assertIn(f'id="{element_id}"', self.html)

    def test_dashboard_uses_vision_stream_and_status_endpoints(self):
        self.assertIn('src="/api/vision/stream"', self.html)
        self.assertIn('fetch("/api/vision/status"', self.html)
        self.assertIn("function refreshVisionStatus()", self.html)
        self.assertIn("function reconnectVisionStream()", self.html)


if __name__ == "__main__":
    unittest.main()
