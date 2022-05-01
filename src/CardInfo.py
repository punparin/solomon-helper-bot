from Card import Card


class CardInfo:
    def __init__(self, en_name, jp_name, set_code, type, img_url):
        self.en_name = en_name
        self.jp_name = jp_name
        self.set_code = set_code
        self.type = type
        self.img_url = img_url
        self.url = None
        self.cards = []

    def add_card(self, card):
        self.cards.append(card)
