# Daily Research Agent

一个每日自动抓取并筛选论文的研究助手：从 arXiv 与期刊 RSS 获取新论文，调用大模型评估相关性与重要性，生成摘要，并通过邮件发送每日 digest。

## 功能

- 抓取 arXiv 指定分类的新论文
- 抓取期刊 RSS（如 PRL/PRX/Nature Physics 等）
- 结合 SciRate 与期刊权重评分
- 使用大模型生成结构化摘要与相关性分析
- 邮件发送每日精选列表
- 本地去重与已读记录

## 目录结构

- main.py：主程序入口
- abc.json：用户配置（研究方向、邮箱、订阅源）
- seen_papers.json：已读论文记录（运行后自动更新）

## 快速开始

1. 安装依赖（建议使用虚拟环境）

	 需要的主要依赖：

	 - requests
	 - feedparser
	 - arxiv
	 - yagmail
	 - python-dotenv
	 - beautifulsoup4
	 - joblib
	 - scirate

2. 准备配置文件 abc.json（见下方配置说明）

3. 配置大模型 API Key（见“模型配置”）

4. 运行

	 python main.py

## 配置说明（abc.json）

示例结构：

{
	"RESEARCH_PROFILE": "你的研究方向描述...",
	"EMAIL_ADDRESS": "your_email@example.com",
	"EMAIL_PASSWORD": "your_email_app_password",
	"ARXIV_CATEGORIES": ["hep-th", "quant-ph"],
	"JOURNAL_FEEDS": {
		"PRL": "https://feeds.aps.org/rss/recent/prl.xml",
		"PRX": "https://feeds.aps.org/rss/recent/prx.xml"
	},
	"JOURNAL_WEIGHT_0_10": {
		"PRL": 9,
		"PRX": 8
	}
}

字段说明：

- RESEARCH_PROFILE：研究方向描述，用于大模型判断相关性
- EMAIL_ADDRESS：发送与接收邮件地址（当前代码会发送给自己）
- EMAIL_PASSWORD：邮箱授权码/应用密码（如 Gmail 需使用 App Password）
- ARXIV_CATEGORIES：arXiv 分类列表
- JOURNAL_FEEDS：期刊 RSS 源
- JOURNAL_WEIGHT_0_10：期刊权重（0–10）

## 模型配置

当前代码在 main.py 中使用 DeepSeek 接口并包含 API_KEY 变量。请在使用前替换为你自己的密钥，或修改代码以从 .env 读取。

## 运行逻辑简述

- 拉取过去几天的 arXiv 论文与期刊 RSS
- 根据 seen_papers.json 去重并过滤已读
- 对每篇论文调用模型打分与摘要
- 计算总分并选取阈值以上论文
- 生成 HTML digest 并发送邮件

## 常见问题

- **邮件发送失败**：会自动保存为 email_failed.html
- **无新论文**：程序会直接退出，不发送邮件

## 备注

本项目面向个人研究日报自动化。如需修改筛选策略或权重，请在 main.py 中调整相关参数。
