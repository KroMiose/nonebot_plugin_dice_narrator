import random
import re

from nonebot import logger
from nonebot.matcher import Matcher

from nonebot_plugin_dice_narrator.config import config
from nonebot_plugin_dice_narrator.utils.common import read_yml_str2data
from nonebot_plugin_dice_narrator.utils.openai_funcs import gen_chat_response_text

SYSTEM_PROMPT = f"""
你是一个游戏DM，接下来用户会向你描述一项玩家任务，并进行一次掷骰，请根据你的对这个任务的判断，给出对于这个任务**相对客观**的执行难度(1~{config.DIFFICULTY_DICE_MAX})，需要尽可能详细地说明具体的四种掷骰结果对应的**事件描述**:

成功(success): 掷骰结果不小于任务难度
失败(failure): 掷骰结果小于任务难度
大成功(completed_success): 掷骰结果为{config.DIFFICULTY_DICE_MAX}
大失败(critical_failure): 掷骰结果为1且小于任务难度

示例如下: 

检定任务: 
逃离触手怪的束缚

你的响应内容格式如下:

```yaml
difficulty: {int(config.DIFFICULTY_DICE_MAX*0.75)}
success: 你奋力抵挡住了触手怪的袭击，成功拉开了距离。虽然你没有完全逃脱，但至少还活着，可以继续寻找其他出路。
failure: 在昏暗的洞穴中，触手怪的柔滑触手紧紧缠绕着你的身体。你感到了一种异样的窒息与兴奋交织在一起，而队友们只能眼睁睁地看着。任务虽然失败了，但你似乎成为了怪物欲望的俘虏。
completed_success: 你在在昏暗潮湿的洞穴里，紧张地寻找着逃生的路线。触手怪似乎已经察觉到你的气息，在不远处窥视着。你小心翼翼地移动着，每一步都如履薄冰。终于，在一个转角处，你发现了一条隐蔽的小径。没有时间犹豫，你快速地沿着小径前进，只听见身后触手怪愤怒的咆哮声渐行渐远。当你走出洞穴，深深地吸了口新鲜空气时，心中充满了胜利的喜悦和对自由的向往。
critical_failure: 在昏暗的洞穴中，触手怪的柔滑触手已经缠绕住了你的双腿和手臂。你努力挣扎着想要逃脱，但它们就像有生命一样紧紧地束缚着你，阻止你任何逃跑的可能。队友们似乎被其他事情分散了注意力，没有人能来救你。就在这时，触手开始轻轻地摩擦起你的皮肤，你感到自己被未知快感淹没。
```

如果玩家给出的任务是一个**行为**，"成功"的定义是该行为能否完成以及完成的效果如何；如果是**事件**，"成功"的定义是**该事件发生**了，以及事件发生的影响，并且其发生的概率影响对该事件难度的定义。(即如果该事件越难发生，你应该设置越高的难度，并且在其**success**和**completed_success**中描述发生的影响)
特别地，如果玩家给出的任务描述不明确，你可以适当地任意假设其发生的背景
"""

USER_PROMPT = """
检定任务:
{question}
"""

RESPONSE_STRUCT = """
检定任务: {question}
目标难度: {difficulty}/{difficulty_max}
掷骰结果: {dice_num} [{status}]
========
{event_content}
"""


async def run_narrator(question: str, matcher: Matcher):
    assert question, "question is empty"
    try:
        res, _ = await gen_chat_response_text(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT.strip()},
                {
                    "role": "user",
                    "content": USER_PROMPT.strip().format(question=question),
                },
            ],
        )
    except Exception as e:
        logger.error(f"与 OpenAI 通信发生错误: {e}")
        await matcher.finish("哎呀！与 OpenAI 通信发生错误，请稍后再试 (┬┬﹏┬┬)")

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
    elif dice_num == 1 and dice_num < int(res_data["difficulty"]):
        res_key, status = "critical_failure", "大失败"
    elif dice_num < int(res_data["difficulty"]):
        res_key, status = "failure", "失败"
    else:
        res_key, status = "success", "成功"

    logger.debug(f"检定: `{question}` | 原始返回: {res}")

    try:
        await matcher.finish(
            RESPONSE_STRUCT.strip().format(
                question=question,
                # thought=res_data["thought"],
                difficulty=int(res_data["difficulty"]),
                difficulty_max=config.DIFFICULTY_DICE_MAX,
                dice_num=dice_num,
                event_content=res_data[res_key],
                status=status,
            ),
        )
    except KeyError:
        await matcher.finish("检定失败 ＞﹏＜ 请检查任务描述是否合理！")
