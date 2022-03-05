import pytest

from actions import actions
from tests.conftest import EMPTY_TRACKER


@pytest.mark.asyncio
async def test_validate_model_name_iphone(dispatcher, domain):
    tracker = EMPTY_TRACKER
    action = actions.ValidatePlaybackIssueForm()
    result = await action.validate_model_name("iPhone", dispatcher, tracker, domain)
    expected_result = {
        "model_name": "iPhone",
        "os_name": "ios",
        "platform": "Phone",
        "vendor": "Apple"
    }

    assert result == expected_result
