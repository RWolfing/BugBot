import logging
import os
from time import sleep
from typing import Text, Any, Dict

from dotenv import load_dotenv
from elasticsearch import ConnectionTimeout
from elasticsearch_dsl import Search, Q
from elasticsearch_dsl.connections import connections

load_dotenv()

elastic_host = os.environ.get('ELASTIC_HOST')
elastic_admin = os.environ.get('ELASTIC_ADMIN')
elastic_pswd = os.environ.get('ELASTIC_PSWD')
index_id = "supported_devices_v2"


connections.create_connection(hosts=[elastic_host], http_auth=(elastic_admin, elastic_pswd), timeout=20)

logger = logging.getLogger(__name__)


def search_model(model: str) -> Dict[Text, Any]:
    def do_search(query: str):
        result = {}
        search = Search(index=index_id) \
            .query(Q("multi_match", query=query, type="best_fields", fields=["Model Name^2", "Manufacturer"])) \
            .suggest('model', query, phrase={'field': 'Model Name'}) \
            .execute()
        if search.hits.total.value > 0:
            result["hit"] = search.hits[0].to_dict()

        for item in search.suggest.model:
            best_match = None
            for option in item.options:
                if not best_match or option.score > best_match.score:
                    best_match = option

            if best_match:
                result["suggestion"] = best_match.text
                break
        return result
    return retry_on_error(lambda: do_search(model))


def search_manufacturer(manufacturer: str) -> Dict[Text, Any]:
    def do_search(query: str):
        result = {}
        elastic_resp = Search(index=index_id)\
            .query(Q("multi_match", query=query, type="best_fields", fields=["Manufacturer"]))\
            .suggest('manufacturer', query, phrase={'field': 'Manufacturer'})\
            .execute()
        if elastic_resp.hits.total.value > 0:
            result["hit"] = elastic_resp.hits[0].to_dict()

        for item in elastic_resp.suggest.manufacturer:
            best_match = None
            for option in item.options:
                if not best_match or option.score > best_match.score:
                    best_match = option

            if best_match:
                result["suggestion"] = best_match.text
                break
        return result
    return retry_on_error(lambda: do_search(manufacturer))


def retry_on_error(action):
    for retry in range(3):
        try:
            return action()
        except ConnectionTimeout as cto:
            interval = retry * 1000
            logger.error(f"Connection timeout out while fetching search results. Retrying in {interval}", cto)
            sleep(interval)
            pass
        
    
