import json
from pathlib import Path

import pytest
from rasa_sdk import Tracker
from rasa_sdk.executor import CollectingDispatcher

here = Path(__file__).parent.resolve()

EMPTY_TRACKER = Tracker.from_dict(json.load(open(here / "./data/empty_tracker.json")))


@pytest.fixture
def dispatcher():
    return CollectingDispatcher()


@pytest.fixture
def domain():
    return dict()
