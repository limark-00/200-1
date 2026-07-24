from pathlib import Path
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
ROOT_README = REPOSITORY_ROOT / "README.md"
CONSOLE_README = REPOSITORY_ROOT / "smart-home-console" / "README.md"
FIRMWARE_README = (
    REPOSITORY_ROOT
    / "applications"
    / "sample"
    / "wifi-iot"
    / "app"
    / "day08_mqtt_new"
    / "README.md"
)
IMPLEMENTATION_PLAN = (
    REPOSITORY_ROOT
    / "docs"
    / "superpowers"
    / "plans"
    / "2026-07-22-yolo-zone-alarm-phase2.md"
)


class Phase2DocumentationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = ROOT_README.read_text(encoding="utf-8")
        cls.console = CONSOLE_README.read_text(encoding="utf-8")
        cls.firmware = FIRMWARE_README.read_text(encoding="utf-8")
        cls.plan = IMPLEMENTATION_PLAN.read_text(encoding="utf-8")

    def test_systemd_uses_project_virtual_environment(self):
        self.assertIn(
            'Environment="PATH=/path/to/smart-home-console/.venv/bin:',
            self.console,
        )
        self.assertIn(
            "ExecStart=/path/to/smart-home-console/.venv/bin/uvicorn",
            self.console,
        )
        self.assertNotIn("ExecStart=/path/to/.venv/bin/uvicorn", self.console)

    def test_deployment_requires_access_control_for_sensitive_routes(self):
        for required_text in (
            "本应用不包含内置身份认证",
            "禁止直接暴露到公网",
            "局域网",
            "VPN",
            "防火墙",
            "反向代理身份认证",
            "/api/vision/events",
            "/vision-events/",
        ):
            with self.subTest(required_text=required_text):
                self.assertIn(required_text, self.console)

    def test_backup_and_ignore_guidance_covers_overridden_paths(self):
        for required_text in (
            "仅适用于默认路径",
            '${VISION_DB_PATH:-data/vision_events.db}',
            '${VISION_EVENT_DIR:-static/vision_events}',
            "只覆盖默认路径",
            "git status --short --ignored",
        ):
            with self.subTest(required_text=required_text):
                self.assertIn(required_text, self.console)

    def test_restart_acceptance_distinguishes_graceful_and_unclean_exit(self):
        for document in (self.console, self.plan):
            with self.subTest(document="console" if document is self.console else "plan"):
                self.assertIn("优雅重启", document)
                self.assertIn("server_shutdown", document)
                self.assertIn("受控非正常终止", document)
                self.assertIn("server_restart", document)

    def test_snapshot_build_requires_complete_openharmony_tree(self):
        for required_text in (
            "完整且兼容的 OpenHarmony 工程树",
            "build.py -> build/lite/build.py",
            "目标在本仓库快照中不存在",
            "python build.py wifiiot",
        ):
            with self.subTest(required_text=required_text):
                self.assertIn(required_text, self.firmware)

    def test_api_evidence_telemetry_and_storage_health_are_documented(self):
        for required_text in (
            "/api/vision/alarm/silence",
            "/vision-events/",
            "storage_error",
            "BEMFA_ENV_PUB_TOPIC",
            "ENV_TOPIC",
            "ENV_PUB_TOPIC",
        ):
            with self.subTest(required_text=required_text):
                self.assertIn(required_text, self.console)

    def test_root_readme_uses_untracked_secret_configuration_only(self):
        for required_text in (
            "仅通过环境变量或仓库外配置文件注入",
            "不得写入或提交到 `config.py`、README、脚本或其他受版本控制文件",
            "泄露后立即轮换",
        ):
            with self.subTest(required_text=required_text):
                self.assertIn(required_text, self.root)

        for stale_text in (
            "编辑 config.py，设置 BEMFA_UID 环境变量或修改默认值",
            "BEMFA_UID 默认值",
        ):
            with self.subTest(stale_text=stale_text):
                self.assertNotIn(stale_text, self.root)

    def test_root_readme_requires_a_private_or_authenticated_access_boundary(self):
        for required_text in (
            "本应用不包含内置身份认证",
            "禁止直接暴露到公网",
            "局域网",
            "VPN",
            "防火墙",
            "反向代理身份认证",
        ):
            with self.subTest(required_text=required_text):
                self.assertIn(required_text, self.root)

        for stale_public_example in (
            "server_name your-domain.com",
            "listen 443 ssl",
            "uvicorn app:app --host 0.0.0.0 --port 5001",
        ):
            with self.subTest(stale_public_example=stale_public_example):
                self.assertNotIn(stale_public_example, self.root)

    def test_root_readme_points_phase2_operations_to_the_canonical_guide(self):
        self.assertIn("第二阶段（YOLO 区域警报）", self.root)
        self.assertIn(
            "[smart-home-console/README.md](./smart-home-console/README.md)",
            self.root,
        )
        self.assertIn("唯一权威说明", self.root)

    def test_canonical_readme_keeps_credentials_out_of_tracked_config(self):
        self.assertIn("凭据", self.console)
        self.assertIn("环境变量", self.console)
        self.assertIn("不要写入或提交源码", self.console)
        self.assertNotIn(
            "编辑 `config.py` 或通过环境变量覆盖（建议）",
            self.console,
        )


if __name__ == "__main__":
    unittest.main()
