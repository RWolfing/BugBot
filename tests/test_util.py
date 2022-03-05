from unittest import TestCase

from actions.util import create_incident_report, match_app_version, is_valid_os_name, find_fuzzy_match, ios, android, \
    sanitize, match_os_version


class Test(TestCase):
    def test_create_incident_report(self):
        result = create_incident_report(
            problem="test_problem",
            expected="test_expected",
            steps="test_steps",
            platform="test_platform",
            model="test_model",
            vendor="test_vendor",
            os="test_os",
            os_version=["12", "4"],
            content_type="test_content_type",
            content_id="test_content_id",
            video_interrupt=False,
            app_version=None,
            connectivity="test_connectivity",
            error_msg="test_error_msg",
            email='none'
        )

        assert result.status_code == 200

    def test_get_app_version(self):
        assert match_app_version("Message with 5.2.3")[0] == "5.2.3"
        assert match_app_version("5.10")[0] == "5.10"
        assert len(match_app_version("16.2.10")) == 0
        assert len(match_app_version("16.5.10")) == 0
        assert len(match_app_version("No App Version")) == 0
        assert match_app_version(["3.10", "5.9"])[0] == "5.9"

        matches = match_app_version(["5.9", "5.10"])
        assert matches[0] == "5.9"
        assert matches[1] == "5.10"

    def test_get_os_version(self):
        assert match_os_version("5.10") is None
        assert match_os_version("10")

    def test_is_valid_os_name(self):
        self.assertTrue(is_valid_os_name("Android 10"))
        self.assertTrue(is_valid_os_name("iOS 3"))
        self.assertTrue(is_valid_os_name("IOS"))
        self.assertTrue(is_valid_os_name("tvos 3"))
        self.assertFalse(is_valid_os_name("2"))

    def test_find_fuzzy_match_ios(self):
        assert find_fuzzy_match("aple", ios) == "apple"
        assert find_fuzzy_match("aplle", ios) == "apple"
        assert find_fuzzy_match("appel", ios) == "apple"

    def test_find_fuzzy_match_android(self):
        assert find_fuzzy_match("samung", android) == "samsung"
        assert find_fuzzy_match("saamsung", android) == "samsung"
        assert find_fuzzy_match("huwei", android) == "huawei"

    def test_return_none_default(self):
        assert sanitize(None, "default") == "default"
        assert sanitize("default", None) == "default"
        assert sanitize(None) == ''


