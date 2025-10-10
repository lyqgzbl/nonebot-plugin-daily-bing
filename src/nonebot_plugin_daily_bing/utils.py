import json

import httpx
import aiofiles
from nonebot.log import logger
import nonebot_plugin_localstore as store

DAILY_BING_API_URL = "https://bing.ee123.net/img/"
RANDOMLY_DAILY_BING_API_URL = "https://bing.ee123.net/img/rand"
daily_bing_cache_json = store.get_plugin_cache_file("daily_bing.json")
task_config_file = store.get_plugin_data_file("daily_bing_task_config.json")


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
