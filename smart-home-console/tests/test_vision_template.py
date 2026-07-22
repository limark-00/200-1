from __future__ import annotations

import os
import re
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

    def test_dashboard_contains_zone_editor_and_event_history(self):
        for element_id in (
            "visionZoneCanvas",
            "visionZoneEditButton",
            "visionZoneSaveButton",
            "visionZoneCancelButton",
            "visionZoneDeleteButton",
            "visionZoneState",
            "visionPeopleInZone",
            "visionActiveAlert",
            "visionAckButton",
            "visionEventList",
            "boardVisionAlarmValue",
        ):
            self.assertIn(f'id="{element_id}"', self.html)

    def test_dashboard_uses_zone_and_event_interfaces(self):
        self.assertIn('fetch("/api/vision/zone"', self.html)
        self.assertIn('fetch("/api/vision/events"', self.html)
        self.assertIn("function imageContentRect()", self.html)
        self.assertIn("function normalizedZoneFromDrag", self.html)
        self.assertIn('fetch("/api/vision/alarm/silence"', self.html)
        self.assertIn("visionAlarm:", self.html)
        self.assertIn('data.visionAlarm', self.html)
        self.assertIn('/vision-events/', self.html)

    def test_event_refresh_is_single_flight_with_one_queued_rerun(self):
        self.assertIn("let visionEventRefreshPromise = null;", self.html)
        self.assertIn("let visionEventRefreshQueued = false;", self.html)
        self.assertIn("if (visionEventRefreshPromise)", self.html)
        self.assertIn("visionEventRefreshQueued = true;", self.html)
        self.assertRegex(
            self.html,
            re.compile(
                r"const rerunRequested =\s+"
                r"visionEventRefreshQueued \|\|",
            ),
        )
        self.assertIn("if (rerunRequested)", self.html)
        self.assertIn("return refreshVisionEvents();", self.html)

    def test_status_and_zone_refreshes_are_single_flight(self):
        for refresh_type in ("Status", "Zone"):
            self.assertIn(
                f"let vision{refresh_type}RefreshPromise = null;",
                self.html,
            )
            self.assertIn(
                f"let vision{refresh_type}RefreshQueued = false;",
                self.html,
            )
            self.assertIn(
                f"if (vision{refresh_type}RefreshPromise)",
                self.html,
            )
            self.assertIn(
                f"vision{refresh_type}RefreshQueued = true;",
                self.html,
            )
            self.assertIn(
                f"return refreshVision{refresh_type}();",
                self.html,
            )

    def test_refreshes_discard_pre_mutation_responses(self):
        self.assertIn("let visionMutationRevision = 0;", self.html)
        self.assertGreaterEqual(
            self.html.count(
                "const requestRevision = visionMutationRevision;"
            ),
            3,
        )
        self.assertGreaterEqual(
            self.html.count(
                "requestRevision !== visionMutationRevision"
            ),
            3,
        )
        self.assertGreaterEqual(
            self.html.count("visionMutationRevision += 1;"),
            3,
        )

    def test_zone_drag_waits_for_natural_image_dimensions(self):
        self.assertIn("function visionImageReady()", self.html)
        self.assertIn("image.naturalWidth > 0", self.html)
        self.assertIn("image.naturalHeight > 0", self.html)
        self.assertIn("if (!visionImageReady())", self.html)
        self.assertIn("实时画面尚未加载，请稍后再试。", self.html)

    def test_live_label_does_not_intercept_canvas_pointer_events(self):
        self.assertRegex(
            self.html,
            re.compile(
                r"\.vision-frame-label\s*\{[^}]*pointer-events:\s*none;",
                re.DOTALL,
            ),
        )


if __name__ == "__main__":
    unittest.main()
