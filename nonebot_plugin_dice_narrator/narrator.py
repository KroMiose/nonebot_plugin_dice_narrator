import random
import re

from nonebot.matcher import Matcher

from nonebot_plugin_dice_narrator.config import config
from nonebot_plugin_dice_narrator.utils.common import read_yml_str2data
from nonebot_plugin_dice_narrator.utils.openai_funcs import gen_chat_response_text

SYSTEM_PROMPT = f"""
你是一个游戏DM，接下来用户会向你描述一项玩家任务，并进行一次掷骰，请给出这个任务的执行难度(1~{config.DIFFICULTY_DICE_MAX})，需要说明具体的**玩家行为描述**、四种掷骰结果对应的**事件描述**：

大成功(completed_success)：掷骰结果为{config.DIFFICULTY_DICE_MAX}
成功(success)：掷骰结果不小于任务难度
失败(failure)：掷骰结果小于任务难度
大失败(critical_failure)：掷骰结果为1

示例如下：

检定任务：
逃离触手怪的束缚

你的响应内容格式如下:

```yaml
difficulty: {int(config.DIFFICULTY_DICE_MAX*0.75)}
completed_success: 你展现出了惊人的协作和勇气。巧妙地躲过了触手怪的攻击，找到了一个隐藏的通道，成功逃离了触手怪的魔爪。你喘着粗气，但胜利的喜悦填满了你的心。
success: 你奋力抵挡住了触手怪的袭击，成功拉开了距离。虽然你没有完全逃脱，但至少还活着，可以继续寻找其他出路。
failure: 触手怪的一只触手抓住了你，你被拖入了一个黑暗的洞穴。你感到窒息和恐惧，而队友们无能为力。任务失败，你们成为了怪物的俘虏。
critical_failure: 你踩到了一块松动的地板，发出了巨大的声响。触手怪立刻察觉到了你的位置，它的触手缠绕住你，将你提起，然后狠狠地摔在地上。你昏迷了过去，不再感知周围的世界。
```

特别地，如果玩家给出的任务描述不明确，你可以适当地任意假设其发生的背景
"""

USER_PROMPT = """
检定任务:
{question}
"""

RESPONSE_STRUCT = """
检定任务: {question}
目标难度: {difficulty}/{difficulty_max}
检定结果: {dice_num} [{status}]
======
{event_content}
"""


async def run_narrator(question: str, matcher: Matcher):
    assert question, "question is empty"
    res, _ = await gen_chat_response_text(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT.strip()},
            {"role": "user", "content": USER_PROMPT.strip().format(question=question)},
        ],
    )

    # 提取并解析 yaml
    try:
        content = re.findall(r"```yaml(.*)```", res, re.S)[0]
    except:
        content = res
    try:
        res_data = read_yml_str2data(content)
    except Exception:
        res_data = read_yml_str2data(content + "```")

    # 掷骰
    dice_num = random.randint(1, config.DIFFICULTY_DICE_MAX)
    if dice_num == config.DIFFICULTY_DICE_MAX:
        res_key, status = "completed_success", "大成功"
    elif dice_num == 1:
        res_key, status = "critical_failure", "大失败"
    elif dice_num < int(res_data["difficulty"]):
        res_key, status = "failure", "失败"
    else:
        res_key, status = "success", "成功"

    print(res_data)

    await matcher.finish(RESPONSE_STRUCT.strip().format(
        question=question,
        difficulty=int(res_data["difficulty"]),
        difficulty_max=config.DIFFICULTY_DICE_MAX,
        dice_num=dice_num,
        event_content=res_data[res_key],
        status=status,
    ))
