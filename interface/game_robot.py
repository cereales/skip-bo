import logging, utils.Tools as Tools
logger = logging.getLogger(__name__)

from interface.robot import Robot
from utils.Emoji import Emoji



class GameRobot(Robot):
    """
    Represents one instance of a UI for BANG! game.
    """
    def __init__(self, client, channel):
        super().__init__(client, channel)
