# -*- coding: utf-8 -*-
"""
学校主站、教务处、学工部、机电学院等通用爬虫
这些网站结构类似，使用统一的解析策略，再用各站CSS选择器微调
"""

import re
from datetime import datetime

from bs4 import BeautifulSoup

from .base import BaseScraper, logger


class CampusScraper(BaseScraper):
    """学校主站通知公告爬虫"""

    def parse(self, html: str) -> list[dict]:
        soup = BeautifulSoup(html, "lxml")
        notices = []

        # 策略1：寻找通知列表（常见模式：ul/div > li > a）
        selectors = [
            "div.news-list li",           # 常见列表
            "div.notice-list li",
            "ul.list-box li",
            "div.main-con ul li a",       # 通用结构
            "div.content ul li",
            ".news-con ul li",
            "table tr td a",              # 表格型
        ]

        items = []
        for sel in selectors:
            items = soup.select(sel)
            if items:
                break

        # 如果上面的选择器都没找到，尝试更宽泛的匹配
        if not items:
            # 找所有带链接的列表项
            items = soup.find_all("a", href=re.compile(r"(info|news|notice|content|article)"))
            items = [a.parent for a in items if a.parent.name in ("li", "div", "td")]

        for item in items[:30]:  # 限制前30条
            link = item.find("a") if item.name != "a" else item
            if not link or not link.get("href"):
                continue

            title = self.clean_text(link.get_text())
            if not title or len(title) < 4:
                continue

            # 提取日期
            date_str = ""
            date_el = item.find(class_=re.compile(r"date|time|day"))
            if not date_el:
                date_el = item.find("span")
            if date_el:
                date_str = self.clean_text(date_el.get_text())
                # 尝试匹配日期格式
                m = re.search(r"(\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2})", date_str)
                if m:
                    date_str = m.group(1)

            url = self.make_absolute_url(link["href"])

            notices.append({
                "id": self.generate_id(title, date_str, self.name),
                "title": title,
                "date": self.parse_date(date_str),
                "source_url": url,
                "summary": "",
            })

        return notices


class JwcScraper(BaseScraper):
    """教务处爬虫 — 适配现代高校CMS系统"""

    def parse(self, html: str) -> list[dict]:
        soup = BeautifulSoup(html, "lxml")
        notices = []

        # 不限制href格式，接受所有有效链接
        links = soup.find_all("a", href=True)
        seen_titles = set()

        for a in links:
            href = a.get("href", "").strip()
            # 跳过无效链接
            if not href or href.startswith("#") or href.startswith("javascript"):
                continue

            title = self.clean_text(a.get_text())
            if not title or len(title) < 4:
                continue
            if title in seen_titles:
                continue
            seen_titles.add(title)

            url = self.make_absolute_url(href)

            # 在父元素中找日期（向上遍历最多5层）
            date_str = ""
            parent = a.parent
            for _ in range(5):
                if parent:
                    text = parent.get_text()
                    # 支持多种日期格式：2026-05-27, 05-27, 2026/05/27, 2026年5月27日
                    m = re.search(r"(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}|\d{1,2}[-/月]\d{1,2})", text)
                    if m:
                        date_str = m.group(1)
                        break
                    parent = parent.parent

            notices.append({
                "id": self.generate_id(title, date_str, self.name),
                "title": title,
                "date": self.parse_date(date_str),
                "source_url": url,
                "summary": "",
            })

            if len(notices) >= 50:
                break

        return notices


class XgbScraper(BaseScraper):
    """学工部爬虫 — 过滤导航菜单，只保留真正的通知"""

    # 需要过滤的导航词
    NAV_KEYWORDS = {
        "首页", "更多", "详情", "返回", "关闭", "查看",
        "资助育人", "学生资助", "毕业迎新", "劳动教育",
        "法治教育", "日常管理", "思想教育", "学风建设",
        "队伍建设", "心理健康", "国防教育", "学生事务",
        "新闻动态", "通知公告", "规章制度", "下载中心",
        "关于我们", "联系我们", "快速链接", "相关链接",
        "友情链接", "学校首页", "部门首页",
    }

    def parse(self, html: str) -> list[dict]:
        soup = BeautifulSoup(html, "lxml")
        notices = []

        # 优先找通知列表区域
        list_area = soup.select_one("div.notice-list, ul.news-list, div.news-con, div.main-con")
        search_root = list_area if list_area else soup

        # 遍历所有a标签，按文本长度和内容过滤
        links = search_root.find_all("a", href=True)
        seen_titles = set()

        for a in links:
            href = a.get("href", "").strip()
            if not href or href.startswith("#") or href.startswith("javascript"):
                continue

            title = self.clean_text(a.get_text())
            # 过滤：太短、纯导航词、含"更多"等
            if not title or len(title) < 6:
                continue
            if title in self.NAV_KEYWORDS or any(kw in title for kw in ["更多>>", "查看详情"]):
                continue
            if title in seen_titles:
                continue
            seen_titles.add(title)

            url = self.make_absolute_url(href)

            # 提取日期
            date_str = ""
            parent = a.parent
            for _ in range(5):
                if parent:
                    text = parent.get_text()
                    m = re.search(r"(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}|\d{1,2}[-/月]\d{1,2})", text)
                    if m:
                        date_str = m.group(1)
                        break
                    parent = parent.parent

            notices.append({
                "id": self.generate_id(title, date_str, self.name),
                "title": title,
                "date": self.parse_date(date_str),
                "source_url": url,
                "summary": "",
            })

            if len(notices) >= 40:
                break

        return notices


class CollegeScraper(BaseScraper):
    """学院官网爬虫（机电学院等）"""

    def parse(self, html: str) -> list[dict]:
        return CampusScraper.parse(self, html)
