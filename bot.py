"""
Main executable file.
In this file, instanciate discord client and listen to events.
Then distribute events to appropriate entities.
"""
### Setup logger
import logging, utils.Tools as Tools
logging.basicConfig(level=logging.DEBUG)
logging.addLevelName(Tools.VERBOSE, "VERBOSE") # level must be > 0
logging.getLogger("discord").setLevel(logging.WARNING)
logging.getLogger("websockets").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
# logger.setLevel(Tools.VERBOSE)

import sys, configparser, traceback
import asyncio, discord
from actions.action_list import ActionList
from actions.help import Help
from actions.stop import Stop
from actions.game import Game
from interface.robot_manager import RobotManager



# Read context from input argument
if len(sys.argv) < 2:
    print("Use:\t{} context".format(sys.argv[0]))
    exit(1)

# Global variables
CONTEXT = sys.argv[1]
COMMON = "COMMON"
CONFIG_PATH = "resources/config.ini"

# Read config file
try:
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH)

    prefix_command = config[COMMON]["prefix_command"]

    TOKEN = config[CONTEXT]["token"]
    allowed_channels = []
    allowed_channels.append(int(config[CONTEXT]["target_channel"]))
    allowed_channels.append(int(config[CONTEXT]["private_channel"]))
    error_channel = int(config[CONTEXT]["error_channel"])
except:
    logger.error("Cannot read properly config file.")
    raise


client = discord.Client()

ActionList.add_action(Help)
ActionList.add_action(Stop)
ActionList.add_action(Game)


def action_called(action, message_content):
    first_word = message_content.split()[0]
    full = first_word == action.command()
    short = first_word == action.command_short()
    return full or short


async def parse_command(message):
    if message.content[0] != prefix_command:
        return
    logger.debug("Command prefix detected : %s", message.content)
    for action in ActionList.actions:
        if action_called(action, message.content[1:]):
            logger.debug("Command detected.")
            await action.on_call(message, client)


async def displayMessage(message):
    message_content = message.content
    isPrivateMessage = type(message.channel) == discord.DMChannel
    if isPrivateMessage:
        logger.debug("In private message.")
        serverNameOrPrivate = "PRIVATE"
        channelName = ""
        authorName = message.author.name
    else:
        assert type(message.channel) == discord.TextChannel # can also be GroupChannel
        logger.debug("In server : %s", message.guild)
        serverNameOrPrivate = message.guild.name
        channelName = message.channel.name
        authorName = message.author.display_name # FIXME: doesnot work with nicked
        if authorName != message.author.name:
            logger.debug("%s is nicknamed %s", message.author.name, authorName)
    logger.info("(%s) [%s] %s : %s", serverNameOrPrivate, channelName, authorName, message_content)


@client.event
async def on_raw_reaction_add(payload):
    logger.debug("Reaction {} detected ({}).".format(payload.emoji.name, payload.emoji.name.encode("ascii", 'backslashreplace')))
    try:
        await RobotManager.on_raw_reaction_add(payload)
    except:
        msg = traceback.format_exc()
        logger.error(msg)
        channel = client.get_channel(error_channel)
        await channel.send(msg)


@client.event
async def on_message(message):
    try:
        if message.channel.id not in allowed_channels:
            return
        await displayMessage(message)
        if message.author == client.user:
            return

        logger.debug("Message %s to parse is :\"%s\"", message.id, message.content)
        await parse_command(message)

    except Exception as e:
        msg = traceback.format_exc()
        logger.error(msg)
        channel = client.get_channel(error_channel)
        await channel.send(msg)


@client.event
async def on_ready():
    logger.debug("%s connected.", client.user.name)
    helpMessage = discord.Game(prefix_command + "help for help")
    await client.change_presence(activity=helpMessage)


"""
@client.event
async def on_error(event, *args, **kwargs):
    channel = client.get_channel(error_channel)
    try:
        await channel.send("Error in method *"+ str(event) + "* on message : `" + str(args[0]) + "`.")
    except:
        await channel.send("Error in %s.", event)
"""


try:
    client.run(TOKEN)
except KeyboardInterrupt:
    pass
