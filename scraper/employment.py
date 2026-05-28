# -*- coding: utf-8 -*-
"""
本科生就业网爬虫
"""

import re

from bs4 import BeautifulSoup

from .base import BaseScraper


class EmploymentScraper(BaseScraper):
    """就业网通知公告/招聘信息爬虫"""

    def parse(self, html: str) -> list[dict]:
        soup = BeautifulSoup(html, "lxml")
        notices = []

        # 就业网的常见列表结构
        links = soup.select("a[href]")
        seen = set()

        for a in links:
            href = a.get("href", "")
            if not href or href == "#" or "javascript" in href:
                continue

            # 只取直接文本节点（不包含子元素）
            direct_text = " ".join(
                t.strip() for t in a.find_all(string=True, recursive=False) if t.strip()
            )
            if not direct_text:
                direct_text = a.get_text(strip=True)

            # 如果文本太长（>60字），尝试取第一个span或第一个直接子文本节点
            if len(direct_text) > 60:
                first_span = a.find("span")
                if first_span:
                    direct_text = first_span.get_text(strip=True)
                else:
                    direct_text = direct_text[:60] + "..."

            title = self.clean_text(direct_text)
            if not title or len(title) < 4:
                continue
            if title in seen:
                continue
            seen.add(title)

            # 只保留看起来是通知/信息的链接
            if not any(kw in href.lower() for kw in ("news", "notice", "career", "detail", "info", "content", "article", "zp", "jy")):
                continue

            url = self.make_absolute_url(href)

            # 提取日期
            date_str = ""
            parent = a.parent
            for _ in range(4):
                if parent:
                    text = parent.get_text()
                    m = re.search(r"(\d{4}[-/]\d{1,2}[-/]\d{1,2})", text)
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

            if len(notices) >= 30:
                break

        return notices
