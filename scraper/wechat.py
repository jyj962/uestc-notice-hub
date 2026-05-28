# -*- coding: utf-8 -*-
"""
微信公众号文章抓取
通过搜狗微信搜索接口获取公众号最新文章
"""

import time
import random
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from .base import BaseScraper, logger
import config


class WechatScraper:
    """
    微信公众号文章抓取器
    使用搜狗微信搜索接口 (weixin.sogou.com)
    注意：搜狗可能反爬，此模块需要酌情使用
    """

    SOGOU_URL = "https://weixin.sogou.com/weixin"
    SOGOU_ARTICLE_URL = "https://weixin.sogou.com/weixin"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": config.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Accept-Encoding": "gzip, deflate",
        })

    def search_account(self, account_name: str, max_articles: int = 10) -> list[dict]:
        """
        搜索指定公众号的最新文章
        返回: [{"title": "xxx", "url": "xxx", "date": "2026-05-27", "summary": "xxx"}, ...]
        """
        articles = []
        try:
            params = {
                "type": "2",        # 搜索文章
                "query": account_name,
                "ie": "utf8",
            }
            resp = self.session.get(self.SOGOU_ARTICLE_URL, params=params, timeout=config.REQUEST_TIMEOUT)
            resp.raise_for_status()

            soup = BeautifulSoup(resp.text, "lxml")

            # 搜狗微信搜索结果页结构
            items = soup.select("ul.news-list2 li") or soup.select("div.news-box li")

            for item in items[:max_articles]:
                link = item.find("a")
                if not link:
                    continue

                title = link.get_text(strip=True)
                url = link.get("href", "")
                if not title or not url:
                    continue

                # 提取摘要
                summary_el = item.find("p", class_="txt-info") or item.find("p")
                summary = summary_el.get_text(strip=True)[:200] if summary_el else ""

                # 提取日期
                date_str = ""
                date_el = item.find(class_=re.compile(r"date|time|s2"))
                if date_el:
                    date_str = date_el.get_text(strip=True)
                    m = re.search(r"(\d{4}[-/年]\d{1,2}[-/月]\d{1,2})", date_str)
                    if m:
                        date_str = m.group(1).replace("年", "-").replace("月", "-").replace("日", "")

                articles.append({
                    "title": title,
                    "date": self._parse_date(date_str),
                    "source_url": url,
                    "summary": summary,
                })

            time.sleep(config.REQUEST_INTERVAL + random.uniform(0, 2))
        except Exception as e:
            logger.warning(f"搜狗微信搜索 [{account_name}] 失败: {e}")

        return articles

    def run_all(self) -> list[dict]:
        """抓取所有公众号的文章"""
        all_articles = []
        for i, account in enumerate(config.WECHAT_ACCOUNTS):
            logger.info(f"[微信] 搜索公众号 [{account}] ({i+1}/{len(config.WECHAT_ACCOUNTS)})")
            articles = self.search_account(account)
            for a in articles:
                a["source_name"] = f"公众号·{account}"
                a["source_category"] = "其他"
                a["source_type"] = "wechat"
                a["id"] = f"wechat|{account}|{a.get('title','')}|{a.get('date','')}"
            all_articles.extend(articles)
            # 公众号之间间隔久一点，避免被搜狗封IP
            if i < len(config.WECHAT_ACCOUNTS) - 1:
                time.sleep(3 + random.uniform(0, 3))

        logger.info(f"[微信] 共抓取 {len(all_articles)} 篇文章")
        return all_articles

    @staticmethod
    def _parse_date(date_str: str) -> str:
        """解析日期"""
        if not date_str:
            return datetime.now().strftime("%Y-%m-%d")
        date_str = date_str.strip().replace("年", "-").replace("月", "-").replace("日", "")
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d")
        except ValueError:
            return datetime.now().strftime("%Y-%m-%d")
