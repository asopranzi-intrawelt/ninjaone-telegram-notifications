import json
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from relay.config import Config, ConfigError, load_dotenv
from relay.ninjaone_client import NinjaOneClient
from relay.telegram_client import TelegramClient
from relay.state import SeenAlertsStore, make_key
from relay.main import run_once

TOKEN_RESPONSE = {"access_token": "fake-token", "expires_in": 3600, "token_type": "bearer"}

ALERT_1 = {
    "uid": "alert-uid-1",
    "deviceId": 42,
    "message": "Disk free space < 10%",
    "createTime": 1752000000,
    "severity": "MODERATE",
    "priority": "HIGH",
    "conditionName": "Low disk space",
    "sourceType": "CONDITION_AGENT_DISK_FREE_SPACE",
    "device": {"displayName": "WKS-<b>TEST</b>", "organizationId": 1},
}
ALERT_2 = {
    "uid": "alert-uid-2",
    "deviceId": 7,
    "message": None,
    "createTime": 1752000100,
    "severity": None,
    "priority": None,
    "conditionName": None,
    "sourceType": "CONDITION_PING",
    "device": {"organizationId": 1},
}


class RelayEndToEndTest(unittest.TestCase):
    def setUp(self):
        self.sent_messages = []
        self.alerts = [dict(ALERT_1), dict(ALERT_2)]
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        self.state_path = os.path.join(self.tmpdir.name, "seen.json")

        self.post_patcher = patch("relay.ninjaone_client.requests.post", side_effect=self._fake_post)
        self.get_patcher = patch("relay.ninjaone_client.requests.get", side_effect=self._fake_get)
        self.telegram_post_patcher = patch("relay.telegram_client.requests.post", side_effect=self._fake_post)
        self.post_patcher.start()
        self.get_patcher.start()
        self.telegram_post_patcher.start()
        self.addCleanup(self.post_patcher.stop)
        self.addCleanup(self.get_patcher.stop)
        self.addCleanup(self.telegram_post_patcher.stop)

        self.ninjaone = NinjaOneClient("https://eu.ninjarmm.com", "cid", "csecret", "monitoring")
        self.telegram = TelegramClient("BOTTOKEN", "-100123", None)
        self.state = SeenAlertsStore(self.state_path)

    def _fake_post(self, url, data=None, json=None, headers=None, timeout=None):
        resp = MagicMock()
        if "oauth/token" in url:
            resp.status_code = 200
            resp.json.return_value = TOKEN_RESPONSE
            return resp
        if "sendMessage" in url:
            self.sent_messages.append(json)
            resp.status_code = 200
            return resp
        raise AssertionError(f"unexpected POST {url}")

    def _fake_get(self, url, headers=None, timeout=None):
        self.assertEqual(headers["Authorization"], "Bearer fake-token")
        resp = MagicMock()
        resp.status_code = 200
        resp.raise_for_status = MagicMock()
        resp.json.return_value = self.alerts
        return resp

    def _run(self, min_severities=None, organization_ids=None):
        run_once(
            self.ninjaone, self.telegram, self.state, [111, 222],
            min_severities or [], organization_ids or [],
        )

    def test_new_alerts_are_notified_and_html_escaped(self):
        self._run()
        self.assertEqual(len(self.sent_messages), 2)
        self.assertIn("Disk free space", self.sent_messages[0]["text"])
        self.assertIn("WKS-&lt;b&gt;TEST&lt;/b&gt;", self.sent_messages[0]["text"])
        self.assertIn("tg://user?id=111", self.sent_messages[0]["text"])
        self.assertIn("tg://user?id=222", self.sent_messages[0]["text"])

    def test_missing_fields_fall_back_gracefully(self):
        self._run()
        self.assertIn("device #7", self.sent_messages[1]["text"])
        self.assertIn("(nessun messaggio)", self.sent_messages[1]["text"])

    def test_second_poll_does_not_resend_seen_alerts(self):
        self._run()
        self.sent_messages.clear()
        self._run()
        self.assertEqual(len(self.sent_messages), 0)

    def test_resolved_alert_is_pruned_and_new_one_notified(self):
        self._run()
        self.alerts = [
            dict(ALERT_2),
            {**ALERT_1, "uid": "alert-uid-3", "message": "Nuovo alert diverso"},
        ]
        self.sent_messages.clear()
        self._run()
        self.assertEqual(len(self.sent_messages), 1)
        self.assertIn("Nuovo alert diverso", self.sent_messages[0]["text"])

        with open(self.state_path) as f:
            seen_after = set(json.load(f))
        self.assertEqual(
            seen_after,
            {make_key("alert-uid-2", None), make_key("alert-uid-3", "MODERATE")},
        )

    def test_severity_filter_blocks_low_severity(self):
        self.alerts = [dict(ALERT_1)]  # severity MODERATE
        self._run(min_severities=["CRITICAL"])
        self.assertEqual(len(self.sent_messages), 0)

    def test_severity_filter_allows_matching_severity(self):
        self.alerts = [{**ALERT_1, "severity": "CRITICAL"}]
        self._run(min_severities=["CRITICAL", "MAJOR"])
        self.assertEqual(len(self.sent_messages), 1)

    def test_organization_filter_blocks_other_organizations(self):
        self.alerts = [{**ALERT_1, "device": {**ALERT_1["device"], "organizationId": 99}}]
        self._run(organization_ids=[1])
        self.assertEqual(len(self.sent_messages), 0)

    def test_organization_filter_allows_matching_organization(self):
        self._run(organization_ids=[1])
        self.assertEqual(len(self.sent_messages), 2)

    def test_organization_filter_excludes_alert_from_pruned_state(self):
        self.alerts = [
            dict(ALERT_1),
            {**ALERT_2, "device": {**ALERT_2["device"], "organizationId": 99}},
        ]
        self._run(organization_ids=[1])
        self.assertEqual(len(self.sent_messages), 1)
        with open(self.state_path) as f:
            seen = set(json.load(f))
        self.assertEqual(seen, {make_key("alert-uid-1", "MODERATE")})

    def test_escalation_of_same_alert_is_notified_once_it_qualifies(self):
        # Primo giro: severity MODERATE, sotto soglia -> nessuna notifica, nessun mark_seen.
        self.alerts = [dict(ALERT_1)]
        self._run(min_severities=["CRITICAL"])
        self.assertEqual(len(self.sent_messages), 0)

        # L'alert peggiora a CRITICAL restando lo stesso uid -> deve essere notificato.
        self.alerts = [{**ALERT_1, "severity": "CRITICAL"}]
        self._run(min_severities=["CRITICAL"])
        self.assertEqual(len(self.sent_messages), 1)

        # Rivisto invariato al giro successivo -> nessun duplicato.
        self.sent_messages.clear()
        self._run(min_severities=["CRITICAL"])
        self.assertEqual(len(self.sent_messages), 0)


BASE_ENV = {
    "NINJAONE_CLIENT_ID": "cid",
    "NINJAONE_CLIENT_SECRET": "csecret",
    "TELEGRAM_BOT_TOKEN": "BOTTOKEN",
    "TELEGRAM_CHAT_ID": "-100123",
}


class ConfigFromEnvTest(unittest.TestCase):
    def _config_with(self, instance):
        env = {**BASE_ENV, "NINJAONE_INSTANCE": instance}
        with patch.dict(os.environ, env, clear=True):
            return Config.from_env()

    def test_region_code_maps_to_official_host(self):
        config = self._config_with("eu")
        self.assertEqual(config.ninjaone_base_url, "https://eu.ninjarmm.com")

    def test_branded_https_url_is_used_verbatim_without_trailing_slash(self):
        config = self._config_with("https://msp-di-esempio.rmmservice.eu/")
        self.assertEqual(config.ninjaone_base_url, "https://msp-di-esempio.rmmservice.eu")

    def test_unknown_instance_is_rejected(self):
        with self.assertRaises(ConfigError):
            self._config_with("emea")


class LoadDotenvTest(unittest.TestCase):
    def test_parses_file_and_does_not_override_real_environment(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = os.path.join(tmpdir, ".env")
            with open(env_path, "w", encoding="utf-8") as f:
                f.write(
                    "# commento\n"
                    "\n"
                    "PLAIN=valore\n"
                    'QUOTED="con spazi"\n'
                    "PREESISTENTE=dal-file\n"
                    "DUPLICATA=\n"
                    "DUPLICATA=ultima-valorizzata\n"
                    "VUOTA=\n"
                )
            with patch.dict(os.environ, {"PREESISTENTE": "dall-ambiente"}, clear=True):
                load_dotenv(env_path)
                self.assertEqual(os.environ["PLAIN"], "valore")
                self.assertEqual(os.environ["QUOTED"], "con spazi")
                self.assertEqual(os.environ["PREESISTENTE"], "dall-ambiente")
                self.assertEqual(os.environ["DUPLICATA"], "ultima-valorizzata")
                self.assertNotIn("VUOTA", os.environ)

    def test_missing_file_is_a_no_op(self):
        load_dotenv("/percorso/inesistente/.env")


if __name__ == "__main__":
    unittest.main()
