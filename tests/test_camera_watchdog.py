import unittest
from unittest.mock import MagicMock, patch

from scripts.camera_watchdog import (
    CAMERA_CATALOG,
    build_decoder_entry,
    evaluate_and_heal,
    expected_nvr_mac,
    hex_ip_to_str,
)


class TestCameraWatchdog(unittest.TestCase):
    def test_hex_ip_to_str(self):
        self.assertEqual(hex_ip_to_str("0x0401A8C0"), "192.168.1.4")
        self.assertEqual(hex_ip_to_str("0xC901A8C0"), "192.168.1.201")
        self.assertEqual(hex_ip_to_str("0xCE01A8C0"), "192.168.1.206")
        self.assertIsNone(hex_ip_to_str(None))
        self.assertIsNone(hex_ip_to_str("invalid"))

    def test_expected_nvr_mac_policy(self):
        by_code = {c["code"]: c for c in CAMERA_CATALOG}
        self.assertEqual(expected_nvr_mac(by_code["D01"]), "")
        self.assertEqual(expected_nvr_mac(by_code["D02"]), "00:13:00:f6:69:a0")
        self.assertEqual(expected_nvr_mac(by_code["D03"]), "00:13:00:01:61:7b")
        self.assertEqual(expected_nvr_mac(by_code["D04"]), "")
        self.assertEqual(expected_nvr_mac(by_code["D05"]), "48:8f:4c:3d:13:14")
        self.assertEqual(expected_nvr_mac(by_code["D06"]), "")

    def test_build_decoder_entry_clears_mac_for_d06(self):
        d06 = next(c for c in CAMERA_CATALOG if c["code"] == "D06")
        entry = build_decoder_entry(d06, "192.168.1.206")
        self.assertTrue(entry["Enable"])
        dec = entry["Decoder"][0]
        self.assertEqual(dec["IPAddress"], "192.168.1.206")
        self.assertEqual(dec["UserName"], "admin")
        self.assertEqual(dec["PassWord"], "23blurbang")
        self.assertEqual(dec["MacAddr"], "")

    @patch("scripts.camera_watchdog.DVRIPClient")
    @patch("scripts.camera_watchdog.probe_camera_endpoint")
    @patch("scripts.camera_watchdog.discover_xiongmai_udp")
    @patch("scripts.camera_watchdog.fetch_lansentry_mac_map")
    def test_evaluate_and_heal_fixes_dhcp_ip_and_mac_policy(
        self, mock_lan, mock_udp, mock_probe, mock_dvrip_cls
    ):
        # Simulate D02 having changed IP from .14 to .4 in LanSentry
        mock_lan.return_value = {
            "d4:a3:eb:89:bd:f4": {"ip": "192.168.1.201", "online": 1, "date": "2026-11-06"},
            "f8:16:0c:96:d5:f6": {"ip": "192.168.1.4", "online": 1, "date": "2026-11-06"},
            "00:13:00:01:61:7b": {"ip": "192.168.1.203", "online": 1, "date": "2026-11-06"},
            "38:be:ab:91:96:85": {"ip": "192.168.1.204", "online": 1, "date": "2026-11-06"},
            "48:8f:4c:3d:13:14": {"ip": "192.168.1.3", "online": 1, "date": "2026-11-06"},
            "a4:ef:15:30:79:32": {"ip": "192.168.1.206", "online": 1, "date": "2026-11-06"},
        }
        mock_udp.return_value = {
            "00:13:00:f6:69:a0": {"ip": "192.168.1.4", "host_ip": "192.168.1.4", "raw": {}},
        }

        def fake_probe(ip, port, proto, user, pwd, timeout=3.5, retries=2, **kwargs):
            valid_ips = {
                "192.168.1.201",
                "192.168.1.4",
                "192.168.1.203",
                "192.168.1.204",
                "192.168.1.3",
                "192.168.1.206",
            }
            if ip in valid_ips:
                return {"ok": True, "latency_ms": 12.3, "error": None, "locked_206": False}
            return {"ok": False, "latency_ms": None, "error": "timeout", "locked_206": False}

        mock_probe.side_effect = fake_probe

        fake_nvr = MagicMock()
        fake_nvr.session_hex = "0x00000001"
        chn_status = [
            {"Status": "Connected", "CurRes": "1080P"},
            {"Status": "Offline", "CurRes": "Unknown"},  # D02 offline on old IP .14
            {"Status": "Connected", "CurRes": "1080P"},
            {"Status": "Connected", "CurRes": "4M"},
            {"Status": "Connected", "CurRes": "720P"},
            {"Status": "Offline", "CurRes": "Unknown"},  # D06 has wrong MacAddr set
        ]
        rem_devs = [
            build_decoder_entry(CAMERA_CATALOG[0], "192.168.1.201"),
            build_decoder_entry(CAMERA_CATALOG[1], "192.168.1.14"),  # Old IP .14
            build_decoder_entry(CAMERA_CATALOG[2], "192.168.1.203"),
            build_decoder_entry(CAMERA_CATALOG[3], "192.168.1.204"),
            build_decoder_entry(CAMERA_CATALOG[4], "192.168.1.3"),
            build_decoder_entry(CAMERA_CATALOG[5], "192.168.1.206"),
        ]
        # Inject unwanted MacAddr on D06 to verify self-heal clears it
        rem_devs[5]["Decoder"][0]["MacAddr"] = "a4:ef:15:30:79:32"

        def fake_get_config(name):
            if name == "NetWork.ChnStatus":
                return {"NetWork.ChnStatus": chn_status, "Ret": 100}
            if name == "NetWork.RemoteDeviceV3":
                return {"NetWork.RemoteDeviceV3": rem_devs, "Ret": 100}
            return {"Ret": 100}

        fake_nvr.get_config.side_effect = fake_get_config
        fake_nvr.request.return_value = ((1041, 1), {"Ret": 100})
        mock_dvrip_cls.return_value = fake_nvr

        res = evaluate_and_heal(apply_heal=True, dry_run=False)
        self.assertTrue(res["healed"])
        self.assertEqual(rem_devs[1]["Decoder"][0]["IPAddress"], "192.168.1.4")
        self.assertEqual(rem_devs[1]["Decoder"][0]["MacAddr"], "00:13:00:f6:69:a0")
        self.assertEqual(rem_devs[5]["Decoder"][0]["MacAddr"], "")
        fake_nvr.request.assert_called_once()


if __name__ == "__main__":
    unittest.main()
