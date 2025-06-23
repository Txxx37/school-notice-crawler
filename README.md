# 校园通知智能爬虫

自动爬取学校官网通知，存储到 CSV 和 MySQL，并推送课题通知到邮箱。

![Python](https://img.shields.io/badge/python-3.9-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)


## 项目背景

在校园生活中，及时获取学校通知尤其是课题相关信息至关重要。本项目通过自动化爬虫技术，实现对学校官网通知的实时监控、筛选和推送，帮助用户高效获取关键信息。


## 功能亮点

### 1. 智能爬取模块
- 定时抓取官网通知公告页
- 支持多线程并发处理
- 自动识别网页结构变化并告警

### 2. 数据清洗与处理
- 标题去重（移除"关于"/"通知"等冗余词）
- 自动提取关键信息：
  - 项目名称
  - 项目类型（课题申报/项目结题/成果认定等）
  - 发布日期/截止日期
  - 联系人信息
  - 网页链接

### 3. 多维持久化存储
- 每日生成结构化 CSV 文件
- 同步存储到 MySQL 数据库
- 支持数据增量更新

### 4. 智能邮件推送
- 自动筛选含"课题"关键词的通知
- 每日定时推送最新信息
- 邮件内容包含：
  - 通知摘要
  - 关键时间节点
  - 原文链接
  - 可视化图表（如发布趋势）


## 技术架构

![技术栈](https://via.placeholder.com/600x200?text=Technology+Stack)

- **爬虫框架**：Requests + BeautifulSoup4
- **数据处理**：Pandas + NumPy
- **数据库**：MySQL + SQLAlchemy
- **邮件服务**：smtplib + email
- **定时任务**：APScheduler
- **部署**：Docker + GitHub Actions


## 项目结构

```
campus-notice-crawler/
├── main.py               # 主程序入口
├── config/               # 配置文件
│   ├── db_config.py      # 数据库配置
│   └── email_config.py   # 邮件配置
├── crawler/              # 爬虫模块
│   ├── spider.py         # 网页爬虫
│   └── parser.py         # 内容解析
├── processor/            # 数据处理模块
│   ├── cleaner.py        # 数据清洗
│   └── exporter.py       # 数据导出
├── mailer/               # 邮件模块
│   └── sender.py         # 邮件发送
├── tests/                # 测试用例
├── requirements.txt      # 依赖清单
└── README.md             # 项目说明
```


## 安装与使用

### 环境准备

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt
```

### 配置文件

修改 `config/` 目录下的配置文件：

```python
# db_config.py
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'your_username',
    'password': 'your_password',
    'database': 'school_notices'
}

# email_config.py
EMAIL_CONFIG = {
    'smtp_server': 'smtp.example.com',
    'smtp_port': 587,
    'sender_email': 'your_email@example.com',
    'sender_password': 'your_email_password',
    'recipient_email': 'recipient@example.com'
}
```

### 运行程序

```bash
# 直接运行
python main.py

# 或使用定时任务（Linux）
crontab -e
0 9 * * * cd /path/to/project && python main.py  # 每天9点执行
```


## 效果展示

### 邮件推送示例

![邮件示例](https://via.placeholder.com/600x400?text=Email+Notification+Example)

### 数据库存储

![数据库表结构](https://via.placeholder.com/600x300?text=Database+Schema)


## 贡献指南

1. Fork 本仓库
2. 创建新分支：`git checkout -b feature/new-feature`
3. 提交更改：`git commit -m "Add new feature"`
4. 推送分支：`git push origin feature/new-feature`
5. 提交 Pull Request


## 许可证

本项目采用 [MIT License](https://github.com/your_username/school-notice-crawler/blob/main/LICENSE) 许可协议。


## 联系我

- GitHub: [Txxx37]([https://github.com/Txxx37])
- Email: 2191370750@example.com


