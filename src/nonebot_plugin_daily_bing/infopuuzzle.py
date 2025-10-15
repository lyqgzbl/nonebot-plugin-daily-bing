import json
from pathlib import Path

import aiofiles
from nonebot.log import logger
from nonebot import get_plugin_config
import nonebot_plugin_localstore as store
from nonebot_plugin_htmlrender import md_to_pic

from .config import Config

plugin_config = get_plugin_config(Config)
daily_bing_hd_image = plugin_config.daily_bing_hd_image
daily_bing_cache_json = store.get_plugin_cache_file("daily_bing.json")
daily_bing_infopuzzle_dark_mode = plugin_config.daily_bing_infopuzzle_dark_mode


async def daily_bing_josn_to_md(daily_bing_json) -> str:
    title = daily_bing_json["imgtitle"]
    explanation = daily_bing_json["imgdetail"]
    if daily_bing_hd_image:
        url = daily_bing_json["imgurl_d"] or daily_bing_json["imgurl"]
    else:
        url = daily_bing_json["imgurl"]
    copyright = daily_bing_json.get("imgcopyright", "无")
    date = daily_bing_json["date"]
    return f"""<div class="container">
    <h1>今日必应壁纸</h1>
    <h2>{title}</h2>

    <div class="image-container">
        <img src="{url}" alt="Bing Daily Image">
    </div>

    <p class="explanation">{explanation}</p>

    <div class="info">
        <p><strong>版权：</strong> {copyright}</p>
        <p><strong>日期：</strong> {date}</p>
    </div>
</div>
"""


async def generate_daily_bing_image() -> bytes | None:
    try:
        if not daily_bing_cache_json.exists():
            return None
        else:
            async with aiofiles.open(str(daily_bing_cache_json), encoding="utf-8") as f:
                content = await f.read()
                data = json.loads(content)
        md_content = await daily_bing_josn_to_md(data)
        css_file = (
                Path(__file__).parent
                / "css"
                / ("dark.css" if daily_bing_infopuzzle_dark_mode else "light.css")
            )
        img_bytes = await md_to_pic(md_content, width=600, css_path=str(css_file))
        return img_bytes
    except Exception as e:
        logger.error(f"生成今日必应壁纸图片时发生错误：{e}")
        return None
