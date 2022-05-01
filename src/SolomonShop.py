import re
import os
from discord import Embed, Colour
from discord_components import DiscordComponents, ComponentsBot, Button, SelectOption, Select
import discord.ext.commands as commands
from CardInfo import CardInfo
from Logger import Logger
from ShopHelper import ShopHelper
from SheetHandler import SheetHandler


class SolomonShop:
    def __init__(self, logger):
        self.logger = logger
        self.bot_id = os.getenv('BOT_ID')
        self.shopHelper = ShopHelper(logger)
        self.SheetHandler = SheetHandler(logger)

    def get_embed_name(self, card_info):
        embed = Embed(title="Is this what you're looking for?", color=Colour.dark_teal())
        embed.set_thumbnail(url=card_info.img_url)
        embed.add_field(name=card_info.en_name, value="[{0}] {1}".format(card_info.set_code, card_info.jp_name))

        return embed

    def get_success_embed(self):
        return Embed(title="The new card has been updated to your stock", color=Colour.green())

    def get_failed_embed(self, message):
        return Embed(title=message, color=Colour.red())

    def get_source_icon(self, source):
        if source.lower() == "bigweb":
            return os.getenv('BIGWEB_ICON')
        elif source.lower() == "yuyutei":
            return os.getenv('YUYUTEI_ICON')

    def get_selected_card_embed(self, card_info, card):
        embed = Embed(title="Add this card to your stock?", color=Colour.teal())
        embed.set_author(name=card.source, url=card_info.url, icon_url=self.get_source_icon(card.source))
        embed.set_thumbnail(url=card_info.img_url)

        info = "ID: {0}\nRarity: {1}\nCondition: {2}\nPrice: ¥{3} (THB {4})".format(
            card.id,
            card.rarity,
            card.condition,
            card.jpy_price,
            card.thb_price
        )
        embed.add_field(name="{0} ({1})".format(card_info.en_name, card_info.jp_name), value=info)

        return embed

    def get_embed_from_card_info(self, card_info, source, cards):
        embed = Embed(title="{0} ({1})".format(card_info.en_name, card_info.jp_name), color=Colour.orange())
        embed.set_author(name=source, url=card_info.url, icon_url=self.get_source_icon(source))
        embed.set_thumbnail(url=card_info.img_url)

        for i in range(len(card_info.cards)):
            card = card_info.cards[i]
            
            if card.source == source.lower():
                info = "ID: {0}\nRarity: {1}\nCondition: {2}\nPrice: ¥{3} (THB {4})".format(
                    card.id,
                    card.rarity,
                    card.condition,
                    card.jpy_price,
                    card.thb_price
                )
                embed.add_field(name="#" + str(i), value=info)

        return embed

    def get_card_options(self, card_info):
        options = []
        count = 0

        for i in range(len(card_info.cards)):
            card = card_info.cards[i]
            option = SelectOption(label="{0}: {1}".format(i, card), value=i)
            options.append(option)
            count += 1

            if count == 25:
                break

        return Select(
                placeholder="Select your card",
                options=options
            )

    async def process(self, client, ctx):
        if ctx.author.id == self.bot_id:
            return

        if len(ctx.attachments) == 0:
            return
        
        img_url = ctx.attachments[0].url
        card_info = self.shopHelper.get_card_info(img_url)
        name_embed = self.get_embed_name(card_info)

        if card_info.jp_name is None:
            await ctx.channel.send(embed=self.get_failed_embed("Card not found"))
            return

        yuyutei_cards = self.shopHelper.get_cards("yuyutei", card_info.jp_name)
        bigweb_cards = self.shopHelper.get_cards("bigweb", card_info.jp_name)
        card_info = self.shopHelper.merge_card_info_with_cards_from_source(card_info, "yuyutei", yuyutei_cards)
        card_info = self.shopHelper.merge_card_info_with_cards_from_source(card_info, "bigweb", bigweb_cards)

        yes_button = Button(label="Yes", style="3", custom_id="yes")

        # Check if name is correct
        await ctx.channel.send(embed=name_embed, components=[[yes_button]])
        interaction = await client.wait_for("button_click", check=lambda i: i.custom_id == "yes")

        yuyutei_embed = self.get_embed_from_card_info(card_info, "YUYUTEI", yuyutei_cards)
        bigweb_embed = self.get_embed_from_card_info(card_info, "Bigweb", bigweb_cards)

        await ctx.channel.send(embed=yuyutei_embed)
        await ctx.channel.send(embed=bigweb_embed)

        card_options = self.get_card_options(card_info)

        await interaction.send("Select your card", components=[[card_options]])

        selected_interaction = await client.wait_for("select_option")
        selected_card = card_info.cards[int(selected_interaction.values[0])]
        selected_card_embed = self.get_selected_card_embed(card_info, selected_card)
        confirm_button = Button(label="Confirm", style="2", emoji="🥴", custom_id="confirm")

        await selected_interaction.send(embed=selected_card_embed, components=[[confirm_button]])

        confirm_interaction = await client.wait_for("button_click", check=lambda i: i.custom_id == "confirm")
        
        self.SheetHandler.add_new_record(
            card_info.en_name,
            selected_card.rarity,
            "",
            selected_card.id,
            selected_card.jpy_price,
            selected_card.thb_price
            )
        
        await confirm_interaction.send(embed=self.get_success_embed())
