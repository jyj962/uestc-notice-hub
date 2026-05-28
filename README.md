# 电子科技大学通知聚合系统

清水河校区 · 机电学院 · 电气工程 | 每天自动抓取学校通知并展示

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 修改配置（可选）
编辑 `config.py`：
- `SOURCES`：增减数据源及URL
- `WECHAT_ACCOUNTS`：增减公众号名称
- `SCHEDULE_TIMES`：修改抓取时间（默认每天 08:00 和 18:00）
- `WEB_PORT`：修改 Web 服务端口（默认 5000）

### 3. 启动
```bash
python main.py
```
打开浏览器访问 http://127.0.0.1:5000

### 4. 后台运行（Windows）
```powershell
# 创建计划任务，每天自动启动
# 或者直接保持终端窗口不关闭
```

## 数据源

| 来源 | 状态 |
|------|------|
| 学校主站 (news.uestc.edu.cn) | ✅ |
| 教务处 (jwc.uestc.edu.cn) | ✅ |
| 学工部 (xgb.uestc.edu.cn) | ✅ |
| 就业网 (jiuye.uestc.edu.cn) | ✅ |
| 机电学院 (smee.uestc.edu.cn) | ✅ |
| 清水河畔BBS (bbs.uestc.edu.cn) | ⚠️ 待适配 |
| 微信公众号 (12个) | ⚠️ 需手动触发 |

## 项目结构
```
uestc-notice-hub/
├── main.py              # 入口
├── config.py            # 配置文件
├── scheduler.py         # 定时任务
├── scraper/             # 爬虫模块
│   ├── base.py          # 基础框架
│   ├── campus.py        # 学校/教务/学工/学院爬虫
│   ├── employment.py    # 就业网爬虫
│   ├── bbs.py           # 清水河畔爬虫
│   ├── wechat.py        # 微信公众号爬虫
│   └── models.py        # 数据库模型
├── web/                 # Web 看板
│   ├── app.py           # Flask 服务
│   ├── templates/       # HTML 模板
│   └── static/          # CSS/JS
├── data/                # SQLite 数据库
└── logs/                # 抓取日志
```

## 功能

- 🔍 多源通知聚合（学校/教务处/学工部/就业/学院/BBS/公众号）
- 📊 本地 Web 看板，支持分类筛选和关键词搜索
- 🆕 今日新增标记
- ⏰ 定时自动抓取（APScheduler）
- 💾 SQLite 存储，保留 90 天
- 📱 响应式布局，手机可看

## 云部署（PythonAnywhere 免费版，关机也能访问）

如果你希望手机随时访问、电脑关机也不影响，可把项目部署到 PythonAnywhere 免费账户。

### 1. 上传代码到 GitHub
只上传代码文件（不要上传 `data/`、`logs/`）。

### 2. PythonAnywhere 部署步骤
1. 注册并登录 PythonAnywhere 免费账号
2. 打开 `Bash` 控制台，克隆你的仓库：
   ```bash
   git clone https://github.com/<你的用户名>/<你的仓库>.git
   ```
3. 创建虚拟环境并安装依赖：
   ```bash
   cd <你的仓库>
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
4. 进入 `Web` 页签，新增 Flask Web App，设置：
   - Source code: `/home/<你的用户名>/<你的仓库>`
   - Working directory: 同上
   - WSGI configuration file: 使用项目里的 `wsgi.py`

### 3. 部署后初始化数据
首次部署后访问：
```
https://<你的用户名>.pythonanywhere.com/admin/init
```
即可初始化数据库并执行一次抓取。

### 4. 免费版“定时抓取”方案（替代后台常驻任务）
PythonAnywhere 免费账户不适合后台常驻进程。推荐使用页面触发：
- 手动触发抓取：`/admin/fetch`
- 或设置 PythonAnywhere 的 `Scheduled tasks`（免费账户也可设置每日任务）调用：
  ```bash
  curl -s https://<你的用户名>.pythonanywhere.com/admin/fetch
  ```
