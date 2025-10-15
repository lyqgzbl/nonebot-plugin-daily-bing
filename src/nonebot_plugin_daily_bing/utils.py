import json
import hashlib
import asyncio
from datetime import timedelta

import httpx
import aiofiles
from nonebot.log import logger
from nonebot import get_plugin_config
import nonebot_plugin_localstore as store
from nonebot_plugin_apscheduler import scheduler
from nonebot import get_driver, get_bot, get_bots
from nonebot_plugin_argot import Text, add_argot, get_message_id
from nonebot_plugin_alconna.uniseg import MsgTarget, Target, UniMessage

from .config import Config
from .infopuuzzle import generate_daily_bing_image


driver = get_driver()
config_lock = asyncio.Lock()
plugin_config = get_plugin_config(Config)
hd_image = plugin_config.daily_bing_hd_image
DAILY_BING_API_URL = "https://bing.ee123.net/img/"
daily_bing_infopuzzle = plugin_config.daily_bing_infopuzzle
RANDOMLY_DAILY_BING_API_URL = "https://bing.ee123.net/img/rand"
daily_bing_cache_json = store.get_plugin_cache_file("daily_bing.json")
task_config_file = store.get_plugin_data_file("daily_bing_task_config.json")


@driver.on_startup
async def init_daily_bing_tasks():
    await restore_daily_bing_tasks()


async def fetch_daily_bing_data() -> bool:
    try:
        async with httpx.AsyncClient(timeout = httpx.Timeout(10.0)) as client:
            response = await client.get(
                DAILY_BING_API_URL,
                params={"imgtype": "jpg", "type": "json"},
            )
            response.raise_for_status()
            content = await response.aread()
            data = json.loads(content.decode())
            async with aiofiles.open(daily_bing_cache_json, "w", encoding="utf-8") as f:
                await f.write(json.dumps(data, indent=4, ensure_ascii=False))
            return True
    except httpx.RequestError as e:
        logger.error(f"网络请求错误: {e}")
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP 状态错误 {e.response.status_code}: {e.response.text}")
    except Exception as e:
        logger.error(f"处理数据或写文件时出错: {e}")
    return False


async def fetch_randomly_daily_bing_data() -> bytes | None:
    try:
        async with httpx.AsyncClient(timeout = httpx.Timeout(10.0)) as client:
            response = await client.get(
                RANDOMLY_DAILY_BING_API_URL,
                follow_redirects=True,
            )
            response.raise_for_status()
            content = await response.aread()
            return content
    except httpx.RequestError as e:
        logger.error(f"网络请求错误: {e}")
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP 状态错误 {e.response.status_code}: {e.response.text}")
    except Exception as e:
        logger.error(f"处理数据时出错: {e}")
    return None


def generate_job_id(target: MsgTarget) -> str:
    serialized_target = json.dumps(Target.dump(target), sort_keys=True)
    job_id = hashlib.md5(serialized_target.encode()).hexdigest()
    return f"send_daily_bind_task_{job_id}"


async def save_task_configs(tasks: list, locked: bool = False):
    async def _save():
        serialized_tasks = [
            {
                "send_time": task["send_time"],
                "target": Target.dump(task["target"]),
            }
            for task in tasks
        ]
        async with aiofiles.open(task_config_file, "w", encoding="utf-8") as f:
            await f.write(json.dumps(
                {"tasks": serialized_tasks},
                ensure_ascii=False,
                indent=4,
            ))
    try:
        if locked:
            await _save()
        else:
            async with config_lock:
                await _save()
    except Exception as e:
        logger.error(f"保存每日壁纸定时任务配置时发生错误：{e}")


async def remove_daily_bing_task(target: MsgTarget):
    job_id = generate_job_id(target)
    job = scheduler.get_job(job_id)
    if job:
        scheduler.remove_job(job_id)
        logger.info(f"已移除每日必应壁纸定时任务 (目标: {target})")
        async with config_lock:
            tasks = await load_task_configs(locked=True)
            tasks = [task for task in tasks if task["target"] != target]
            await save_task_configs(tasks, locked=True)
    else:
        logger.info(f"未找到每日必应壁纸定时任务 (目标: {target})")


async def load_task_configs(locked: bool = False) -> list[dict]:
    if not task_config_file.exists():
        return []
    async def _load():
        if not task_config_file.exists():
            return []
        async with aiofiles.open(task_config_file, encoding="utf-8") as f:
            content = await f.read()
        if not content.strip():
            return []
        config_data = json.loads(content)
        return [
            {"send_time": task["send_time"], "target": Target.load(task["target"])}
            for task in config_data.get("tasks", [])
        ]
    try:
        if locked:
            return await _load()
        async with config_lock:
            return await _load()
    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"加载或解析任务配置时发生错误：{e}，将视为空配置。")
        return []
    except Exception as e:
        logger.error(f"加载每日壁纸定时任务配置时发生错误：{e}")
        return []


async def send_daily_bing(target: MsgTarget):
    logger.debug(f"主动发送目标: {target}")
    bots = get_bots()
    if target.self_id in bots:
        bot = get_bot(target.self_id)
    else:
        logger.warning("<yellow>未找到可用的机器人实例，此任务将被跳过</yellow>")
        return
    if not daily_bing_cache_json.exists():
        success = await fetch_daily_bing_data()
        if not success:
            await UniMessage.text("获取今日必应壁纸失败请稍后再试").send(
                target=target,
                bot=bot,
            )
            return
    async with aiofiles.open(str(daily_bing_cache_json), encoding="utf-8") as f:
        content = await f.read()
        data = json.loads(content)
        explanation = data.get("imgdetail", "")
        explanation = explanation.replace("<p>", "").replace("</p>", "")
        if hd_image:
            img_url = data.get("imgurl_d")
        else:
            img_url = data.get("imgurl")
    if not daily_bing_infopuzzle:
        message = await UniMessage.text(
            f"{data.get('imgtitle','今日必应壁纸')}"
        ).image(
            url=img_url
        ).send(
            target=target,
            bot=bot,
        )
        await add_argot(
            message_id=get_message_id(message) or "",
            name="explanation",
            command="简介",
            segment=Text(explanation),
            expired_at=timedelta(minutes=2),
        )
    else:
        img_bytes = await generate_daily_bing_image()
        if not img_bytes:
            await UniMessage.text("生成今日必应壁纸图片失败请稍后再试").send(
                target=target,
                bot=bot,
            )
            return
        await UniMessage.image(
            raw=img_bytes
        ).send(
            target=target,
            bot=bot,
        )


async def schedule_daily_bing_task(send_time: str, target: MsgTarget):
    try:
        hour, minute = map(int, send_time.split(":"))
        job_id = generate_job_id(target)
        scheduler.add_job(
            func=send_daily_bing,
            trigger="cron",
            args=[target],
            hour=hour,
            minute=minute,
            id=job_id,
            max_instances=1,
            replace_existing=True,
        )
        logger.info(
            "已成功设置必应每日壁纸定时任务,"
            f"发送时间为 {send_time} (目标: {target})"
        )
        async with config_lock:
            tasks = await load_task_configs(locked=True)
            tasks = [task for task in tasks if task["target"] != target]
            tasks.append({"send_time": send_time, "target": target})
            await save_task_configs(tasks, locked=True)
    except ValueError:
        logger.error(f"时间格式错误：{send_time}，请使用 HH:MM 格式")
        raise ValueError(f"时间格式错误：{send_time}")
    except Exception as e:
        logger.error(f"设置设置必应每日壁纸定时任务时发生错误：{e}")



async def restore_daily_bing_tasks():
    try:
        tasks = await load_task_configs()
        if tasks:
            for task in tasks:
                send_time = task.get("send_time")
                target = task.get("target")
                if send_time and target:
                    hour, minute = map(int, send_time.split(":"))
                    job_id = generate_job_id(target)
                    scheduler.add_job(
                        func=send_daily_bing,
                        trigger="cron",
                        args=[target],
                        hour=hour,
                        minute=minute,
                        id=job_id,
                        max_instances=1,
                        replace_existing=True,
                    )
            logger.info(f"已恢复 {len(tasks)} 个每日必应壁纸定时任务")
        else:
            logger.debug("没有找到任何每日必应壁纸定时任务配置")
    except Exception as e:
        logger.error(f"恢复每日必应壁纸定时任务时发生错误：{e}")


@scheduler.scheduled_job("cron", hour=0, minute=0, id="clear_daily_bing_cache")
async def clear_daily_bing_cache():
    if daily_bing_cache_json.exists():
        try:
            await asyncio.to_thread(daily_bing_cache_json.unlink)
            logger.info("已清除今日必应壁纸缓存")
        except Exception as e:
            logger.error(f"清除今日必应壁纸缓存时出错: {e}")
