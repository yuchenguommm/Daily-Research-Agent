# Daily Research Agent / 每日论文研究助手

[English](#english) | [中文](#中文)

---

<a name="english"></a>
## English

### Overview

Daily Research Agent is an automated research assistant that fetches, filters, and summarizes academic papers daily. It retrieves new papers from arXiv and journal RSS feeds, uses large language models to evaluate relevance and importance, generates summaries, and sends curated daily digests via email.

### Features

- 📚 Fetch new papers from specified arXiv categories
- 📰 Monitor journal RSS feeds (e.g., PRL, PRX, Nature Physics)
- ⭐ Integrate SciRate scores and journal weight ratings
- 🤖 Use LLM to generate structured summaries and relevance analysis
- 📧 Send daily curated paper lists via email
- 🔄 Local deduplication and read tracking
- 💾 Persistent storage of seen papers to avoid duplicates

### Prerequisites

- Python 3.7+
- Email account with SMTP access (Gmail, Outlook, etc.)
- API key for LLM service (DeepSeek or compatible API)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yuchenguommm/New_article_client.git
   cd New_article_client
   ```

2. **Create a virtual environment (recommended)**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

   Or install manually:
   ```bash
   pip install requests feedparser arxiv yagmail python-dotenv beautifulsoup4 joblib scirate
   ```

### Configuration

#### 1. Create Configuration File

Create a file named `abc.json` in the project root with the following structure:

```json
{
  "RESEARCH_PROFILE": "Your research interests and focus areas...",
  "EMAIL_ADDRESS": "your_email@example.com",
  "EMAIL_PASSWORD": "your_email_app_password",
  "ARXIV_CATEGORIES": ["hep-th", "quant-ph", "cond-mat.str-el"],
  "JOURNAL_FEEDS": {
    "PRL": "https://feeds.aps.org/rss/recent/prl.xml",
    "PRX": "https://feeds.aps.org/rss/recent/prx.xml",
    "Nature Physics": "https://www.nature.com/nphys.rss"
  },
  "JOURNAL_WEIGHT_0_10": {
    "PRL": 9,
    "PRX": 8,
    "Nature Physics": 10
  }
}
```

**Configuration Fields:**

- `RESEARCH_PROFILE`: Description of your research interests (used by LLM for relevance scoring)
- `EMAIL_ADDRESS`: Your email address (both sender and recipient)
- `EMAIL_PASSWORD`: Email app password (see [Email Setup](#email-setup))
- `ARXIV_CATEGORIES`: List of arXiv category codes to monitor
- `JOURNAL_FEEDS`: Dictionary of journal names and their RSS feed URLs
- `JOURNAL_WEIGHT_0_10`: Journal importance weights (0-10 scale)

#### 2. Email Setup

**Gmail:**
1. Enable 2-factor authentication
2. Generate an App Password: [Google Account Settings](https://myaccount.google.com/apppasswords)
3. Use the app password in `EMAIL_PASSWORD` field

**Outlook/Other:**
- Follow your provider's instructions for app-specific passwords

#### 3. API Key Configuration

Edit `main.py` to set your LLM API key:

```python
API_KEY = "your_api_key_here"
```

Or use environment variables:
```bash
export DEEPSEEK_API_KEY="your_api_key_here"
```

And modify `main.py` to read from environment:
```python
import os
API_KEY = os.getenv("DEEPSEEK_API_KEY")
```

### Usage

Run the agent:

```bash
python main.py
```

The agent will:
1. Fetch papers from the past few days from arXiv and journals
2. Filter out papers already seen (stored in `seen_papers.json`)
3. Score each paper using the LLM based on relevance and importance
4. Calculate total scores combining LLM ratings and journal weights
5. Select papers above the threshold
6. Generate an HTML digest and send it via email

### Project Structure

```
New_article_client/
├── main.py                 # Main entry point
├── abc.json               # User configuration file
├── seen_papers.json       # Tracking file for read papers (auto-generated)
├── email_failed.html      # Backup file if email sending fails
└── README.md              # This file
```

### Workflow

```
1. Fetch new papers from arXiv + Journal RSS
          ↓
2. Deduplicate using seen_papers.json
          ↓
3. For each paper:
   - Call LLM for relevance score & summary
   - Add journal weight if applicable
          ↓
4. Filter papers above threshold
          ↓
5. Generate HTML digest
          ↓
6. Send email (or save to email_failed.html)
```

### Troubleshooting

**Email not sending:**
- Check email credentials in `abc.json`
- Verify app password is correct
- Check that less secure app access is enabled (if applicable)
- If email fails, digest is saved to `email_failed.html`

**No papers fetched:**
- Verify arXiv categories are correct
- Check journal RSS feed URLs are accessible
- Ensure internet connection is stable

**API errors:**
- Verify API key is valid and has credits
- Check API endpoint configuration
- Review rate limits

**No email received:**
- The program exits without sending if no new papers are found
- Check spam/junk folder
- Verify email address in configuration

### Customization

To modify filtering strategy or weights, edit the relevant parameters in `main.py`:

- Adjust relevance score thresholds
- Modify journal weights
- Change LLM prompts for different analysis styles
- Customize HTML email template

### Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

### License

This project is open source and available for personal research automation use.

---

<a name="中文"></a>
## 中文

### 概述

每日论文研究助手是一个自动化的研究助手工具，可以每天自动抓取、筛选和总结学术论文。它从 arXiv 和期刊 RSS 源获取新论文，使用大型语言模型评估相关性和重要性，生成摘要，并通过电子邮件发送每日精选摘要。

### 功能特性

- 📚 从指定的 arXiv 分类抓取新论文
- 📰 监控期刊 RSS 源（如 PRL、PRX、Nature Physics 等）
- ⭐ 整合 SciRate 评分和期刊权重评级
- 🤖 使用大语言模型生成结构化摘要和相关性分析
- 📧 通过电子邮件发送每日精选论文列表
- 🔄 本地去重和已读跟踪
- 💾 持久化存储已读论文以避免重复

### 系统要求

- Python 3.7+
- 支持 SMTP 的邮箱账户（Gmail、Outlook 等）
- 大语言模型服务的 API 密钥（DeepSeek 或兼容 API）

### 安装步骤

1. **克隆仓库**
   ```bash
   git clone https://github.com/yuchenguommm/New_article_client.git
   cd New_article_client
   ```

2. **创建虚拟环境（推荐）**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows 系统：venv\Scripts\activate
   ```

3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

   或手动安装：
   ```bash
   pip install requests feedparser arxiv yagmail python-dotenv beautifulsoup4 joblib scirate
   ```

### 配置说明

#### 1. 创建配置文件

在项目根目录创建名为 `abc.json` 的文件，结构如下：

```json
{
  "RESEARCH_PROFILE": "你的研究方向和重点领域描述...",
  "EMAIL_ADDRESS": "your_email@example.com",
  "EMAIL_PASSWORD": "your_email_app_password",
  "ARXIV_CATEGORIES": ["hep-th", "quant-ph", "cond-mat.str-el"],
  "JOURNAL_FEEDS": {
    "PRL": "https://feeds.aps.org/rss/recent/prl.xml",
    "PRX": "https://feeds.aps.org/rss/recent/prx.xml",
    "Nature Physics": "https://www.nature.com/nphys.rss"
  },
  "JOURNAL_WEIGHT_0_10": {
    "PRL": 9,
    "PRX": 8,
    "Nature Physics": 10
  }
}
```

**配置字段说明：**

- `RESEARCH_PROFILE`：研究方向描述（用于大模型判断相关性）
- `EMAIL_ADDRESS`：你的邮箱地址（发送和接收地址）
- `EMAIL_PASSWORD`：邮箱应用专用密码（见[邮箱设置](#邮箱设置)）
- `ARXIV_CATEGORIES`：要监控的 arXiv 分类代码列表
- `JOURNAL_FEEDS`：期刊名称和 RSS 源 URL 的字典
- `JOURNAL_WEIGHT_0_10`：期刊重要性权重（0-10 分制）

#### 2. 邮箱设置 {#邮箱设置}

**Gmail：**
1. 启用两步验证
2. 生成应用专用密码：[Google 账户设置](https://myaccount.google.com/apppasswords)
3. 在 `EMAIL_PASSWORD` 字段使用应用专用密码

**Outlook/其他邮箱：**
- 按照你的邮箱服务商的说明设置应用专用密码

#### 3. API 密钥配置

编辑 `main.py` 设置你的大语言模型 API 密钥：

```python
API_KEY = "你的_api_密钥"
```

或使用环境变量：
```bash
export DEEPSEEK_API_KEY="你的_api_密钥"
```

并修改 `main.py` 从环境变量读取：
```python
import os
API_KEY = os.getenv("DEEPSEEK_API_KEY")
```

### 使用方法

运行助手：

```bash
python main.py
```

程序将会：
1. 从 arXiv 和期刊获取过去几天的论文
2. 过滤掉已读论文（存储在 `seen_papers.json` 中）
3. 使用大语言模型根据相关性和重要性对每篇论文评分
4. 结合大模型评分和期刊权重计算总分
5. 选择超过阈值的论文
6. 生成 HTML 摘要并通过邮件发送

### 项目结构

```
New_article_client/
├── main.py                 # 主程序入口
├── abc.json               # 用户配置文件
├── seen_papers.json       # 已读论文跟踪文件（自动生成）
├── email_failed.html      # 邮件发送失败时的备份文件
└── README.md              # 本文件
```

### 工作流程

```
1. 从 arXiv 和期刊 RSS 获取新论文
          ↓
2. 使用 seen_papers.json 去重
          ↓
3. 对每篇论文：
   - 调用大模型评估相关性分数和生成摘要
   - 如适用则添加期刊权重
          ↓
4. 筛选超过阈值的论文
          ↓
5. 生成 HTML 摘要
          ↓
6. 发送邮件（或保存到 email_failed.html）
```

### 常见问题

**邮件无法发送：**
- 检查 `abc.json` 中的邮箱凭据
- 验证应用专用密码是否正确
- 检查是否启用了不太安全的应用访问（如适用）
- 如果邮件发送失败，摘要会保存到 `email_failed.html`

**未获取到论文：**
- 验证 arXiv 分类代码是否正确
- 检查期刊 RSS 源 URL 是否可访问
- 确保网络连接稳定

**API 错误：**
- 验证 API 密钥是否有效且有额度
- 检查 API 端点配置
- 查看请求频率限制

**未收到邮件：**
- 如果没有新论文，程序会直接退出不发送邮件
- 检查垃圾邮件/垃圾箱文件夹
- 验证配置中的邮箱地址

### 自定义

要修改筛选策略或权重，可以编辑 `main.py` 中的相关参数：

- 调整相关性分数阈值
- 修改期刊权重
- 更改大模型提示词以获得不同的分析风格
- 自定义 HTML 邮件模板

### 贡献

欢迎贡献！请随时提交问题或拉取请求。

### 许可证

本项目为开源项目，可用于个人研究自动化使用。

---

**Made with ❤️ for researchers | 为研究者用心打造**
