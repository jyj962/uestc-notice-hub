# -*- coding: utf-8 -*-
"""
数据模型和数据库操作
使用 SQLite 存储，简单不折腾
"""

import sqlite3
from datetime import datetime, timedelta
from contextlib import contextmanager

import config


def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA encoding='UTF-8'")
    return conn


@contextmanager
def db_session():
    """数据库会话上下文管理器，自动提交/回滚"""
    conn = get_db()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """初始化数据库表"""
    with db_session() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS notices (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                date TEXT NOT NULL,
                source_name TEXT NOT NULL,
                source_category TEXT NOT NULL,
                source_type TEXT NOT NULL,
                source_url TEXT,
                summary TEXT,
                is_new INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        # 索引：加速按日期和分类查询
        conn.execute("CREATE INDEX IF NOT EXISTS idx_date ON notices(date)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_category ON notices(source_category)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_source ON notices(source_name)")
        # 索引：加速去重查询
        conn.execute("CREATE INDEX IF NOT EXISTS idx_title_date ON notices(title, date)")

        # 抓取日志表：记录每次抓取的状态
        conn.execute("""
            CREATE TABLE IF NOT EXISTS fetch_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_name TEXT NOT NULL,
                success INTEGER NOT NULL,
                count INTEGER DEFAULT 0,
                error_msg TEXT,
                created_at TEXT NOT NULL
            )
        """)


def save_notices(notices: list[dict]) -> int:
    """
    保存通知到数据库，返回新增数量
    去重规则：同一 source_name + title + date 只保留一条
    """
    saved = 0
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    today = datetime.now().strftime("%Y-%m-%d")

    with db_session() as conn:
        for n in notices:
            try:
                notice_id = n.get("id") or f"{n.get('source_name','')}|{n.get('title','')}|{n.get('date','')}"
                exists = conn.execute(
                    "SELECT id FROM notices WHERE title=? AND date=? AND source_name=?",
                    (n["title"], n.get("date", today), n.get("source_name", ""))
                ).fetchone()

                if exists:
                    conn.execute("""
                        UPDATE notices SET 
                            source_url=?, summary=?, updated_at=?
                        WHERE id=?
                    """, (
                        n.get("source_url", ""),
                        n.get("summary", ""),
                        now,
                        exists["id"]
                    ))
                else:
                    conn.execute("""
                        INSERT OR IGNORE INTO notices (id, title, date, source_name, source_category, 
                                         source_type, source_url, summary, is_new, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                    """, (
                        notice_id,
                        n["title"],
                        n.get("date", today),
                        n.get("source_name", ""),
                        n.get("source_category", "其他"),
                        n.get("source_type", "web"),
                        n.get("source_url", ""),
                        n.get("summary", ""),
                        now,
                        now
                    ))
                    saved += 1
            except Exception:
                # 忽略单条保存失败的，继续处理下一条
                continue

    return saved


def get_notices(date_from: str = None, date_to: str = None,
                categories: list[str] = None, keyword: str = None,
                source_names: list[str] = None, limit: int = 200) -> list[dict]:
    """
    查询通知列表，支持多条件筛选
    """
    conditions = ["1=1"]
    params = []

    if date_from:
        conditions.append("date >= ?")
        params.append(date_from)
    if date_to:
        conditions.append("date <= ?")
        params.append(date_to)
    if categories:
        placeholders = ",".join("?" * len(categories))
        conditions.append(f"source_category IN ({placeholders})")
        params.extend(categories)
    if keyword:
        conditions.append("(title LIKE ? OR summary LIKE ?)")
        params.extend([f"%{keyword}%", f"%{keyword}%"])
    if source_names:
        placeholders = ",".join("?" * len(source_names))
        conditions.append(f"source_name IN ({placeholders})")
        params.extend(source_names)

    sql = f"""
        SELECT * FROM notices 
        WHERE {' AND '.join(conditions)}
        ORDER BY date DESC, created_at DESC
        LIMIT ?
    """
    params.append(limit)

    with db_session() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def get_stats() -> dict:
    """获取统计信息"""
    with db_session() as conn:
        total = conn.execute("SELECT COUNT(*) FROM notices").fetchone()[0]
        today_new = conn.execute(
            "SELECT COUNT(*) FROM notices WHERE is_new=1 AND date=?", 
            (datetime.now().strftime("%Y-%m-%d"),)
        ).fetchone()[0]
        # 各分类数量
        cat_rows = conn.execute(
            "SELECT source_category, COUNT(*) as cnt FROM notices GROUP BY source_category"
        ).fetchall()
        categories = {r["source_category"]: r["cnt"] for r in cat_rows}
    return {
        "total": total,
        "today_new": today_new,
        "categories": categories
    }


def mark_all_read():
    """将所有通知标记为非新增"""
    with db_session() as conn:
        conn.execute("UPDATE notices SET is_new=0 WHERE is_new=1")


def clean_old_notices():
    """清理过期数据"""
    cutoff = (datetime.now() - timedelta(days=config.RETENTION_DAYS)).strftime("%Y-%m-%d")
    with db_session() as conn:
        deleted = conn.execute("DELETE FROM notices WHERE date < ?", (cutoff,)).rowcount
        conn.execute("DELETE FROM fetch_log WHERE created_at < ?", (cutoff,))
    return deleted


def log_fetch(source_name: str, success: bool, count: int = 0, error_msg: str = None):
    """记录抓取日志"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with db_session() as conn:
        conn.execute(
            "INSERT INTO fetch_log (source_name, success, count, error_msg, created_at) VALUES (?, ?, ?, ?, ?)",
            (source_name, 1 if success else 0, count, error_msg, now)
        )
