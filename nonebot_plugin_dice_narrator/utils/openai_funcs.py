from math import log
from typing import Dict, List, Optional, Tuple

import httpx
import openai
import pkg_resources
from nonebot import logger

from nonebot_plugin_dice_narrator.config import config

__openai_version = pkg_resources.get_distribution("openai").version

if __openai_version <= "0.28.0":    # 低版本 openai 兼容
    openai.api_base = config.OPENAI_BASE_URL  # type: ignore
else:
    from openai import AsyncOpenAI  # type: ignore

    openai.base_url = config.OPENAI_BASE_URL  # type: ignore

openai_key_idx = 0


class RunOutOfKeyException(Exception):
    
    def __init__(self, message: str = ""):
        self.message = message
        super().__init__(message)


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
            raise RunOutOfKeyException("Run out of API keys")

    return wrapper


@_key_iterator_decorator
async def gen_chat_response_text(
    messages: List[Dict],
    temperature: float = 0,
    frequency_penalty: float = 0.2,
    presence_penalty: float = 0.2,
    top_p: float = 1,
    stop_words: Optional[List[str]] = None,
    max_tokens: Optional[int] = None,
    api_key: Optional[str] = None,
) -> Tuple[str, int]:
    """生成聊天回复内容"""

    if __openai_version <= "0.28.0":
        openai.api_key = api_key

        res = openai.ChatCompletion.create(  # type: ignore
            model=config.CHAT_MODEL,
            messages=messages,
            temperature=temperature,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            max_tokens=max_tokens,
            stop=stop_words,
        )
        logger.debug(f"Chat response: {res}")

        output = res.choices[0].message.content  # type: ignore
        token_consumption = res.usage.total_tokens  # type: ignore
        logger.info(f"请求消耗: {token_consumption} tokens")
        assert output, "Chat response is empty"
        return output, token_consumption

    client = AsyncOpenAI(
        api_key=api_key,
        base_url=config.OPENAI_BASE_URL,
        http_client=(
            httpx.AsyncClient(
                proxy=config.OPENAI_PROXY,
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
        max_tokens=max_tokens,
        stop=stop_words,
    )

    output = res.choices[0].message.content
    token_consumption = res.usage.total_tokens if res.usage else -1
    logger.info(f"请求消耗: {token_consumption} tokens")
    assert output, "Chat response is empty"
    return output, token_consumption
