"""
Daily Research Agent
- Fetches new papers from arXiv + PRL/PRX/Nature Physics
- Uses DeepSeek-R1-671B (Tsinghua deployment) to judge relevance & summarize
- Sends a daily email digest
"""

import os
import sys
import datetime
import requests
import feedparser
import arxiv
import yagmail
import math
from dotenv import load_dotenv
import re
import json
from bs4 import BeautifulSoup
from joblib import Parallel, delayed
from scirate.client import ScirateClient
from scirate.paper import SciratePaper
client = ScirateClient()

# =========================
# 0. 基础配置
# =========================

# load user json profile
user_profile_file = "abc.json"
if os.path.exists(user_profile_file):
    with open(user_profile_file, "r", encoding="utf-8") as f:
        user_profile = json.load(f)
    RESEARCH_PROFILE = user_profile.get("RESEARCH_PROFILE", "")
    EMAIL_ADDRESS = user_profile.get("EMAIL_ADDRESS", "")
    EMAIL_PASSWORD = user_profile.get("EMAIL_PASSWORD", "")
    ARXIV_CATEGORIES = user_profile.get("ARXIV_CATEGORIES", [])
    JOURNAL_FEEDS = user_profile.get("JOURNAL_FEEDS", {})
    JOURNAL_WEIGHT_0_10 = user_profile.get("JOURNAL_WEIGHT_0_10", {})
else:
    print(f"⚠️ User profile file {user_profile_file} not found.")


EMAIL_SUBJECT_PREFIX = "[Daily Research Digest]"

# =========================
# 1. DeepSeek API
# =========================

load_dotenv()
API_KEY = "YOUR_API_KEY"
# Obtain API from, e.g., https://madmodel.cs.tsinghua.edu.cn/ (Deepseek at Tsinghua)

def send_request(messages):
    url = 'https://madmodel.cs.tsinghua.edu.cn/v1/chat/completions'
    headers = {
        'Content-Type': 'application/json',
        'authorization': f'Bearer {API_KEY}'
    }
    data = {
        "model": "DeepSeek-R1-Distill-32B", # 设置模型
        "messages": messages, # 设置prompt
        "temperature": 0.6,
        "repetition_penalty": 1.2,
        "stream": False # stream = True 时启⽤流式传输
    }
    try:
    # 发送请求
        response = requests.post(
        url,
        headers=headers,
        json=data,
        timeout=60
        )
        return response.json() # 返回结果
    except Exception as e:
        return str(e)

# =========================
# 2. 抓 arXiv 新论文
# =========================

def fetch_arxiv(days=1, max_results=40):
    print("Fetching arXiv...")
    if len(ARXIV_CATEGORIES) == 0:
        print("  → No arXiv categories configured, skip.")
        return []
    query = " OR ".join(f"cat:{c}" for c in ARXIV_CATEGORIES)

    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )

    since = datetime.datetime.utcnow() - datetime.timedelta(days=days)
    papers = []

    for r in search.results():
        if r.published.replace(tzinfo=None) < since:
            continue
        papers.append({
            "source": "arXiv",
            "title": r.title.strip(),
            "abstract": r.summary.strip(),
            "url": r.entry_id
        })
    print(f"  → Found {len(papers)} arXiv entries.")
    return papers

def extract_arxiv_id(url: str):
    """
    arXiv entry_id like:
      https://arxiv.org/abs/2501.12345v2  or  .../abs/2501.12345
    We return 2501.12345 (without version).
    """
    if not url:
        return None
    m = re.search(r"arxiv\.org/abs/([^?/#]+)", url)
    if not m:
        return None
    arxiv_id = m.group(1)
    arxiv_id = arxiv_id.split("v")[0]  # drop version suffix
    return arxiv_id

def fetch_scirate_score(arxiv_id: str):
    """
    Returns integer scirate count or None.
    """
    if not arxiv_id:
        return None

    paper = client.paper(arxiv_id)
    val = paper.scites
    return val

def scirate_to_0_10(sc):
    if sc is None or sc <= 0:
        return 0.0
    return float(min(10.0, 5 * math.log10(sc + 1)))  # 只是示例


# =========================
# 3. 抓期刊 RSS
# =========================


def fetch_journals(max_results_per_journal=10):
    papers = []

    for journal, url in JOURNAL_FEEDS.items():
        print("Fetching journal feed:", journal)
        feed = feedparser.parse(url)
        for e in feed.entries[:max_results_per_journal]:
            papers.append({
                "source": journal,
                "title": e.title.strip(),
                "abstract": getattr(e, "summary", ""),
                "url": e.link
            })
        print(f"  → Found {len(feed.entries)} entries.")

    return papers


def get_journal_weight(source: str) -> int:
    return int(JOURNAL_WEIGHT_0_10.get(source, 6))

SEEN_DB_FILE = "seen_papers.json"

def load_seen():
    if os.path.exists(SEEN_DB_FILE):
        try:
            with open(SEEN_DB_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except:
            return set()
    return set()

def save_seen(seen_set):
    try:
        with open(SEEN_DB_FILE, "w", encoding="utf-8") as f:
            json.dump(sorted(list(seen_set)), f, ensure_ascii=False, indent=2)
    except:
        pass

def paper_uid(p):
    # arXiv 用 arxiv_id，否则用 url
    return p.get("arxiv_id") or p.get("url") or p.get("title")

# =========================
# 4. LLM 分析论文
# =========================

def extract_json_from_text(text: str):
    """
    Robustly extract the first JSON object from LLM output.
    Returns dict or raises ValueError.
    """
    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in text")

    json_str = text[start:end + 1]
    return json.loads(json_str)

def analyze_paper_structured(paper):
    prompt = f"""
    Return ONLY a valid JSON object (no markdown, no extra text) with keys:
    - "significance_0_10": number in [0,10], characterizing significance, pleace be critical
    - "relevance_0_10":  number in [0,10], characterizing relevance to my research, pleace be critical
    - "summary": a concise technical summary (<=120 words)
    - "why_relevant": why it matters for my research (<=120 words)

    My research profile:
    {RESEARCH_PROFILE}

    Paper:
    Source: {paper['source']}
    Title: {paper['title']}
    Abstract: {paper['abstract']}
    """
    # robust JSON parse
    try:
        responds = send_request(
            [
                {"role": "system", "content": "You are a senior theoretical physicist and careful JSON generator."},
                {"role": "user", "content": prompt},
            ]
        )

        text = responds["choices"][0]["message"]["content"]
        obj = extract_json_from_text(text)
        # normalize & guard
        significance_score = float(obj.get("significance_0_10", 0))
        relevance_score = float(obj.get("relevance_0_10", 0))
        summary = str(obj.get("summary", "")).strip()
        why = str(obj.get("why_relevant", "")).strip()
        return {
            "significance_0_10": significance_score,
            "relevance_0_10": relevance_score,
            "summary": summary,
            "why_relevant": why,
        }
    except Exception as e:
        # fallback：如果模型没按 JSON 输出，就给一个保守的结构
        return {
            "significance_0_10": 0,
            "relevance_0_10": 0,
            "summary": f"⚠️ Analysis failed：{e}",
            "why_relevant": "",
        }

def compute_scores(significance_0_10: float, relevance_0_10: float, journal_0_10: float):
    """
    三项打分 + 总分（0–10）
    你可以按偏好调权重。
    """
    w_significance, w_relevance, w_journal = 0.30, 0.40, 0.30
    total = w_significance * significance_0_10 + \
            w_relevance * relevance_0_10 + \
            w_journal * journal_0_10
    return {
        "significance_0_10": round(significance_0_10, 2),
        "relevance_0_10": round(relevance_0_10, 2),
        "journal_0_10": round(journal_0_10, 2),
        "total_0_10": round(total, 2),
    }

# =========================
# 5. 生成每日 Digest
# =========================
def html_escape(s: str) -> str:
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def build_digest_html(results):
    today = datetime.date.today().isoformat()
    parts = []
    parts.append(f"""\
        <html>
        <body style="font-family: Arial, Helvetica, sans-serif; line-height: 1.55; color: #111;">
            <h2 style="margin: 0 0 12px 0;">📚 Daily Research Digest ({today})</h2>
            <div style="color:#666; font-size: 13px; margin-bottom: 18px;">
            Sorted by Total score. (LLM / SciRate / Journal)
            </div>
    """)

    for r in results:
        s = r["scores"]
        llm = r["llm"]

        title = html_escape(r.get("title", ""))
        source = html_escape(r.get("source", ""))
        url = html_escape(r.get("url", ""))
        summary = html_escape(llm.get("summary", ""))
        why = html_escape(llm.get("why_relevant", "").strip())

        parts.append(f"""\
            <div style="border:1px solid #e6e6e6; border-radius:12px; padding:14px 16px; margin: 0 0 14px 0;">
            <div style="font-size: 16px; font-weight: 700; margin-bottom: 2px;">{title}</div>
            <div style="font-size: 13px; color:#444; margin-bottom: 2px;">
                <b>Source:</b> {source}
            </div>
            <div style="font-size: 13px; margin-bottom: 2px;">
                <b>Scores (0–10):</b>
                Significance={s['significance_0_10']}, Relevance={s['relevance_0_10']}, Journal={s['journal_0_10']}
                <b>Total={s['total_0_10']}</b>
            </div>
            <div style="font-size: 13px; margin-bottom: 2px;">
                <b>Summary:</b> {summary}
            </div>
        """)
        if why:
            parts.append(f"""\
                <div style="font-size: 13px; margin-bottom: 2px;">
                    <b>Why relevant:</b> {why}
                </div>
            """)
        parts.append(f"""\
            <div style="font-size: 13px;">
                🔗 <a href="{url}" target="_blank" rel="noreferrer">{url}</a>
            </div>
            </div>
        """)

    parts.append("""\
        </body>
        </html>
    """)

    return "".join(parts)


# =========================
# 6. 发邮件
# =========================

def send_email(content):
    yag = yagmail.SMTP(EMAIL_ADDRESS, EMAIL_PASSWORD)
    subject = f"{EMAIL_SUBJECT_PREFIX} {datetime.date.today().isoformat()}"
    try:
        yag.send(to=EMAIL_ADDRESS, subject=subject, contents=content)
    except: # save the email content to a local file if sending fails
        with open("email_failed.html", "w", encoding="utf-8") as f:
            f.write(content)
        print("⚠️ Failed to send email. Saved to email_failed.html")
        

# =========================
# 7. 主流程
# =========================

def work(i, p):
    print(f"🧠 [{i}] Analyzing:", p["title"])
    # 1) SciRate (only meaningful for arXiv links)
    arxiv_id = extract_arxiv_id(p.get("url", ""))
    if arxiv_id:
        sc_count = fetch_scirate_score(arxiv_id) if arxiv_id else None
        j_0_10 = scirate_to_0_10(sc_count)
    else:
        j_0_10 = float(get_journal_weight(p.get("source", "")))

    # 3) LLM structured relevance + summary
    llm_obj = analyze_paper_structured(p)

    scores = compute_scores(
        significance_0_10=float(llm_obj["significance_0_10"]),
        relevance_0_10=float(llm_obj["relevance_0_10"]),
        journal_0_10=j_0_10
    )

    result = {
        **p,
        "arxiv_id": arxiv_id,
        "llm": llm_obj,
        "scores": scores,
    }
    return result

def main():
    print("🔍 Fetching papers...")

    papers = []
    papers.extend(fetch_arxiv(days=5, max_results=100))
    papers.extend(fetch_journals(max_results_per_journal=5))

    print(f"📄 Found {len(papers)} papers")


    seen = load_seen()

    # 基础去重（按 url 优先）
    uniq = {}
    for p in papers:
        key = p.get("url") or p.get("title")
        if key and key not in uniq:
            uniq[key] = p
    papers = list(uniq.values())

    # 过滤已看过
    new_papers = []
    for p in papers:
        uid = p.get("url") or p.get("title")
        if uid in seen:
            continue
        new_papers.append(p)

    papers = new_papers
    print(f"🆕 New papers after seen-filter: {len(papers)}")

    if not papers:
        print("✅ No new papers today. Skip emailing.")
        return

    results = Parallel(n_jobs=64)(
        delayed(work)(i, p) for i, p in enumerate(papers)
    )
    results = sorted(results, key=lambda x: x["scores"]["total_0_10"], reverse=True)
    results_filtered = [r for r in results if r["scores"]["total_0_10"] >= 6.0]
    if len(results_filtered) > 10:
        results_filtered = results_filtered[:10]  # 至多发10篇


    digest = build_digest_html(results_filtered)

    print("📧 Sending email...")
    send_email(digest)

    print("✅ Done!")

    for r in results_filtered:
        seen.add(r.get("url") or r.get("title"))
    save_seen(seen)

if __name__ == "__main__":
    main()
    
