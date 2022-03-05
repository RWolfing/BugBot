# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions
import logging
from typing import Any, Text, Dict, List, OrderedDict

from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.events import AllSlotsReset, SlotSet
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import REQUESTED_SLOT
from rasa_sdk.types import DomainDict

from actions.elastic import search_model, search_manufacturer
from actions.util import create_incident_report, is_valid_os_name, match_os_version, match_app_version, ios, OS_IOS, \
    find_fuzzy_match, OS_ANDROID, VENDOR_APPLE

logger = logging.getLogger(__name__)

SLOT_PROBLEM_DESCR = "a_detailed_problem"
SLOT_REPRODUCE = "c_steps_to_reproduce"
SLOT_PLATFORM = "platform"
SLOT_APP_VERSION = "app_version"
SLOT_OS_NAME = "os_name"
SLOT_OS_VERSION = "os_version"
SLOT_ISSUE_TYPE = "issue_type"
SLOT_MODEL = "model_name"
SLOT_VENDOR = "vendor"
SLOT_VIDEO_CONTENT_TYPE = "video_content_type"
SLOT_VIDEO_CONTENT_ID = "video_content_id"
SLOT_CONNECTIVITY = "connectivity"
SLOT_INTERRUPTIONS = "video_interruptions"
SLOT_ERROR_MSG = "error_message"
SLOT_CONFIRM = "confirm_slot"
SLOT_CONFIRM_REQ = "confirm_required"

SLOT_VALUE_WEB = "web"

form_slots_required = [SLOT_PROBLEM_DESCR, SLOT_REPRODUCE, SLOT_MODEL, SLOT_PLATFORM, SLOT_VENDOR, SLOT_OS_NAME,
                       SLOT_OS_VERSION, SLOT_APP_VERSION]
form_slots_stream_interruptions = form_slots_required + [SLOT_VIDEO_CONTENT_TYPE, SLOT_VIDEO_CONTENT_ID,
                                                         SLOT_CONNECTIVITY]
form_slots_synchronisation = form_slots_required + [SLOT_VIDEO_CONTENT_TYPE, SLOT_VIDEO_CONTENT_ID, SLOT_INTERRUPTIONS,
                                                    SLOT_CONNECTIVITY]
form_slots_playback = form_slots_required + [SLOT_VIDEO_CONTENT_TYPE, SLOT_VIDEO_CONTENT_ID, SLOT_INTERRUPTIONS,
                                             SLOT_CONNECTIVITY, SLOT_ERROR_MSG]
form_slots_offline = [SLOT_INTERRUPTIONS, SLOT_VIDEO_CONTENT_ID]


def filter_slots(issue_type, slots: List[Text]):
    if issue_type == 'stream_interrupt':
        slots = form_slots_stream_interruptions
    if issue_type == 'synchronisation':
        slots = form_slots_synchronisation
    if issue_type == 'playback':
        slots = form_slots_playback
    if issue_type == 'offline':
        slots = form_slots_offline

    return slots


def unique(values):
    return list(dict.fromkeys(values))


def get_confirm_slot(tracker: Tracker):
    slot_confirm_required = tracker.get_slot(SLOT_CONFIRM_REQ)
    if not slot_confirm_required:
        slot_confirm_required = []

    return slot_confirm_required


def get_confidence_for_slot_value(tracker: Tracker, entity_name):
    for event in reversed(tracker.events):
        if event["event"] == "user":
            for entity in event["parse_data"]["entities"]:
                if entity["entity"] == entity_name:
                    return entity.get("confidence_entity", 1)
    return 1


def list_slot_to_list(slot, should_filter: bool = True):
    if slot is None:
        return []
    elif isinstance(slot, str):
        return [slot]
    else:
        if should_filter:
            return unique(slot.copy())
        return slot.copy()


class ValidatePlaybackIssueForm(FormValidationAction):

    def name(self) -> Text:
        return "validate_form_issue_playback"

    async def required_slots(self, slots_mapped_in_domain: List[Text], dispatcher: CollectingDispatcher,
                             tracker: Tracker, domain: DomainDict) -> List[Text]:
        logger.info("Checking required slots")
        slots = await super().required_slots(slots_mapped_in_domain, dispatcher, tracker, domain)
        slots = filter_slots(tracker.get_slot(SLOT_ISSUE_TYPE), slots) + ['email_contact']

        if tracker.get_slot(SLOT_PLATFORM) == SLOT_VALUE_WEB:
            slots.remove(SLOT_APP_VERSION)
            slots.remove(SLOT_OS_NAME)
            slots.remove(SLOT_OS_VERSION)
            slots.remove(SLOT_VENDOR)

        # If we have multiple matches for a slot that should be single we add a confirm slot to fire a
        # custom AskForConfirmation Action.
        slot_confirm_required = tracker.get_slot(SLOT_CONFIRM_REQ)
        if slot_confirm_required:
            logger.info("Required Slots: Confirmation required for %s", slot_confirm_required)
            logger.info("Inserting confirm_slot")
            slots.insert(0, SLOT_CONFIRM)

        logger.info(f"Required slots are {slots}")

        return unique(slots)

    async def extract_confirm_slot(
            self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict
    ) -> Dict[Text, Any]:
        slot_confirm_required = tracker.get_slot(SLOT_CONFIRM_REQ)
        if slot_confirm_required:
            return {SLOT_CONFIRM: None}
        return {SLOT_CONFIRM: "DONE"}

    async def validate_model_name(
            self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict
    ) -> Dict[Text, Any]:
        slot_value = list_slot_to_list(slot_value)

        if len(slot_value) == 0:
            return {SLOT_MODEL: None}
        elif len(slot_value) > 1:
            slot_confirm_required = get_confirm_slot(tracker)
            slot_confirm_required.append(SLOT_MODEL)
            return {SLOT_MODEL: slot_value, SLOT_CONFIRM: None, SLOT_CONFIRM_REQ: slot_confirm_required}

        slot_value = slot_value[0]
        if slot_value.lower() in ["phone", "tablet", "tv"]:
            dispatcher.utter_message(
                text=f"{slot_value} ist etwas zu generisch. Ich benötige die genaue Bezeichnung...")
            return {SLOT_MODEL: None}

        # We only check the confidence if we automatically filled the slot from the conversation, if we specifically ask
        # for it we also accept low confidence input
        slot_confidence = get_confidence_for_slot_value(tracker, SLOT_MODEL)
        if tracker.get_slot(REQUESTED_SLOT) != SLOT_MODEL and slot_confidence < 0.9:
            slot_confirm_required = get_confirm_slot(tracker)
            slot_confirm_required.append(SLOT_MODEL)
            logger.info("Confirmation necessary for app version: %s", slot_confirm_required)
            return {SLOT_MODEL: slot_value, SLOT_CONFIRM: None, SLOT_CONFIRM_REQ: slot_confirm_required}

        elastic_resp = search_model(slot_value)
        hit = elastic_resp.get("hit", dict())
        hit_model = hit.get("Model Name", "").strip()
        sugg = elastic_resp.get("suggestion", None)

        platform = tracker.get_slot(SLOT_PLATFORM)
        os_name = tracker.get_slot(SLOT_OS_NAME)
        manufacturer = tracker.get_slot(SLOT_VENDOR)

        # We do not have any browsers in our knowledge base. Devices named as browsers could overwrite values.
        if hit_model.lower() == slot_value.lower() and platform != SLOT_VALUE_WEB:
            platform = hit.get("Form Factor", platform)
            if platform == "Desktop":
                platform = SLOT_VALUE_WEB  # There is no desktop application only web
                slot_value = None  # Ask for the model again (this time browser name), TODO introduce specific slot

            is_android = hit.get("Android SDK Versions", None)
            if is_android:
                os_name = OS_ANDROID
            manufacturer = hit.get("Manufacturer", manufacturer)
            if manufacturer and manufacturer.lower() == VENDOR_APPLE:
                os_name = OS_IOS
        else:
            logger.info("Not prefilling from model name.")
            logger.info("Hit %s", hit)
            logger.info("Sugg %s", sugg)

            # Quick fix to identify apple devices
            for token in slot_value.split():
                if find_fuzzy_match(token, ios):
                    manufacturer = VENDOR_APPLE
                    os_name = OS_IOS

        result = {SLOT_MODEL: slot_value, SLOT_PLATFORM: platform, SLOT_OS_NAME: os_name, SLOT_VENDOR: manufacturer}
        logger.info("Setting slots: %s", result)
        return result

    async def validate_os_name(
            self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict
    ) -> Dict[Text, Any]:
        values = list_slot_to_list(slot_value)
        valid_values = []

        for value in values:
            value = value.lower()  # Rasa matches the string in conditional utterances case sensitive
            if is_valid_os_name(value):
                valid_values.append(value)

        if len(valid_values) == 0:
            return {SLOT_OS_NAME: None}
        elif len(valid_values) == 1:
            value = valid_values[0]
            os_version = match_os_version(value)
            if os_version:
                return {SLOT_OS_NAME: value, SLOT_OS_VERSION: os_version}
            return {SLOT_OS_NAME: value}
        else:
            slot_confirm_required = get_confirm_slot(tracker)
            slot_confirm_required.append(SLOT_OS_NAME)
            return {SLOT_OS_NAME: valid_values, SLOT_CONFIRM: None, SLOT_CONFIRM_REQ: slot_confirm_required}

    async def validate_os_version(
            self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict
    ) -> Dict[Text, Any]:
        os_version = match_os_version(slot_value)
        requested_slot = tracker.get_slot("requested_slot")
        prev_value = tracker.get_slot("os_version")

        if requested_slot == SLOT_OS_VERSION and not os_version:
            dispatcher.utter_message(response="utter_validate_os_version")
            return {SLOT_OS_VERSION: None}

        if not os_version:
            return {SLOT_OS_VERSION: prev_value}

        return {SLOT_OS_VERSION: os_version}

    async def validate_app_version(
            self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict
    ) -> Dict[Text, Any]:
        logger.info("Validating app version... Value %s", slot_value)
        versions = match_app_version(slot_value)
        logger.info("Candidates are %s", versions)

        if not versions:
            dispatcher.utter_message(response="utter_validate_app_version")
            return {SLOT_APP_VERSION: None}

        if len(versions) > 1:
            slot_confirm_required = get_confirm_slot(tracker)
            slot_confirm_required.append(SLOT_APP_VERSION)
            logger.info("Confirmation necessary for app version: %s", slot_confirm_required)
            return {SLOT_APP_VERSION: versions, SLOT_CONFIRM: None, SLOT_CONFIRM_REQ: slot_confirm_required}

        return {SLOT_APP_VERSION: versions}

    async def validate_vendor(
            self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict
    ) -> Dict[Text, Any]:
        slots = {}
        slot_value = list_slot_to_list(slot_value)

        if len(slot_value) > 1:
            slot_confirm_required = get_confirm_slot(tracker)
            slot_confirm_required.append(SLOT_VENDOR)
            logger.info("Confirmation necessary for vendor: %s", slot_confirm_required)
            return {SLOT_VENDOR: slot_value, SLOT_CONFIRM: None, SLOT_CONFIRM_REQ: slot_confirm_required}

        manufacturer = next(iter(slot_value), None)
        elastic_resp = search_manufacturer(manufacturer)
        hit = elastic_resp.get("hit", dict())
        hit_manufacturer = hit.get("Manufacturer", "").strip()

        # Check if we find the manufacturer in our knowledge base
        if manufacturer and hit_manufacturer.lower() == manufacturer.lower():
            is_android = hit.get("Android SDK Versions", None)
            if is_android:
                slots[SLOT_OS_NAME] = OS_ANDROID
            manufacturer = hit.get("Manufacturer", manufacturer)
            if manufacturer and manufacturer.lower() == VENDOR_APPLE:
                slots[SLOT_OS_NAME] = OS_IOS
        elif manufacturer:
            # If not we try a simple backup fuzzy matching common tokens
            match_ios = find_fuzzy_match(manufacturer, ios)
            if match_ios:
                slots[SLOT_OS_NAME] = OS_IOS

        slots[SLOT_VENDOR] = manufacturer
        return slots


class AskForConfirmation(Action):
    def name(self) -> Text:
        return "action_ask_" + SLOT_CONFIRM

    async def run(self, dispatcher: "CollectingDispatcher", tracker: Tracker,
                  domain: "DomainDict") -> List[Dict[Text, Any]]:
        slot_confirm_required = tracker.get_slot(SLOT_CONFIRM_REQ)
        if slot_confirm_required:
            item = list(OrderedDict.fromkeys(slot_confirm_required))[0]
            slot_confirm_required.remove(item)

            # 1. Detected multiple application version - Asking confirmation
            if item == SLOT_APP_VERSION:
                candidates = tracker.get_slot(SLOT_APP_VERSION)
                buttons = []
                for version in candidates:
                    buttons.append({'payload': f'/inform{{"app_version":"{version}"}}', 'title': version})
                dispatcher.utter_message(response="utter_ask_confirm_app_version", buttons=buttons)
                return [SlotSet(SLOT_APP_VERSION, None), SlotSet(SLOT_CONFIRM_REQ, slot_confirm_required)]
            # 2. Detect a model name with low confidence
            if item == SLOT_MODEL:
                candidates = list_slot_to_list(tracker.get_slot(SLOT_MODEL))
                if len(candidates) > 1:
                    buttons = []
                    for candidate in candidates:
                        buttons.append({'payload': f'/inform{{"model_name":"{candidate}"}}', 'title': candidate})
                    dispatcher.utter_message(response="utter_ask_select_model", buttons=buttons)
                else:
                    buttons = [{'payload': f'/deny', 'title': "Nein"},
                               {'payload': f'/inform{{"model_name":"{candidates[0]}"}}', 'title': "Ja"}]
                    dispatcher.utter_message(response="utter_ask_confirm_model_name", buttons=buttons)
                return [SlotSet(SLOT_MODEL, None), SlotSet(SLOT_CONFIRM_REQ, slot_confirm_required)]
            # 3. Detected multiple os names - Asking confirmation
            if item == SLOT_OS_NAME:
                candidates = tracker.get_slot(SLOT_OS_NAME)
                buttons = []
                for name in candidates:
                    buttons.append({'payload': f'/inform{{"os_name":"{name}"}}', 'title': name})
                dispatcher.utter_message(response="utter_ask_confirm_os_name", buttons=buttons)
                return [SlotSet(SLOT_OS_NAME, None), SlotSet(SLOT_CONFIRM_REQ, slot_confirm_required)]
            # 4. Multiple Manufacturers - Ask for confirmation
            if item == SLOT_VENDOR:
                candidates = tracker.get_slot(SLOT_VENDOR)
                buttons = []
                for manufacturer in candidates:
                    buttons.append({'payload': f'/inform{{"vendor":"{manufacturer}"}}', 'title': manufacturer})
                dispatcher.utter_message(response="utter_ask_confirm_vendor", buttons=buttons)
                return [SlotSet(SLOT_VENDOR, None), SlotSet(SLOT_CONFIRM_REQ, slot_confirm_required)]
        return []


class SubmitIncidentAction(Action):
    affirm_intents = ['confirm', 'thankyou']
    deny_intents = ['deny', 'cancel']

    def name(self) -> Text:
        return "submit_incident"

    async def run(self, dispatcher: "CollectingDispatcher", tracker: Tracker,
                  domain: "DomainDict") -> List[Dict[Text, Any]]:

        last_intent = tracker.latest_message['intent'].get('name')
        if last_intent in self.affirm_intents:
            response = create_incident_report(
                problem=tracker.get_slot(SLOT_PROBLEM_DESCR),
                expected=tracker.get_slot("b_expected_behavior"),
                steps=tracker.get_slot(SLOT_REPRODUCE),
                platform=tracker.get_slot(SLOT_PLATFORM),
                model=tracker.get_slot(SLOT_MODEL),
                vendor=tracker.get_slot(SLOT_VENDOR),
                os=tracker.get_slot(SLOT_OS_NAME),
                os_version=tracker.get_slot(SLOT_OS_VERSION),
                content_type=tracker.get_slot(SLOT_VIDEO_CONTENT_TYPE),
                content_id=tracker.get_slot(SLOT_VIDEO_CONTENT_ID),
                video_interrupt=tracker.get_slot(SLOT_INTERRUPTIONS),
                app_version=tracker.get_slot(SLOT_APP_VERSION),
                connectivity=tracker.get_slot(SLOT_CONNECTIVITY),
                error_msg=tracker.get_slot(SLOT_ERROR_MSG),
                email=tracker.get_slot("email_contact")
            )
            if response:
                dispatcher.utter_message(response="utter_incident_submit_success")
                dispatcher.utter_message(response="utter_do_survey")
                return [AllSlotsReset()]
            else:
                dispatcher.utter_message(response="utter_general_error")
                dispatcher.utter_message(response="utter_handoff")
                return [AllSlotsReset()]
        else:
            dispatcher.utter_message(response="utter_acknowledge")
            dispatcher.utter_message(response="utter_handoff")
            return [AllSlotsReset()]


class ActionExplainRequestSlot(Action):

    def name(self) -> Text:
        return "action_explain_requested_slot"

    async def run(self, dispatcher: "CollectingDispatcher", tracker: Tracker,
                  domain: "DomainDict") -> List[Dict[Text, Any]]:
        requested_slot = tracker.get_slot("requested_slot")
        logger.info("Explain slot %s", requested_slot)

        responses = domain.get("responses", {})
        utterance = f"utter_explain_{requested_slot}"
        if utterance not in responses:
            logger.warning("Trying to utter %s but utterance does not exist!", utterance)
            dispatcher.utter_message(response="utter_can_not_explain")
            return []
        else:
            dispatcher.utter_message(response=utterance)
            return []


class ActionHelpRequestSlot(Action):

    def name(self) -> Text:
        return "action_help_fill_requested_slot"

    async def run(self, dispatcher: "CollectingDispatcher", tracker: Tracker,
                  domain: "DomainDict") -> List[Dict[Text, Any]]:
        requested_slot = tracker.get_slot("requested_slot")
        logger.info("Trying to help fill slot %s", requested_slot)

        responses = domain.get("responses", {})
        utterance = f"utter_help_{requested_slot}"
        if utterance not in responses:
            logger.warning("Trying to utter %s but utterance does not exist!", utterance)
            dispatcher.utter_message(response="utter_can_not_help_slot")
            return []
        else:
            dispatcher.utter_message(response=utterance)
            return []


class ActionSetIncidentTypeSlot(Action):
    def name(self) -> Text:
        return "action_set_incident_type_slot"

    async def run(self, dispatcher: "CollectingDispatcher", tracker: Tracker,
                  domain: "DomainDict") -> List[Dict[Text, Any]]:

        intent = tracker.get_intent_of_latest_message()
        issue_type = 'undefined'
        if intent == 'issue_playback':
            issue_type = 'playback'
        if intent == 'issue_stream_interruptions':
            issue_type = 'stream_interrupt'
        if intent == 'issue_synchronization':
            issue_type = 'synchronisation'
        if intent == 'issue_offline':
            issue_type = 'offline'

        return [SlotSet(SLOT_ISSUE_TYPE, issue_type)]
