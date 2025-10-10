import re
import json

import aiofiles
from nonebot import require
from nonebot.permission import SUPERUSER
from nonebot.plugin import PluginMetadata, inherit_supported_adapters

require("nonebot_plugin_alconna")
require("nonebot_plugin_localstore")
import nonebot_plugin_localstore as store
from nonebot_plugin_alconna.uniseg import UniMessage
from nonebot_plugin_alconna import Option, Args, Alconna, CommandMeta, on_alconna

from .config import Config
from .utils import fetch_daily_bing_data, fetch_randomly_daily_bing_data

__plugin_meta__ = PluginMetadata(
    name="每日必应壁纸",
    description="定时发送必应每日提供的壁纸",
    usage="/daily_bing 状态; /daily_bing 关闭; /daily_bing 开启 13:30",
    type="application",
    config=Config,
    homepage="https://github.com/lyqgzbl/nonebot-plugin-daily-bing",
    supported_adapters=inherit_supported_adapters("nonebot_plugin_alconna"),
    extra={
        "author": "lyqgzbl <admin@lyqgzbl.com>",
        "version": "0.1.0",
    },
)


daily_bing_cache_json = store.get_plugin_cache_file("daily_bing.json")


def is_valid_time_format(time_str: str) -> bool:
    if not re.match(r"^\d{1,2}:\d{2}$", time_str):
        return False
    try:
        hour, minute = map(int, time_str.split(":"))
        return 0 <= hour <= 23 and 0 <= minute <= 59
    except ValueError:
        return False


daily_bing_command = on_alconna(
    Alconna(
        "今日必应壁纸",
        meta=CommandMeta(
            compact=True,
            description="获取今日必应壁纸",
            usage="/今日必应壁纸",
            example="/今日必应壁纸",
        ),
    ),
    use_cmd_start=True,
    priority=10,
    block=True,
)


randomly_daily_bing_command = on_alconna(
    Alconna(
        "随机必应壁纸",
        meta=CommandMeta(
            compact=True,
            description="获取随机必应壁纸",
            example="/随机必应壁纸",
        ),
    ),
    use_cmd_start=True,
    priority=10,
    block=True,
)


daily_bing_setting = on_alconna(
    Alconna(
        "daily_bing",
        Option("状态|status"),
        Option("关闭|stop"),
        Option("开启|start", Args["send_time?#每日壁纸发送时间", str]),
        meta=CommandMeta(
            compact=True,
            description="必应每日壁纸设置",
            usage=__plugin_meta__.usage,
            example=(
                "/daily_bing 状态\n"
                "/daily_bing 关闭\n"
                "/daily_bing 开启 13:30"
            ),
        ),
    ),
    aliases={"每日必应"},
    permission=SUPERUSER,
    use_cmd_start=True,
    priority=10,
    block=True,
)


@daily_bing_command.handle()
async def handle_daily_bing():
    if not daily_bing_cache_json.exists():
        success = await fetch_daily_bing_data()
        if not success:
            await daily_bing_command.finish("获取今日必应壁纸失败请稍后再试")
    async with aiofiles.open(str(daily_bing_cache_json), encoding="utf-8") as f:
        content = await f.read()
        data = json.loads(content)
    await UniMessage.text(
        f"今日必应壁纸\n{data.get('imgtitle','今日必应壁纸')}"
    ).image(
        url=data.get("imgurl")
    ).send()


@randomly_daily_bing_command.handle()
async def handle_andomly_daily_bing():
    data = await fetch_randomly_daily_bing_data()
    if not data:
        await randomly_daily_bing_command.finish("获取随机必应壁纸失败请稍后再试")
    await UniMessage.text(
        "随机必应壁纸"
    ).image(
        raw=data
    ).send()
