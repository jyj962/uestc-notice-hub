# -*- coding: utf-8 -*-
"""
电子科技大学通知聚合系统 - 配置文件
修改此文件即可调整数据源、抓取时间和展示方式
"""

import os

# ==================== 项目路径 ====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
LOG_DIR = os.path.join(BASE_DIR, "logs")
DB_PATH = os.path.join(DATA_DIR, "notices.db")

# 确保目录存在
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# ==================== 爬虫通用配置 ====================
REQUEST_INTERVAL = 2       # 请求间隔（秒），避免对服务器造成压力
REQUEST_TIMEOUT = 15       # 单次请求超时（秒）
MAX_RETRIES = 3            # 失败重试次数
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)

# ==================== 定时抓取时间 ====================
SCHEDULE_TIMES = ["08:00", "18:00"]  # 每天执行的时刻

# ==================== 数据保留 ====================
RETENTION_DAYS = 90  # 通知保留天数

# ==================== Web 服务 ====================
WEB_HOST = "0.0.0.0"
WEB_PORT = 5000

# ==================== 数据源配置 ====================
SOURCES = [
    {
        "name": "学校主站",
        "url": "https://news.uestc.edu.cn",
        "notice_url": "https://news.uestc.edu.cn/xxgg/xs.htm",  # 学校公告-学生
        "category": "学校公告",
        "enabled": True,
        "type": "web",
    },
    {
        "name": "教务处",
        "url": "https://www.jwc.uestc.edu.cn",
        "notice_url": "https://www.jwc.uestc.edu.cn",
        "category": "教务通知",
        "enabled": True,
        "type": "web",
    },
    {
        "name": "党委学工部",
        "url": "https://xgb.uestc.edu.cn",
        "notice_url": "https://xgb.uestc.edu.cn/notice/list/5b22b3d234578028a69d2321",  # 通知公告
        "category": "学校公告",
        "enabled": True,
        "type": "web",
    },
    {
        "name": "本科生就业网",
        "url": "https://jiuye.uestc.edu.cn",
        "notice_url": "https://jiuye.uestc.edu.cn/career/news/notice",
        "category": "就业招聘",
        "enabled": True,
        "type": "web",
    },
    {
        "name": "清水河畔BBS",
        "url": "https://bbs.uestc.edu.cn",
        "notice_url": "https://bbs.uestc.edu.cn/forum.php",
        "category": "论坛热帖",
        "enabled": True,
        "type": "bbs",
    },
    {
        "name": "机电学院",
        "url": "https://www.smee.uestc.edu.cn",
        "notice_url": "https://www.smee.uestc.edu.cn",
        "category": "学院通知",
        "enabled": True,
        "type": "web",
    },
]

# ==================== 微信公众号列表 ====================
WECHAT_ACCOUNTS = [
    "电子科技大学",
    "成电微教务",
    "学在成电",
    "文艺成电",
    "积淀态度",
    "成电学工",
    "成电就业",
    "成电外语",
    "成电后勤",
    "成电第三空间",
    "电子科技大学图书馆",
    "电子科技大学学生事务中心",
]

# ==================== 校内系统（标记为需登录，暂不爬取公开页尝试） ====================
PORTAL_SYSTEMS = [
    {"name": "网上服务大厅", "url": "https://portal.uestc.edu.cn/new/index.html?browser=no"},
    {"name": "智慧学工", "url": "https://jzsz.uestc.edu.cn"},
    {"name": "财务系统", "url": "https://cw.uestc.edu.cn"},
]

# ==================== 分类标签定义 ====================
CATEGORIES = {
    "教务通知": {"icon": "🏫", "color": "#1890ff"},
    "学校公告": {"icon": "📢", "color": "#722ed1"},
    "学院通知": {"icon": "🏛️", "color": "#13c2c2"},
    "讲座活动": {"icon": "🎓", "color": "#52c41a"},
    "就业招聘": {"icon": "💼", "color": "#fa8c16"},
    "竞赛科创": {"icon": "🏆", "color": "#eb2f96"},
    "奖助学金": {"icon": "💰", "color": "#f5222d"},
    "论坛热帖": {"icon": "🗣️", "color": "#595959"},
    "其他":     {"icon": "📌", "color": "#8c8c8c"},
}
