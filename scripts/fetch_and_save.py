# -*- coding: utf-8 -*-
"""
GitHub Actions 专用脚本：抓取通知并生成静态页面
"""
import sys
import os
import json
from datetime import datetime

# 添加项目根目录到 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper.campus import CampusScraper, JwcScraper, XgbScraper, CollegeScraper
from scraper.employment import EmploymentScraper
from scraper.bbs import BBSScraper
import config

def run_all_scrapers():
    """运行所有爬虫，返回通知列表"""
    scrapers = [
        CampusScraper([s for s in config.SOURCES if s["name"] == "学校主站"][0]),
        JwcScraper([s for s in config.SOURCES if s["name"] == "教务处"][0]),
        XgbScraper([s for s in config.SOURCES if s["name"] == "党委学工部"][0]),
        EmploymentScraper([s for s in config.SOURCES if s["name"] == "本科生就业网"][0]),
        BBSScraper([s for s in config.SOURCES if s["name"] == "清水河畔BBS"][0]),
        CollegeScraper([s for s in config.SOURCES if s["name"] == "机电学院"][0]),
    ]

    all_notices = []
    for scraper in scrapers:
        try:
            notices = scraper.run()
            all_notices.extend(notices)
            print(f"[{scraper.name}] 获取 {len(notices)} 条")
        except Exception as e:
            print(f"[{scraper.name}] 失败: {e}")

    return all_notices

def save_to_json(notices, output_path):
    """保存通知到 JSON 文件"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "count": len(notices),
            "notices": notices
        }, f, ensure_ascii=False, indent=2)
    print(f"保存了 {len(notices)} 条通知到 {output_path}")

def generate_html(notices, output_path):
    """生成静态 HTML 看板"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    # 按日期排序，最新在前
    notices.sort(key=lambda x: x.get("date", ""), reverse=True)
    
    # 生成通知列表 HTML
    notice_items = ""
    for n in notices:
        is_new = "is-new" if n.get("date") == today else ""
        source = n.get("source_name", "未知")
        category = n.get("source_category", "其他")
        title = n.get("title", "").replace("<", "&lt;").replace(">", "&gt;")
        url = n.get("source_url", "#")
        date = n.get("date", "")
        summary = n.get("summary", "").replace("<", "&lt;").replace(">", "&gt;")[:200]
        new_badge = '<span class="new-badge">NEW</span>' if is_new else ""
        
        notice_items += f'''
        <li class="notice-item {is_new}" onclick="window.open('{url}', '_blank')">
            <div class="notice-title">{title} {new_badge}</div>
            <div class="notice-meta">
                <span class="notice-source">{source}</span>
                <span>📅 {date}</span>
                <span>🏷️ {category}</span>
            </div>
            <div class="notice-summary">{summary}</div>
        </li>'''

    # 生成分类标签
    categories = sorted(set(n.get("source_category", "其他") for n in notices))
    cat_tags = '<span class="cat-tag active" onclick="filterCategory(\'\')">全部</span>'
    for cat in categories:
        cat_tags += f'<span class="cat-tag" onclick="filterCategory(\'{cat}\')">{cat}</span>'

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>电子科技大学通知聚合</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif; background: #f5f6fa; color: #333; }}
        .header {{ background: linear-gradient(135deg, #1a3a5c 0%, #2d6aa0 100%); color: #fff; padding: 16px 24px; position: sticky; top: 0; z-index: 100; }}
        .header h1 {{ font-size: 20px; }}
        .header .subtitle {{ font-size: 13px; opacity: 0.8; }}
        .header .stats {{ font-size: 13px; margin-top: 4px; }}
        .header .stats .num {{ font-size: 22px; font-weight: 700; }}
        .search-bar {{ background: #fff; padding: 12px 24px; display: flex; gap: 10px; flex-wrap: wrap; border-bottom: 1px solid #e8e8e8; }}
        .search-bar input {{ flex: 1; min-width: 200px; padding: 8px 16px; border: 1px solid #d9d9d9; border-radius: 6px; font-size: 14px; }}
        .search-bar input:focus {{ border-color: #2d6aa0; outline: none; }}
        .category-tags {{ background: #fff; padding: 8px 24px; display: flex; gap: 8px; flex-wrap: wrap; border-bottom: 1px solid #e8e8e8; }}
        .cat-tag {{ padding: 4px 14px; border-radius: 20px; font-size: 13px; cursor: pointer; border: 1px solid #d9d9d9; background: #fff; }}
        .cat-tag:hover {{ border-color: #2d6aa0; color: #2d6aa0; }}
        .cat-tag.active {{ background: #2d6aa0; color: #fff; border-color: #2d6aa0; }}
        .container {{ max-width: 960px; margin: 0 auto; padding: 16px 24px; }}
        .notice-list {{ list-style: none; }}
        .notice-item {{ background: #fff; margin-bottom: 10px; border-radius: 8px; padding: 16px 20px; border-left: 4px solid #e8e8e8; cursor: pointer; transition: box-shadow 0.2s; }}
        .notice-item:hover {{ box-shadow: 0 2px 12px rgba(0,0,0,0.1); }}
        .notice-item.is-new {{ border-left-color: #fa8c16; background: #fffbe6; }}
        .notice-title {{ font-size: 15px; font-weight: 600; color: #1a3a5c; margin-bottom: 6px; }}
        .notice-meta {{ display: flex; gap: 16px; font-size: 12px; color: #999; flex-wrap: wrap; }}
        .notice-source {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; background: #2d6aa0; color: #fff; }}
        .notice-summary {{ margin-top: 6px; font-size: 13px; color: #666; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }}
        .new-badge {{ background: #fa8c16; color: #fff; padding: 1px 6px; border-radius: 4px; font-size: 11px; margin-left: 6px; }}
        .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #999; }}
        .empty {{ text-align: center; padding: 60px; color: #999; }}
        @media (max-width: 768px) {{
            .header {{ padding: 12px 16px; }}
            .search-bar {{ padding: 8px 16px; }}
            .container {{ padding: 12px; }}
            .notice-item {{ padding: 12px; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📢 电子科技大学通知聚合</h1>
        <div class="subtitle">清水河校区 · 机电学院 · 电气工程 | 来源真实 每日更新</div>
        <div class="stats">📊 共 <span class="num">{len(notices)}</span> 条通知 | 🕐 更新于 {datetime.now().strftime("%Y-%m-%d %H:%M")}</div>
    </div>
    <div class="search-bar">
        <input type="text" id="searchInput" onkeyup="searchNotices()" placeholder="🔍 搜索通知标题...">
    </div>
    <div class="category-tags" id="categoryTags">
        {cat_tags}
    </div>
    <div class="container">
        <ul class="notice-list" id="noticeList">
            {notice_items}
        </ul>
    </div>
    <div class="footer">
        电子科技大学通知聚合系统 | 数据来源：学校官网、教务处、学工部、就业网等
    </div>
    <script>
        function searchNotices() {{
            const keyword = document.getElementById('searchInput').value.toLowerCase();
            const items = document.querySelectorAll('.notice-item');
            items.forEach(item => {{
                const title = item.querySelector('.notice-title').textContent.toLowerCase();
                item.style.display = title.includes(keyword) ? '' : 'none';
            }});
        }}
        function filterCategory(cat) {{
            document.querySelectorAll('.cat-tag').forEach(t => t.classList.remove('active'));
            event.target.classList.add('active');
            const items = document.querySelectorAll('.notice-item');
            items.forEach(item => {{
                if (!cat) {{ item.style.display = ''; return; }}
                const source = item.querySelector('.notice-meta').textContent;
                item.style.display = source.includes(cat) ? '' : 'none';
            }});
        }}
    </script>
</body>
</html>'''

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"生成静态页面: {output_path}")

if __name__ == "__main__":
    # 确保 public 目录存在
    public_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "public")
    os.makedirs(public_dir, exist_ok=True)

    # 抓取所有数据
    notices = run_all_scrapers()

    # 保存 JSON（备用）
    json_path = os.path.join(public_dir, "notices.json")
    save_to_json(notices, json_path)

    # 生成静态 HTML
    html_path = os.path.join(public_dir, "index.html")
    generate_html(notices, html_path)

    print(f"\n完成！共 {len(notices)} 条通知")
