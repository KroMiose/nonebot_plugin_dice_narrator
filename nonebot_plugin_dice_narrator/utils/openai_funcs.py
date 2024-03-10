from typing import Dict, List, Literal, Optional, Tuple

import httpx
import openai
from nonebot import logger
from openai import AsyncOpenAI
from pydantic import BaseModel

from nonebot_plugin_dice_narrator.config import config

openai.base_url = config.OPENAI_BASE_URL
openai_key_idx = 0


class RunOutOfKey(Exception):
    pass


def _key_iterator_decorator(openai_req_func):
    async def wrapper(**kwargs):
        global openai_key_idx

        try_cnt = len(config.OPENAI_API_KEYS)
        while try_cnt > 0:
            try_cnt -= 1
            openai_key_idx = (openai_key_idx + 1) % len(config.OPENAI_API_KEYS)
            openai.api_key = config.OPENAI_API_KEYS[openai_key_idx]
            try:
                return await openai_req_func(
                    api_key=(
                        config.OPENAI_API_KEYS[openai_key_idx]
                        if "api_key" not in kwargs
                        else kwargs["api_key"]
                    ),
                    **kwargs,
                )
            except Exception as e:
                logger.error(
                    f"Failed to run {openai_req_func.__name__} with Exception: {e}",
                )
        else:
            raise RunOutOfKey

    return wrapper


@_key_iterator_decorator
async def gen_chat_response_text(
    messages: List[Dict],
    temperature: float = 0,
    frequency_penalty: float = 0.2,
    presence_penalty: float = 0.2,
    top_p=1,
    api_key: Optional[str] = None,
) -> Tuple[str, int]:
    """生成聊天回复内容"""

    client = AsyncOpenAI(
        api_key=api_key,
        base_url=config.OPENAI_BASE_URL,
        http_client=(
            httpx.AsyncClient(
                proxies=config.OPENAI_PROXY,
            )
            if config.OPENAI_PROXY
            else None
        ),
    )

    res = await client.chat.completions.create(
        model=config.CHAT_MODEL,
        messages=messages,  # type: ignore
        temperature=temperature,
        frequency_penalty=frequency_penalty,
        presence_penalty=presence_penalty,
        top_p=top_p,
    )
    logger.info(res)

    output = res.choices[0].message.content
    token_consumption = res.usage.total_tokens if res.usage else -1
    logger.info(f"请求消耗: {token_consumption} tokens")
    assert output, "Chat response is empty"
    return output, token_consumption
