import re
import json

import aiofiles
from nonebot.log import logger
from nonebot.permission import SUPERUSER
from nonebot import require, get_plugin_config
from nonebot.plugin import PluginMetadata, inherit_supported_adapters

require("nonebot_plugin_argot")
require("nonebot_plugin_alconna")
require("nonebot_plugin_localstore")
require("nonebot_plugin_htmlrender")
require("nonebot_plugin_apscheduler")
from nonebot_plugin_argot import Text
import nonebot_plugin_localstore as store
from nonebot_plugin_apscheduler import scheduler
from nonebot_plugin_argot.extension import ArgotExtension
from nonebot_plugin_alconna.uniseg import UniMessage, MsgTarget, Target
from nonebot_plugin_alconna import Option, Args, Alconna, CommandMeta, on_alconna, Match

from .config import Config
from .infopuuzzle import generate_daily_bing_image
from .utils import (
    fetch_daily_bing_data,
    fetch_randomly_daily_bing_data,
    remove_daily_bing_task,
    schedule_daily_bing_task,
    generate_job_id,
)

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
        "version": "1.0.0",
    },
)

plugin_config = get_plugin_config(Config)
daily_bing_hd_image = plugin_config.daily_bing_hd_image
default_time = plugin_config.daily_bing_default_send_time
daily_bing_infopuzzle = plugin_config.daily_bing_infopuzzle
daily_bing_cache_json = store.get_plugin_cache_file("daily_bing.json")
task_config_file = store.get_plugin_data_file("daily_bing_task_config.json")


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
    extensions=[ArgotExtension()],

)


randomly_daily_bing_command = on_alconna(
    Alconna(
        "随机必应壁纸",
        meta=CommandMeta(
            compact=True,
            description="获取随机必应壁纸",
            usage="/随机必应壁纸",
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
    explanation = data.get("imgdetail", "")
    explanation = explanation.replace("<p>", "").replace("</p>", "")
    if daily_bing_hd_image:
        img_url = data.get("imgurl_d") or data.get("imgurl")
    if not daily_bing_infopuzzle:
        await UniMessage.text(
            f"{data.get('imgtitle','今日必应壁纸')}"
        ).image(
            url=img_url
        ).send(
            reply_to=True,
            argot={
                "name": "explanation",
                "segment": Text(explanation),
                "command": "简介",
                "expired_at": 360,
            },
        )
    else:
        img_bytes = await generate_daily_bing_image()
        if not img_bytes:
            await daily_bing_command.finish("生成今日必应壁纸图片失败请稍后再试")
        await UniMessage.image(
            raw=img_bytes
        ).send(
            reply_to=True,
        )


@randomly_daily_bing_command.handle()
async def handle_andomly_daily_bing():
    data = await fetch_randomly_daily_bing_data()
    if not data:
        await randomly_daily_bing_command.finish("获取随机必应壁纸失败请稍后再试")
    await UniMessage.text(
        "随机必应壁纸"
    ).image(
        raw=data
    ).send(
        reply_to=True,
    )


@daily_bing_setting.assign("status")
async def daily_bing_status(event, target: MsgTarget):
    if not task_config_file.exists():
        await daily_bing_setting.finish("今日必应壁纸定时任务未开启")
    try:
        async with aiofiles.open(task_config_file, encoding="utf-8") as f:
            content = await f.read()
            config = json.loads(content)
        tasks = config.get("tasks") or []
    except Exception as e:
        await daily_bing_setting.finish(f"加载任务配置时发生错误：{e}")
    if not tasks:
        await daily_bing_setting.finish("今日必应壁纸定时任务未开启")
    current_target = target
    for task in tasks:
        target_data = task["target"]
        data_target = Target.load(target_data)
        if data_target == current_target:
            job_id = generate_job_id(current_target)
            job = scheduler.get_job(job_id)
            if job:
                next_run = (
                    job.next_run_time.strftime("%Y-%m-%d %H:%M:%S")
                    if job.next_run_time else "未知"
                )
                await daily_bing_setting.finish(
                    f"今日必应壁纸定时任务已开启 | 下次发送时间: {next_run}"
                )
            else:
                await daily_bing_setting.finish("今日必应壁纸定时任务未开启")
    await daily_bing_setting.finish("今日必应壁纸定时任务未开启")


@daily_bing_setting.assign("stop")
async def daily_bing_stop(target: MsgTarget):
    await remove_daily_bing_task(target)
    await daily_bing_setting.finish("已关闭今日必应壁纸定时任务")


@daily_bing_setting.assign("start")
async def daily_bing_start(send_time: Match[str], target: MsgTarget):
    if send_time.available:
        time = send_time.result
        if not is_valid_time_format(time):
            await daily_bing_setting.send("时间格式不正确,请使用 HH:MM 格式")
        try:
            await schedule_daily_bing_task(time, target)
            await daily_bing_setting.send(
                f"已开启今日必应壁纸定时任务,发送时间为 {time}"
            )
        except Exception as e:
            logger.error(f"设置今日必应壁纸定时任务时发生错误:{e}")
            await daily_bing_setting.finish("设置今日必应壁纸定时任务时发生错误")
    else:
        await schedule_daily_bing_task(default_time, target)
        await daily_bing_setting.finish(
            f"已开启今日必应壁纸定时任务,默认发送时间为 {default_time}"
        )
