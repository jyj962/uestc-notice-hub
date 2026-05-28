# -*- coding: utf-8 -*-
"""
Flask Web 服务 - 通知看板
"""

import os
from datetime import datetime, timedelta

from flask import Flask, render_template, request, jsonify

import config
from scraper.models import get_notices, get_stats, init_db

app = Flask(__name__)

# 在模块加载时初始化数据库，兼容 PythonAnywhere 的 WSGI 加载方式
init_db()


@app.route("/")
def index():
    """通知看板主页"""
    stats = get_stats()
    return render_template("index.html",
                           categories=config.CATEGORIES,
                           stats=stats)


@app.route("/api/notices")
def api_notices():
    """API: 查询通知列表"""
    date_from = request.args.get("date_from", (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d"))
    date_to = request.args.get("date_to", "")
    keyword = request.args.get("keyword", "")
    categories_str = request.args.get("categories", "")  # 逗号分隔
    source_names_str = request.args.get("sources", "")    # 逗号分隔
    limit = request.args.get("limit", 200, type=int)

    categories = [c.strip() for c in categories_str.split(",") if c.strip()] if categories_str else None
    source_names = [s.strip() for s in source_names_str.split(",") if s.strip()] if source_names_str else None

    notices = get_notices(
        date_from=date_from,
        date_to=date_to or None,
        categories=categories,
        keyword=keyword or None,
        source_names=source_names,
        limit=limit
    )

    return jsonify({
        "count": len(notices),
        "notices": notices
    })


@app.route("/api/stats")
def api_stats():
    """API: 获取统计"""
    return jsonify(get_stats())


@app.route("/api/sources")
def api_sources():
    """API: 获取所有数据源"""
    sources = [
        {"name": s["name"], "category": s["category"], "enabled": s["enabled"]}
        for s in config.SOURCES
    ]
    # 公众号也算数据源
    for account in config.WECHAT_ACCOUNTS:
        sources.append({
            "name": f"公众号·{account}",
            "category": "其他",
            "enabled": True,
        })
    return jsonify(sources)


@app.route("/health")
def health():
    """健康检查"""
    return jsonify({"status": "ok"})


@app.route("/admin/init")
def admin_init():
    """初始化数据库（不抓取，避免超时）"""
    init_db()
    return jsonify({"ok": True, "message": "数据库已初始化，请逐个抓取数据源"})


@app.route("/admin/fetch/<source_name>")
def admin_fetch_one(source_name):
    """逐个抓取单个数据源（避免免费托管超时）"""
    import config
    from scheduler import build_scrapers
    from scraper.models import save_notices, log_fetch

    init_db()
    scrapers = {s.name: s for s in build_scrapers()}

    if source_name not in scrapers:
        return jsonify({"ok": False, "error": f"未找到数据源: {source_name}", "available": list(scrapers.keys())}), 404

    try:
        notices = scrapers[source_name].run()
        saved = save_notices(notices) if notices else 0
        log_fetch(source_name, True, saved)
        return jsonify({"ok": True, "source": source_name, "fetched": len(notices or []), "saved": saved})
    except Exception as e:
        log_fetch(source_name, False, 0, str(e))
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/admin/fetch-all")
def admin_fetch_all():
    """一次性抓取所有数据源（可能超时，建议逐个抓）"""
    from scheduler import run_once

    try:
        added = run_once()
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

    return jsonify({"ok": True, "added": added})


def run_web(host=None, port=None, debug=False):
    """启动 Web 服务"""
    init_db()
    app.run(host=host or config.WEB_HOST, port=port or config.WEB_PORT, debug=debug)


if __name__ == "__main__":
    run_web(debug=True)
