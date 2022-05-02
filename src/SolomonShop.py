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
    def __init__(self, logger, client):
        self.logger = logger
        self.client = client
        self.bot_id = os.getenv('BOT_ID')
        self.shopHelper = ShopHelper(logger)
        self.SheetHandler = SheetHandler(logger)
        self.card_conditions = ["-", "99", "95", "90", "85", "80", "75", "70", "65", "60", "55", "50"]

    def get_embed_name(self, card_info):
        embed = Embed(title="Is this what you're looking for?", color=Colour.dark_teal())
        embed.set_thumbnail(url=card_info.img_url)
        embed.add_field(name=card_info.en_name, value="[{0}] {1}".format(card_info.set_code, card_info.jp_name))

        return embed

    def get_success_embed(self):
        return Embed(title="The new card has been updated to your stock", color=Colour.green())

    def get_bye_embed(self):
        return Embed(title="Bye bye 👋", color=Colour.lighter_grey())

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

        info = "ID: {0}\nRarity: {1}\nCondition: {2}%\nPrice: ¥{3} (THB {4})".format(
            card.id,
            card.rarity,
            card.own_condition,
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

    def get_condition_options(self):
        options = []

        for condition in self.card_conditions:
            option = SelectOption(label=condition, value=condition)
            options.append(option)

        return Select(
                placeholder="What is the card's condition?",
                options=options
            )

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

    async def select_desired_card(self, ctx):
        img_url = ctx.attachments[0].url
        card_info = self.shopHelper.get_card_info(img_url)
        name_embed = self.get_embed_name(card_info)

        if card_info.jp_name is None:
            await ctx.channel.send(embed=self.get_failed_embed("Card not found"))
            return

        yes_button = Button(label="Yes", style="3", emoji="👍🏼", custom_id="yes")
        no_button = Button(label="No", style="4", emoji="👎🏼", custom_id="no")

        await ctx.channel.send(embed=name_embed, components=[[yes_button, no_button]])
        interaction = await self.client.wait_for("button_click", check=lambda i: i.custom_id == "yes" or i.custom_id == "no")

        return interaction, card_info

    async def select_card(self, ctx, interaction, card_info):
        yuyutei_cards = self.shopHelper.get_cards("yuyutei", card_info.jp_name)
        bigweb_cards = self.shopHelper.get_cards("bigweb", card_info.jp_name)
        card_info = self.shopHelper.merge_card_info_with_cards_from_source(card_info, "yuyutei", yuyutei_cards)
        card_info = self.shopHelper.merge_card_info_with_cards_from_source(card_info, "bigweb", bigweb_cards)
        yuyutei_embed = self.get_embed_from_card_info(card_info, "YUYUTEI", yuyutei_cards)
        bigweb_embed = self.get_embed_from_card_info(card_info, "Bigweb", bigweb_cards)

        await ctx.channel.send(embed=yuyutei_embed)
        await ctx.channel.send(embed=bigweb_embed)

        card_options = self.get_card_options(card_info)

        await interaction.send("Select your card", components=[[card_options]])
        selected_interaction = await self.client.wait_for("select_option")

        return selected_interaction, card_info, card_info.cards[int(selected_interaction.values[0])]

    async def select_card_condition(self, interaction, selected_card):
        condition_options = self.get_condition_options()

        await interaction.send("Select your card's condition", components=[[condition_options]])
        condition_interaction = await self.client.wait_for("select_option")

        own_condition = condition_interaction.values[0]
        selected_card.own_condition = own_condition

        return condition_interaction, selected_card

    async def confirm_card(self, interaction, card_info, selected_card):
        selected_card_embed = self.get_selected_card_embed(card_info, selected_card)
        confirm_button = Button(label="Confirm", style="3", emoji="🥴", custom_id="confirm")
        cancel_button = Button(label="Cancel", style="4", emoji="😬", custom_id="cancel")

        await interaction.send(embed=selected_card_embed, components=[[confirm_button, cancel_button]])

        confirm_interaction = await self.client.wait_for("button_click", check=lambda i: i.custom_id == "confirm" or i.custom_id == "cancel")

        return confirm_interaction

    async def bye(self, interaction):
        bye_embed = self.get_bye_embed()

        await interaction.send(embed=bye_embed)

    async def update_sheet(self, interaction, card_info, selected_card):
        self.SheetHandler.add_new_record(
            card_info.en_name,
            selected_card.rarity,
            card_info.type,
            selected_card.id,
            selected_card.own_condition,
            selected_card.jpy_price,
            selected_card.thb_price
            )
        
        success_interaction = await interaction.send(embed=self.get_success_embed())

        return success_interaction

    async def process(self, ctx):
        if ctx.author.id == self.bot_id:
            return

        if len(ctx.attachments) == 0:
            return

        desired_card_interaction, card_info = await self.select_desired_card(ctx)
        if desired_card_interaction.custom_id == "no":
            await self.bye(desired_card_interaction)
            return

        selected_interaction, card_info, selected_card = await self.select_card(ctx, desired_card_interaction, card_info)
        condition_interaction, selected_card = await self.select_card_condition(selected_interaction, selected_card)
        confirm_interaction = await self.confirm_card(condition_interaction, card_info, selected_card)
        if confirm_interaction.custom_id == "cancel":
            await self.bye(confirm_interaction)
            return

        success_interaction = await self.update_sheet(confirm_interaction, card_info, selected_card)
