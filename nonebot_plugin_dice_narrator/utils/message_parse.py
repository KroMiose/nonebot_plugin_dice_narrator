from typing import Optional, Tuple, Union

from nonebot.adapters import Bot
from nonebot.adapters.onebot.v11 import (
    GroupIncreaseNoticeEvent,
    GroupMessageEvent,
    MessageEvent,
)


async def gen_chat_text(event: MessageEvent, bot: Bot) -> Tuple[str, bool]:
    """生成合适的会话消息内容(eg. 将cq at 解析为真实的名字)"""
    if not isinstance(event, GroupMessageEvent):
        return event.get_plaintext(), False

    wake_up = False
    msg = ""
    for seg in event.message:
        if seg.is_text():
            msg += seg.data.get("text", "")
        elif seg.type == "at":
            qq = seg.data.get("qq", None)
            if qq:
                if qq == "all":
                    msg += "@全体成员"
                    wake_up = True
                else:
                    user_name = await get_user_name(
                        event=event,
                        bot=bot,
                        user_id=int(qq),
                    )
                    if user_name:
                        msg += (
                            f"@{user_name}"  # 保持给bot看到的内容与真实用户看到的一致
                        )
    return msg, wake_up


async def get_user_name(
    event: Union[MessageEvent, GroupIncreaseNoticeEvent],
    bot: Bot,
    user_id: int,
) -> Optional[str]:
    """获取QQ用户名"""
    if (
        isinstance(event, GroupMessageEvent)
        and event.sub_type == "anonymous"
        and event.anonymous
    ):  # 匿名消息
        return f"[匿名]{event.anonymous.name}"

    if isinstance(event, (GroupMessageEvent, GroupIncreaseNoticeEvent)):
        user_info = await bot.get_group_member_info(
            group_id=event.group_id,
            user_id=user_id,
            no_cache=False,
        )
        user_name = user_info.get("nickname", None)
        user_name = user_info.get("card", None) or user_name
    else:
        user_name = event.sender.nickname if event.sender else event.get_user_id()

    return user_name
