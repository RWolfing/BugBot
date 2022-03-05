import json
import logging
import os
import re
from typing import Any, List, Text

import requests
from thefuzz import fuzz

DEVICE_TV = "tv"
DEVICE_HANDHELD = "handheld"
DEVICE_WEB = "web"

VENDOR_APPLE = "apple"

OS_ANDROID = "android"
OS_IOS = "ios"
OS_WEB = "browser"

android = ["galaxy", "samsung", "bravia", "mate", "huawei", "pixel", "google"]
ios = ["ipad", "iphone", "apple"]

logger = logging.getLogger(__name__)

airtable_base_id = os.environ.get('AIRTABLE_BASE_ID')
airtable_api_key = os.environ.get('AIRTABLE_API_KEY')
airtable_table_name = os.environ.get('AIRTABLE_TABLE')


def create_incident_report(problem: Any, expected: Any, steps: Any, platform: Any, model: Any, vendor: Any,
                           os: Any, os_version: Any, content_type: Any, content_id: Any, video_interrupt: Any,
                           app_version: Any, connectivity: Any, error_msg: Any, email: Any):
    request = f"https://api.airtable.com/v0/" + airtable_base_id + "/" + airtable_table_name
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer " + airtable_api_key,
    }
    data = {
        "records": [
            {
                "fields": {
                    "Problem Statement": sanitize(problem),
                    "Expected Behavior": sanitize(expected),
                    "Steps to reproduce": sanitize(steps),
                    "Platform": sanitize(platform),
                    "Device Model": sanitize(model),
                    "Vendor": sanitize(vendor),
                    "OS": sanitize(os),
                    "OS Version": sanitize(os_version),
                    "Content Type": sanitize(content_type),
                    "Content ID": sanitize(content_id),
                    "Interruption": sanitize(video_interrupt),
                    "App Version": sanitize(app_version),
                    "Connectivity": sanitize(connectivity),
                    "Error Msg": sanitize(error_msg),
                    "Email": sanitize(email)
                },
            }
        ]
    }

    logger.info("Sending incident report with data %s", data)

    try:
        response = requests.post(request, headers=headers, data=json.dumps(data))
        response.raise_for_status()
    except Exception as err:
        logger.error(err)
        return None

    return response


def sanitize(value: Any, default=""):
    if value:
        return str(value)
    else:
        return default


def is_valid_os_name(name: str):
    pattern = re.compile(r"((android)|(ios)|(tvos))((?:\s*)?(\d+\.)?(\d+\.)?(\d+))?")
    return bool(pattern.match(name.lower())) or name.lower() == "unkown"


def match_os_version(slot_value: Any):
    # An app version is not a valid os version
    is_app_version = match_app_version(slot_value)
    if is_app_version:
        return None
    return match_version(slot_value, r"(\d+\.)?(\d+\.)?(\d+)")


def match_app_version(slot_value: Any):
    return match_version(slot_value, r"((?<!\.)(5\.)(\d+\.)?(\d+))")


def match_version(slot_value: Any, pattern: str):
    def search_match(candidate):
        match = re.search(pattern, candidate)
        if match and match[0]:
            matches.append(match[0])

    matches = []
    if type(slot_value) is list:
        for item in slot_value:
            search_match(item)
    else:
        search_match(slot_value)
    return matches


def find_fuzzy_match(candidate: str, items: List[Text]):
    for token in items:
        ratio = fuzz.ratio(candidate.lower(), token.lower())
        if ratio >= 70:
            return token
    return None
