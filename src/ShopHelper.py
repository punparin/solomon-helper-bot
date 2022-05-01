import os
import json
import requests
import urllib.parse
from io import BytesIO
from discord import Embed, Colour
from elasticsearch import Elasticsearch, helpers
from currency_converter import CurrencyConverter
from SolomonShopError import SolomonShopError
from CardInfo import CardInfo
from Card import Card


class ShopHelper:
    def __init__(self, logger):
        self.logger = logger
        self.index = "yugioh_cards"
        self.solomon_api_endpoint = os.environ["SOLOMON_API_ENDPOINT"]
        self.solomon_vision_api_endpoint = os.environ["SOLOMON_VISION_API_ENDPOINT"]
        self.es_endpoint = os.environ["ELASTICSEARCH_ENDPOINT"]
        self.currency_converter = CurrencyConverter()
        self.es = Elasticsearch(self.es_endpoint)

    def get_thb_price(self, yen_price):
        try:
            return int(self.currency_converter.convert(int(yen_price), "JPY", "THB"))
        except ValueError as err:
            return "-"

    def get_card_info(self, img_url):
        url = self.solomon_vision_api_endpoint + "/search-card"
        headers = {'Content-Type' : 'image/jpeg'}
        img = requests.get(img_url, stream=True)
        image_stream = BytesIO(img.content)

        try:
            r = requests.post(url, data=image_stream, headers=headers, verify=False)

            if r.status_code != 201:
                raise SolomonShopError("Encountered invalid request from Solomon Vision API")

            raw_card_info =  r.json()
            self.logger.info("ShopHelper.get_card_info", raw_card_info)
            
            return CardInfo(raw_card_info["en_name"], raw_card_info["jp_name"], raw_card_info["set_code"], raw_card_info["type"], raw_card_info["img_url"])
        except json.decoder.JSONDecodeError as err:
            self.logger.error("Finder.get_yuyutei_cards", err)
            raise SolomonAPIError("Encountered invalid response from Solomon API")

    def get_cards(self, source, jp_name):
        url = "{0}/api/cards?source={1}&name={2}".format(self.solomon_api_endpoint, source.lower(), urllib.parse.quote(jp_name))

        try:
            r = requests.get(url)

            if r.status_code != 200:
                raise SolomonAPIError("Encountered invalid request from Solomon API")

            return r.json()
        except json.decoder.JSONDecodeError as err:
            self.logger.error("Finder.get_cards", err)
            raise SolomonAPIError("Encountered invalid response from Solomon API")

    def merge_card_info_with_cards_from_source(self, card_info, source, cards):
        card_info.url = cards["url"]

        for card in cards["cards"]:
            new_card = Card(card["id"], source, card["rarity"], card["condition"], card["price"], self.get_thb_price(card["price"]))
            card_info.add_card(new_card)

        return card_info
