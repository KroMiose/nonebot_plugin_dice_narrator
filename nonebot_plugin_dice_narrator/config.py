from pathlib import Path
from typing import List, Optional

import miose_toolkit_common.config
from miose_toolkit_common.config import Config, Env

miose_toolkit_common.config._config_root = Path(  # noqa: SLF001
    "./configs/nonebot_plugin_dice_narrator",
)


class PluginConfig(Config):
    OPENAI_API_KEYS: List[str] = []
    OPENAI_BASE_URL: Optional[str] = None
    OPENAI_PROXY: Optional[str] = None
    CHAT_MODEL: str = "gpt-3.5-turbo"

    DIFFICULTY_DICE_MAX: int = 20

    FORBIDDEN_USERS: List[str] = []
    FORBIDDEN_WORDS: List[str] = []

    FILTER_WORDS: List[str] = []
    FILTER_PLACEHOLDER: str = "[数据删除]"


config = PluginConfig().load_config(create_if_not_exists=True)
config.dump_config(envs=[Env.Default.value])
