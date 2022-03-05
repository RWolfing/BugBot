from unittest import TestCase

from actions.elastic import search_model, search_manufacturer


class Test(TestCase):

    def test_search_model_ipad(self):
        model_name = "iPad"
        result = search_model(model_name)

        assert result
        assert result['hit']['Model Name'] == model_name
        assert result.get("suggestions", None) is None

    def test_search_model_samsung(self):
        model_name = "Galaxy S8"
        result = search_model(model_name)

        assert result
        assert result['hit']['Model Name'] == model_name
        assert result.get("suggestions", None) is None

    def test_search_model_fire_tv(self):
        model_name = "Fire TV"
        result = search_model(model_name)

        assert result
        assert result['hit']['Model Name'] == model_name
        assert result.get("suggestions", None) is None

    def test_search_model_apple_tv(self):
        model_name = "Apple TV 4k"
        result = search_model(model_name)

        assert result
        assert result['hit']['Model Name'] == model_name

    def test_search_apple(self):
        manufacturer = "Apple"
        result = search_manufacturer(manufacturer)

        assert result
        assert result['hit']['Manufacturer'] == "Apple"
