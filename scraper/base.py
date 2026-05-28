# -*- coding: utf-8 -*-
"""
爬虫基础模块
提供所有爬虫的公共能力：请求伪装、重试、日志、去重
"""

import time
import random
import logging
import hashlib
from datetime import datetime, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup

import config

# ==================== 日志配置 ====================
def get_logger(name: str) -> logging.Logger:
    """创建带时间戳的文件日志"""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    log_file = Path(config.LOG_DIR) / f"{name}_{datetime.now():%Y%m%d}.log"
    handler = logging.FileHandler(log_file, encoding="utf-8")
    handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    logger.addHandler(handler)
    # 同时也输出到控制台
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter("[%(name)s] %(message)s"))
    logger.addHandler(console)
    return logger

logger = get_logger("base")


class BaseScraper:
    """所有爬虫的基类"""

    def __init__(self, source_config: dict):
        self.name = source_config["name"]
        self.url = source_config.get("url", "")
        self.notice_url = source_config.get("notice_url", self.url)
        self.category = source_config.get("category", "其他")
        self.enabled = source_config.get("enabled", True)
        self.source_type = source_config.get("type", "web")

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": config.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
        })
        self.logger = get_logger(f"scraper.{self.name}")

    def fetch(self, url: str = None, encoding: str = "utf-8") -> str | None:
        """
        请求页面HTML
        返回 HTML 文本，失败返回 None
        """
        url = url or self.notice_url
        last_error = None
        for attempt in range(1, config.MAX_RETRIES + 1):
            try:
                self.logger.info(f"请求 [{attempt}/{config.MAX_RETRIES}]: {url}")
                resp = self.session.get(url, timeout=config.REQUEST_TIMEOUT)
                resp.raise_for_status()
                # 自动检测编码
                if resp.apparent_encoding:
                    resp.encoding = resp.apparent_encoding
                elif encoding:
                    resp.encoding = encoding
                # 请求成功后随机等待，避免频率过高
                wait = config.REQUEST_INTERVAL + random.uniform(0, 2)
                time.sleep(wait)
                return resp.text
            except requests.RequestException as e:
                last_error = e
                self.logger.warning(f"请求失败 [{attempt}/{config.MAX_RETRIES}]: {e}")
                if attempt < config.MAX_RETRIES:
                    time.sleep(2 ** attempt)  # 指数退避: 2s, 4s, 8s

        self.logger.error(f"全部重试失败: {last_error}")
        return None

    def parse(self, html: str) -> list[dict]:
        """
        解析HTML，提取通知列表。
        子类需要重写此方法。
        返回格式: [{"title": "xxx", "url": "xxx", "date": "2026-05-27", "summary": "xxx"}, ...]
        """
        raise NotImplementedError("子类必须实现 parse() 方法")

    def run(self) -> list[dict]:
        """
        完整执行流程：请求 → 解析 → 返回
        """
        if not self.enabled:
            self.logger.info(f"[{self.name}] 已禁用，跳过")
            return []

        self.logger.info(f"[{self.name}] 开始抓取...")
        html = self.fetch()
        if html is None:
            return []

        try:
            notices = self.parse(html)
            # 给每条通知加上来源信息
            for n in notices:
                n["source_name"] = self.name
                n["source_category"] = self.category
                n["source_type"] = self.source_type
            self.logger.info(f"[{self.name}] 抓取完成: {len(notices)} 条")
            return notices
        except Exception as e:
            self.logger.error(f"[{self.name}] 解析失败: {e}", exc_info=True)
            return []

    def make_absolute_url(self, relative_url: str, base_url: str = None) -> str:
        """将相对URL转换为绝对URL"""
        from urllib.parse import urljoin
        base = base_url or self.url
        return urljoin(base, relative_url)

    @staticmethod
    def generate_id(title: str, date_str: str, source_name: str) -> str:
        """生成通知唯一标识"""
        raw = f"{source_name}|{title}|{date_str}"
        return hashlib.md5(raw.encode("utf-8")).hexdigest()

    @staticmethod
    def clean_text(text: str) -> str:
        """清洗文本：去除多余空白和换行"""
        if not text:
            return ""
        return " ".join(text.split()).strip()

    @staticmethod
    def parse_date(date_str: str) -> str:
        """
        将各种日期格式统一为 YYYY-MM-DD
        支持: 2026-05-27, 2026/05/27, 05-27, 5月27日 等
        """
        if not date_str:
            return datetime.now().strftime("%Y-%m-%d")

        date_str = date_str.strip().replace("年", "-").replace("月", "-").replace("日", "").replace("/", "-")
        try:
            # 如果已经是完整日期
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass

        try:
            # 只有月-日，补上当前年份
            dt = datetime.strptime(date_str, "%m-%d")
            return f"{datetime.now().year}-{dt:%m-%d}"
        except ValueError:
            pass

        # 实在解析不了，返回原始字符串
        return date_str
