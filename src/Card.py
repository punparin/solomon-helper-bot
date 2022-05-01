class Card:
    def __init__(self, id, source, rarity, condition, jpy_price, thb_price):
        self.id = id
        self.source = source
        self.rarity = rarity
        self.condition = condition
        self.jpy_price = jpy_price
        self.thb_price = thb_price

    def __str__(self):
        return "[{0}] {1} - ¥{2}".format(
            self.id,
            self.rarity,
            self.jpy_price
        )
