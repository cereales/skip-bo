import logging, utils.Tools as Tools
logger = logging.getLogger(__name__)

from interface.robot import Robot
from utils.Emoji import Emoji
import random


class State:
    CREATED = 0
    INITIALIZED = 1
    PLAYING = 3


class GameRobot(Robot):
    """
    Represents one instance of a UI for BANG! game.
    """
    def __init__(self, client, channel):
        super().__init__(client, channel)
        self.state = State.CREATED
        self.pile = []
        for family_id in range(12):
            for card_value in range(1, 13):
                self.pile.append(card_value)
        for joker_id in range(18):
            self.pile.append(0)
        random.shuffle(self.pile)
        self.players = []
        self.players_main = []
        self.players_jeu = []
        self.players_pile = []
        self.places = []
        self.discard = []
        logger.info(self.pile)

    async def init(self):
        assert self.state == State.CREATED
        self.state = State.INITIALIZED
        message = await self.refresh_welcome_message()
        await message.add_reaction(Emoji.get_unicode_emoji("point_up"))
        await message.add_reaction(Emoji.get_unicode_emoji("play"))
        await message.add_reaction(Emoji.get_unicode_emoji("abort"))

    async def on_raw_reaction_add(self, payload):
        if payload.user_id == self.client.user.id:
            logger.log(Tools.VERBOSE, "Ignore reaction from bot.")
            return
        # ignore reactions to others messages than the waiting one
        if not self.is_tracked(payload.message_id):
            logger.log(Tools.VERBOSE, "Ignore reaction to untracked message.")
            return


        if self.state == State.INITIALIZED:
            expected_message = await self.get_message()
            if self.emoji_on_message("point_up", payload, expected_message):
                self.players.append(payload.user_id)
                self.players_main.append([])
                self.players_pile.append([])
                self.players_jeu.append([[] for _ in range(4)])
            elif self.emoji_on_message("play", payload, expected_message):
                self.state = State.PLAYING
                for _ in range (10):
                    for p in range(len(self.players)):
                        self.players_pile[p].append(self.pile.pop())
                for _ in range(4):
                    self.places.append([])
                logger.info(self.players_pile)
                # for p in self.players:
                await self.send("Emplacements : {} {}    {} {}    {} {}    {} {}\n".format(self.a_place(0, -2), self.a_place(0, -1), self.a_place(1, -2), self.a_place(1, -1), self.a_place(2, -2), self.a_place(2, -1), self.a_place(3, -2), self.a_place(3, -1), ) + "\n".join(["{} : ({}) {}\n".format(self.players[p], len(self.players_pile[p]) - 1, self.players_pile[p][-1]) + "\n".join(["- " + ", ".join(self.players_jeu[p][i]) for i in range(4)]) for p in range(len(self.players))]))

    def a_place(self, place, i):
        return self.places[place][i] if len(self.places[place]) >= -i else "x"

    async def refresh_welcome_message(self):
        return await self.refresh("Commencer ?")
