from typing import Type

from nonebot import on_command
from nonebot.adapters import Bot, Message
from nonebot.adapters.onebot.v11 import (
    MessageEvent,
)
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.params import CommandArg

from nonebot_plugin_dice_narrator import config
from nonebot_plugin_dice_narrator.narrator import run_narrator
from nonebot_plugin_dice_narrator.utils.message_parse import gen_chat_text


def register_matcher():
    """注册消息响应器"""

    identity: Type[Matcher] = on_command(
        "检定",
        aliases={"判定", "鉴定"},
        priority=20,
        block=True,
    )

    @identity.handle()
    async def _(
        matcher: Matcher,
        event: MessageEvent,
        bot: Bot,
        arg: Message = CommandArg(),
    ):
        global is_progress  # 是否产生编辑进度
        is_progress = False
        # 判断是否是禁止使用的用户
        if event.get_user_id() in config.FORBIDDEN_USERS:
            await identity.finish(
                f"您的账号({event.get_user_id()})已被禁用，请联系管理员。",
            )

        raw_cmd: str = arg.extract_plain_text()
        content, _ = await gen_chat_text(event=event, bot=bot)
        logger.info(f"接收到指令: {raw_cmd} | Parsed: {content}")

        if raw_cmd:
            await run_narrator(question=content[2:].strip(), matcher=matcher)
