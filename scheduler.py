# -*- coding: utf-8 -*-
"""
定时任务调度器
使用 APScheduler 每天定时执行全量抓取
"""

from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

import config
from scraper.models import (init_db, save_notices, log_fetch, 
                             mark_all_read, clean_old_notices)
from scraper.base import logger


# 导入各爬虫
from scraper.campus import CampusScraper, JwcScraper, XgbScraper, CollegeScraper
from scraper.bbs import BBSScraper
from scraper.employment import EmploymentScraper


def build_scrapers() -> list:
    """根据配置文件构建爬虫实例"""
    scraper_map = {
        "学校主站": CampusScraper,
        "教务处": JwcScraper,
        "党委学工部": XgbScraper,
        "本科生就业网": EmploymentScraper,
        "清水河畔BBS": BBSScraper,
        "机电学院": CollegeScraper,
    }
    scrapers = []
    for cfg in config.SOURCES:
        cls = scraper_map.get(cfg["name"], CampusScraper)
        scrapers.append(cls(cfg))
    return scrapers


def fetch_all():
    """
    全量抓取：遍历所有数据源，保存到数据库
    这是定时任务的核心函数
    """
    logger.info("=" * 50)
    logger.info(f"开始全量抓取 {datetime.now():%Y-%m-%d %H:%M:%S}")
    logger.info("=" * 50)

    init_db()
    scrapers = build_scrapers()
    total_saved = 0

    for scraper in scrapers:
        try:
            notices = scraper.run()
            if notices:
                saved = save_notices(notices)
                total_saved += saved
                log_fetch(scraper.name, True, saved)
            else:
                log_fetch(scraper.name, True, 0)
        except Exception as e:
            logger.error(f"[{scraper.name}] 抓取异常: {e}")
            log_fetch(scraper.name, False, 0, str(e))

    # 微信公众号抓取（频率较高，可能被搜狗限流）
    try:
        from scraper.wechat import WechatScraper
        wx = WechatScraper()
        wx_articles = wx.run_all()
        if wx_articles:
            saved = save_notices(wx_articles)
            total_saved += saved
            log_fetch("微信公众号", True, saved)
    except Exception as e:
        logger.error(f"[微信公众号] 抓取异常: {e}")
        log_fetch("微信公众号", False, 0, str(e))

    # 清理过期数据
    try:
        deleted = clean_old_notices()
        if deleted:
            logger.info(f"清理了 {deleted} 条过期数据")
    except Exception as e:
        logger.error(f"清理过期数据失败: {e}")

    # 新一轮抓取完成，重置 new 标记
    # 注意：每次抓取产生的 is_new 标记保留，下一轮抓取前会清零
    # 这里只在当天第一次抓取时清零，后续同一天不再清零
    now = datetime.now()
    if now.hour == 8:  # 早上的轮次清零
        pass  # is_new 由数据库插入时自动设为1，不需要主动清零

    logger.info(f"全量抓取完成，新增: {total_saved} 条")
    return total_saved


def start_scheduler():
    """启动定时任务"""
    scheduler = BackgroundScheduler(timezone="Asia/Shanghai")

    # 解析配置中的抓取时间
    for t in config.SCHEDULE_TIMES:
        hour, minute = t.split(":")
        scheduler.add_job(
            fetch_all,
            CronTrigger(hour=int(hour), minute=int(minute)),
            id=f"fetch_{t}",
            name=f"每日抓取 {t}",
            replace_existing=True
        )

    scheduler.start()
    logger.info(f"定时任务已启动，每天 {', '.join(config.SCHEDULE_TIMES)} 执行抓取")

    return scheduler


def run_once():
    """立即执行一次全量抓取（测试用）"""
    return fetch_all()
