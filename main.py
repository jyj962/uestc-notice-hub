# -*- coding: utf-8 -*-
"""
电子科技大学通知聚合系统 - 主入口
用法: python main.py
启动后自动执行首次抓取，然后开启 Web 看板和定时任务
"""

import sys
import os
import threading

# 把项目根目录加入 path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from scraper.models import init_db
from scraper.base import logger
from scheduler import start_scheduler, run_once
from web.app import run_web


def main():
    print("""
╔══════════════════════════════════════════╗
║   电子科技大学通知聚合系统               ║
║   UESTC Notice Hub v1.0                  ║
╚══════════════════════════════════════════╝
    """)

    # 1. 初始化数据库
    logger.info("初始化数据库...")
    init_db()
    logger.info("数据库就绪")

    # PythonAnywhere 等托管环境：不启动后台定时任务，避免多进程冲突
    if os.environ.get("PA_MODE") == "1":
        logger.info("检测到 PA_MODE=1，跳过后台定时任务，仅启动 Web 服务")
        run_web()
        return

    # 2. 本地模式：立即执行一次抓取
    logger.info("首次抓取中，请稍候...")
    try:
        count = run_once()
        logger.info(f"首次抓取完成，共新增 {count} 条通知")
    except Exception as e:
        logger.error(f"首次抓取失败: {e}")

    # 3. 启动定时任务
    scheduler = start_scheduler()

    # 4. 启动 Web 服务
    logger.info(f"Web 看板启动中: http://{config.WEB_HOST}:{config.WEB_PORT}")
    print(f"""
✨ 系统已就绪！
   打开浏览器访问: http://{config.WEB_HOST}:{config.WEB_PORT}
   按 Ctrl+C 停止服务
""")
    try:
        run_web()
    except KeyboardInterrupt:
        logger.info("正在关闭...")
        scheduler.shutdown()
        logger.info("已停止")


if __name__ == "__main__":
    main()
