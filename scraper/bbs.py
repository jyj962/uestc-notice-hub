# -*- coding: utf-8 -*-
"""
清水河畔BBS 爬虫
"""

import re

from bs4 import BeautifulSoup

from .base import BaseScraper


class BBSScraper(BaseScraper):
    """清水河畔BBS 热帖爬虫"""

    def parse(self, html: str) -> list[dict]:
        soup = BeautifulSoup(html, "lxml")
        notices = []

        # Discuz! 论坛常见结构
        # 帖子列表通常在 table 中
        threads = soup.select("tbody[id^='normalthread_']")

        if not threads:
            # 备用：找所有带链接的帖子标题
            threads = soup.select("a.xst, th.new a, th.common a")

        for t in threads:
            if t.name == "a":
                title = self.clean_text(t.get_text())
                url = self.make_absolute_url(t.get("href", ""))
                parent_td = t.find_parent("td") or t.find_parent("div")
            else:
                link = t.find("a", class_="xst") or t.find("th").find("a") if t.find("th") else None
                if not link:
                    continue
                title = self.clean_text(link.get_text())
                url = self.make_absolute_url(link.get("href", ""))
                parent_td = t

            if not title or len(title) < 2:
                continue

            # Discuz! 中日期通常在 em 或 span 中
            date_str = ""
            if parent_td:
                date_el = parent_td.find("em") or parent_td.find("span")
                if date_el:
                    date_str = self.clean_text(date_el.get_text())

            # 帖子标题添加BBS标记
            full_title = f"[清水河畔] {title}"

            notices.append({
                "id": self.generate_id(title, date_str, self.name),
                "title": full_title,
                "date": self.parse_date(date_str),
                "source_url": url,
                "summary": "",
            })

            if len(notices) >= 20:
                break

        return notices
