<!-- markdownlint-disable MD033 MD036 MD041 -->

<div align="center">

<a href="https://v2.nonebot.dev/store">
  <img src="https://raw.githubusercontent.com/A-kirami/nonebot-plugin-template/resources/nbp_logo.png" width="180" height="180" alt="NoneBotPluginLogo">
</a>

<p>
  <img src="https://raw.githubusercontent.com/lgc-NB2Dev/readme/main/template/plugin.svg" alt="NoneBotPluginText">
</p>

# nonebot-plugin-daily-bing

_✨ 每日必应壁纸 ✨_

![License](https://img.shields.io/pypi/l/nonebot-plugin-daily-bing)
![PyPI](https://img.shields.io/pypi/v/nonebot-plugin-daily-bing.svg)
![Python](https://img.shields.io/badge/python-3.10+-blue.svg)  
[![NoneBot Registry](https://img.shields.io/endpoint?url=https%3A%2F%2Fnbbdg.lgc2333.top%2Fplugin%2Fnonebot-plugin-daily-bing)](https://registry.nonebot.dev/plugin/nonebot-plugin-daily-bing:nonebot_plugin_daily-bing)
[![Supported Adapters](https://img.shields.io/endpoint?url=https%3A%2F%2Fnbbdg.lgc2333.top%2Fplugin-adapters%2Fnonebot-plugin-alconna)](https://registry.nonebot.dev/plugin/nonebot-plugin-alconna:nonebot_plugin_alconna)

</div>


## 安装
使用nb-cli [推荐]
```shell
nb plugin install nonebot-plugin-daily-bing
```
使用pip
```shell
pip install nonebot-plugin-daily-bing
```

## 使用
命令需要加 [NoneBot 命令前缀](https://nonebot.dev/docs/appendices/config#command-start-和-command-separator) (默认为`/`)  
命令需要用户为 [SuperUsers](https://nonebot.dev/docs/appendices/config#superusers)  
使用命令`daily_bing`/`每日必应`触发插件  
命令选项`状态` 查询定时任务状态  
命令选项`关闭` 关闭定时任务  
命令选项`开启` 开启定时任务  

[以下命令无需用户为[SuperUsers](https://nonebot.dev/docs/appendices/config#superusers)]  
使用命令`今日必应壁纸`获取今日必应壁纸  
使用命令`随机必应壁纸`随机获得必应壁纸  


## 配置项

配置方式：直接在 NoneBot 全局配置文件中添加以下配置项即可

### daily_bing_default_send_time [选填]

- 类型：`str`
- 默认值：`13:00`
- 说明：每日必应壁纸的默认发送时间

### daily_bing_hd_image [选填]

- 类型：`bool`
- 默认值：`False`
- 说明：是否启用高清必应壁纸

### daily_bing_infopuzzle [选填]

- 类型：`bool`
- 默认值：`False`
- 说明：是否启用必应壁纸拼图

### daily_bing_infopuzzle_dark_mode [选填]

- 类型：`bool`
- 默认值：`False`
- 说明：是否使用暗色模式的必应壁纸拼图