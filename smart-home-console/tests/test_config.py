import importlib
import os
import unittest
from unittest.mock import patch

import config


class ConfigTests(unittest.TestCase):
    def test_empty_vision_event_directory_uses_safe_default(self):
        self.addCleanup(importlib.reload, config)

        with patch.dict(os.environ, {"VISION_EVENT_DIR": ""}):
            importlib.reload(config)

            self.assertEqual(
                config.VISION_EVENT_DIR,
                "static/vision_events",
            )


if __name__ == "__main__":
    unittest.main()
