from nonebot import get_driver
from nonebot.plugin import PluginMetadata

from nonebot_plugin_dice_narrator.config import config
from nonebot_plugin_dice_narrator.matchers import register_matcher

__plugin_meta__ = PluginMetadata(
    name="nonebot-plugin-dice-narrator",
    description="",
    usage="检定 逃离触手怪的追捕",
    type="application",
)

global_config = get_driver().config

register_matcher()
