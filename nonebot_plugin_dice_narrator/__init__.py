import sys

from nonebot import get_driver
from nonebot.plugin import PluginMetadata
from pydantic import BaseModel

from nonebot_plugin_dice_narrator.config import config
from nonebot_plugin_dice_narrator.matchers import register_matcher


class _Config(BaseModel):
    pass


__plugin_meta__ = PluginMetadata(
    name="nonebot-plugin-dice-narrator",
    description="一只可爱的 AI 掷骰姬，支持各种事件检定",
    usage="检定 逃离触手怪的追捕",
    type="application",
    homepage="https://github.com/KroMiose/nonebot_plugin_dice_narrator",
    supported_adapters={"~onebot.v11"},
    config=_Config,
)

global_config = get_driver().config

register_matcher()

if "--load-test" in sys.argv:
    print("Plugin load tested successfully")
    exit(0)
