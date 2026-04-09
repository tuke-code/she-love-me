"""
generate_html_report.py - 生成 HTML 报告

读取 stats.json + analysis.json，生成现代风格的分析报告
设计风格：Spotify Wrapped 风格 - 深色底、大字排版、渐变色、现代卡片
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime

# Windows 控制台 UTF-8 输出
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_chart_data(stats):
    trend = stats.get("daily_trend", [])
    trend_labels = [d["date"] for d in trend[-60:]]
    trend_data = [d["count"] for d in trend[-60:]]

    hours = stats.get("active_hours", {})
    hour_labels = [f"{i}" for i in range(24)]
    hour_data = [hours.get(str(i), 0) for i in range(24)]

    basic = stats.get("basic", {})
    pie_data = [basic.get("my_messages", 0), basic.get("their_messages", 0)]

    return {
        "trend_labels": trend_labels,
        "trend_data": trend_data,
        "hour_labels": hour_labels,
        "hour_data": hour_data,
        "pie_data": pie_data,
    }


def escape_html(s):
    if not isinstance(s, str):
        s = str(s)
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def render_danger_warnings(danger_warnings):
    if not danger_warnings:
        return '<p style="color:var(--text-subtle);font-size:13px;">本次鉴定未发现明显危险信号</p>'

    level_colors = {
        "极高危": ("#ef4444", "rgba(239,68,68,.12)", "rgba(239,68,68,.25)"),
        "高危":   ("#f97316", "rgba(249,115,22,.12)", "rgba(249,115,22,.25)"),
        "中危":   ("#eab308", "rgba(234,179,8,.12)",  "rgba(234,179,8,.25)"),
        "低危":   ("#22c55e", "rgba(34,197,94,.12)",  "rgba(34,197,94,.25)"),
    }

    items = []
    for w in danger_warnings:
        wtype   = escape_html(w.get("type", ""))
        level   = w.get("level", "中危")
        evidence = escape_html(w.get("evidence", ""))
        color, bg, border = level_colors.get(level, ("#6b7280", "rgba(107,114,128,.12)", "rgba(107,114,128,.25)"))
        items.append(f"""
        <div class="warning-card" style="border-color:{border};background:{bg};">
          <div class="warning-header">
            <span class="warning-type">{wtype}</span>
            <span class="warning-badge" style="color:{color};background:{bg};border-color:{border};">{level}</span>
          </div>
          <p class="warning-evidence">{evidence}</p>
        </div>""")
    return "\n".join(items)


def render_sternberg(sternberg):
    passion    = sternberg.get("passion", 0)
    intimacy   = sternberg.get("intimacy", 0)
    commitment = sternberg.get("commitment", 0)
    love_type  = escape_html(sternberg.get("love_type", ""))
    return f"""
    <div class="sternberg-wrap">
      <div class="sternberg-row">
        <span class="sternberg-label">激情 Passion</span>
        <div class="sternberg-track"><div class="sternberg-fill s-passion" style="width:{passion}%"></div></div>
        <span class="sternberg-val">{passion}</span>
      </div>
      <div class="sternberg-row">
        <span class="sternberg-label">亲密 Intimacy</span>
        <div class="sternberg-track"><div class="sternberg-fill s-intimacy" style="width:{intimacy}%"></div></div>
        <span class="sternberg-val">{intimacy}</span>
      </div>
      <div class="sternberg-row">
        <span class="sternberg-label">承诺 Commitment</span>
        <div class="sternberg-track"><div class="sternberg-fill s-commitment" style="width:{commitment}%"></div></div>
        <span class="sternberg-val">{commitment}</span>
      </div>
      <div class="sternberg-type">→ {love_type}</div>
    </div>"""


def render_gottman(gottman):
    ratio    = gottman.get("positive_negative_ratio", 0)
    horsemen = gottman.get("horsemen_detected", [])
    risk     = escape_html(gottman.get("risk_level", ""))
    ratio_pct = min(int(ratio / 10 * 100), 100)

    horsemen_chips = "".join(
        f'<span class="horseman-chip">{escape_html(h)}</span>' for h in horsemen
    )
    if not horsemen_chips:
        horsemen_chips = '<span style="color:var(--text-subtle);font-size:12px;">未检测到四骑士信号</span>'

    risk_color = {"高危": "#ef4444", "中危": "#eab308", "低危": "#22c55e"}.get(risk, "#6b7280")

    return f"""
    <div class="gottman-wrap">
      <div class="gottman-ratio-row">
        <div>
          <div class="gottman-ratio-val">{ratio}<span style="font-size:.5em;font-weight:500;color:var(--text-muted)">:1</span></div>
          <div class="gottman-ratio-label">正负互动比（健康值 ≥ 5:1）</div>
        </div>
        <div class="gottman-risk-badge" style="color:{risk_color};border-color:{risk_color}22;background:{risk_color}11;">{risk}</div>
      </div>
      <div class="gottman-bar-track"><div class="gottman-bar-fill" style="width:{ratio_pct}%;background:{risk_color};"></div></div>
      <div class="gottman-horsemen-label">四骑士检测</div>
      <div class="gottman-horsemen">{horsemen_chips}</div>
    </div>"""


def render_personality(personality, contact_name):
    user_att    = escape_html(personality.get("user_attachment", ""))
    partner_att = escape_html(personality.get("partner_attachment", ""))
    user_comm   = escape_html(personality.get("user_communication", ""))
    partner_comm = escape_html(personality.get("partner_communication", ""))
    user_lang   = escape_html(personality.get("user_love_language", ""))
    partner_lang = escape_html(personality.get("partner_love_language", ""))
    pursue_dist = personality.get("pursue_distance_cycle", False)
    lang_mismatch = personality.get("love_language_mismatch", False)

    pursue_html = ""
    if pursue_dist:
        pursue_html = """
      <div class="pursue-alert">
        ⚠️ <strong>追逃循环已形成</strong>：你越追，TA越逃；TA越逃，你越焦虑——负向循环持续强化。
      </div>"""

    lang_mismatch_html = ""
    if lang_mismatch:
        lang_mismatch_html = """
      <div class="lang-mismatch-alert">
        💬 <strong>爱的语言不匹配</strong>：你们表达爱的方式不同，导致给予了但对方感受不到。
      </div>"""

    return f"""
    <div class="personality-table">
      <div class="pt-row pt-header">
        <div class="pt-cell"></div>
        <div class="pt-cell pt-you">你</div>
        <div class="pt-cell pt-them">{escape_html(contact_name)}</div>
      </div>
      <div class="pt-row">
        <div class="pt-cell pt-label">依恋类型</div>
        <div class="pt-cell">{user_att}</div>
        <div class="pt-cell">{partner_att}</div>
      </div>
      <div class="pt-row">
        <div class="pt-cell pt-label">沟通风格</div>
        <div class="pt-cell">{user_comm}</div>
        <div class="pt-cell">{partner_comm}</div>
      </div>
      <div class="pt-row">
        <div class="pt-cell pt-label">爱的语言</div>
        <div class="pt-cell">{user_lang}</div>
        <div class="pt-cell">{partner_lang}</div>
      </div>
    </div>
    {pursue_html}
    {lang_mismatch_html}"""


def render_strategist(strategist):
    core    = escape_html(strategist.get("core_problem", ""))
    stops   = strategist.get("stop_doing", [])
    starts  = strategist.get("start_doing", [])
    roadmap = escape_html(strategist.get("roadmap", ""))

    stops_html  = "\n".join(f'<li class="strategy-stop-item">❌ {escape_html(s)}</li>'  for s in stops)
    starts_html = "\n".join(f'<li class="strategy-start-item">✅ {escape_html(s)}</li>' for s in starts)

    return f"""
    <div class="strategist-wrap">
      <div class="core-problem-card">
        <div class="core-problem-label">核心问题</div>
        <p class="core-problem-text">{core}</p>
      </div>
      <div class="strategy-grid">
        <div class="strategy-col">
          <div class="strategy-col-title stop-title">立即停止</div>
          <ul class="strategy-list">{stops_html}</ul>
        </div>
        <div class="strategy-col">
          <div class="strategy-col-title start-title">立即开始</div>
          <ul class="strategy-list">{starts_html}</ul>
        </div>
      </div>
      <div class="roadmap-card">
        <div class="roadmap-label">推进路线图</div>
        <p class="roadmap-text">{roadmap}</p>
      </div>
    </div>"""


def render_key_findings(key_findings):
    if not key_findings:
        return '<p style="color:var(--text-subtle);font-size:13px;">暂无鉴定发现</p>'

    items = []
    for i, f in enumerate(key_findings):
        title    = escape_html(f.get("title", f"发现{i+1}"))
        quote    = escape_html(f.get("quote", ""))
        analysis = escape_html(f.get("analysis", ""))
        items.append(f"""
        <div class="finding-card">
          <div class="finding-index">{i+1:02d}</div>
          <div class="finding-body">
            <div class="finding-title">{title}</div>
            {f'<blockquote class="finding-quote">「{quote}」</blockquote>' if quote else ''}
            <p class="finding-analysis">{analysis}</p>
          </div>
        </div>""")
    return "\n".join(items)


def render_html(stats, analysis, contact_name):
    scores    = stats.get("scores", {})
    simp      = scores.get("simp_index", 0)
    loved     = scores.get("loved_index", 0)
    cold      = scores.get("cold_index", 0)
    basic     = stats.get("basic", {})
    initiative = stats.get("initiative", {})
    reply     = stats.get("reply_speed", {})
    bombing   = stats.get("bombing", {})
    goodnight = stats.get("goodnight", {})
    msg_len   = stats.get("message_length", {})

    relationship_type  = escape_html(analysis.get("relationship_type", "未知"))
    relationship_label = escape_html(analysis.get("relationship_label", ""))
    relationship_trend = escape_html(analysis.get("relationship_trend", ""))
    verdict            = escape_html(analysis.get("verdict", ""))

    danger_warnings_html = render_danger_warnings(analysis.get("danger_warnings", []))
    sternberg_html       = render_sternberg(analysis.get("sternberg", {}))
    gottman_html         = render_gottman(analysis.get("gottman", {}))
    personality_html     = render_personality(analysis.get("personality", {}), contact_name)
    strategist_html      = render_strategist(analysis.get("strategist", {}))
    findings_html        = render_key_findings(analysis.get("key_findings", []))

    chart = build_chart_data(stats)
    chart_data_js = json.dumps(chart, ensure_ascii=False)
    date_str = datetime.now().strftime("%Y.%m.%d")

    date_range = basic.get("date_range", ["?", "?"])
    total_days = basic.get("total_days", 1)
    my_ratio   = int(basic.get("my_ratio", 0) * 100)
    their_ratio = int(basic.get("their_ratio", 0) * 100)
    speed_ratio = reply.get("speed_ratio", 1)

    trend_icon = {"升温中": "🔥", "平稳维持": "➡️", "逐渐降温": "❄️", "已经凉透": "💀"}.get(
        analysis.get("relationship_trend", ""), "📊"
    )

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>她爱你吗 · {escape_html(contact_name)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  :root {{
    --bg: #0a0a0f;
    --surface: #111118;
    --surface-2: #18181f;
    --border: rgba(255,255,255,0.06);
    --border-hover: rgba(255,255,255,0.12);
    --text: #f0f0f5;
    --text-muted: #6b6b80;
    --text-subtle: #3a3a4a;
    --accent-1: #a855f7;
    --accent-2: #ec4899;
    --accent-3: #3b82f6;
    --accent-warm: #f59e0b;
    --grad-love: linear-gradient(135deg, #a855f7, #ec4899);
    --grad-simp: linear-gradient(135deg, #f59e0b, #ef4444);
    --grad-cold: linear-gradient(135deg, #3b82f6, #06b6d4);
    --radius: 16px;
    --radius-sm: 10px;
  }}

  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

  body {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    -webkit-font-smoothing: antialiased;
  }}

  /* ── Hero ── */
  .hero {{
    position: relative;
    overflow: hidden;
    padding: 80px 24px 64px;
    text-align: center;
    border-bottom: 1px solid var(--border);
  }}
  .hero::before {{
    content: '';
    position: absolute;
    inset: 0;
    background:
      radial-gradient(ellipse 60% 50% at 30% 0%, rgba(168,85,247,.18) 0%, transparent 70%),
      radial-gradient(ellipse 60% 50% at 70% 0%, rgba(236,72,153,.18) 0%, transparent 70%);
    pointer-events: none;
  }}
  .hero-eyebrow {{
    font-size: 11px;
    font-weight: 600;
    letter-spacing: .15em;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-bottom: 20px;
  }}
  .hero-title {{
    font-size: clamp(48px, 10vw, 96px);
    font-weight: 900;
    line-height: 1;
    letter-spacing: -.03em;
    background: var(--grad-love);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 16px;
  }}
  .hero-contact {{
    font-size: 20px;
    font-weight: 500;
    color: var(--text-muted);
    margin-bottom: 8px;
  }}
  .hero-contact span {{ color: var(--text); font-weight: 700; }}
  .hero-date {{ font-size: 13px; color: var(--text-subtle); }}

  /* ── Layout ── */
  .container {{ max-width: 960px; margin: 0 auto; padding: 48px 24px 80px; }}
  .section {{ margin-bottom: 64px; }}
  .section-label {{
    font-size: 11px;
    font-weight: 600;
    letter-spacing: .12em;
    text-transform: uppercase;
    color: var(--text-subtle);
    margin-bottom: 20px;
  }}

  /* ── Score Hero Cards ── */
  .score-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }}
  .score-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 28px 20px;
    text-align: center;
    position: relative;
    overflow: hidden;
    transition: border-color .2s;
  }}
  .score-card:hover {{ border-color: var(--border-hover); }}
  .score-card::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
  }}
  .score-card.simp::before {{ background: var(--grad-simp); }}
  .score-card.loved::before {{ background: var(--grad-love); }}
  .score-card.cold::before {{ background: var(--grad-cold); }}
  .score-emoji {{ font-size: 24px; margin-bottom: 12px; }}
  .score-label {{ font-size: 11px; font-weight: 600; color: var(--text-muted); letter-spacing: .08em; text-transform: uppercase; margin-bottom: 8px; }}
  .score-value {{ font-size: 56px; font-weight: 900; line-height: 1; letter-spacing: -.04em; }}
  .score-card.simp .score-value {{ background: var(--grad-simp); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }}
  .score-card.loved .score-value {{ background: var(--grad-love); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }}
  .score-card.cold .score-value {{ background: var(--grad-cold); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }}
  .score-bar {{
    margin-top: 16px;
    height: 3px;
    background: var(--surface-2);
    border-radius: 99px;
    overflow: hidden;
  }}
  .score-bar-fill {{ height: 100%; border-radius: 99px; }}
  .score-card.simp .score-bar-fill {{ background: var(--grad-simp); }}
  .score-card.loved .score-bar-fill {{ background: var(--grad-love); }}
  .score-card.cold .score-bar-fill {{ background: var(--grad-cold); }}

  /* ── 成分表 ── */
  .ingredient-list {{ display: flex; flex-direction: column; gap: 14px; }}
  .ingredient-row {{
    display: grid;
    grid-template-columns: 110px 1fr 52px;
    align-items: center;
    gap: 14px;
  }}
  .ingredient-name {{ font-size: 13px; font-weight: 500; color: var(--text-muted); }}
  .ingredient-track {{
    height: 6px;
    background: var(--surface-2);
    border-radius: 99px;
    overflow: hidden;
  }}
  .ingredient-fill {{ height: 100%; border-radius: 99px; }}
  .i-simp {{ background: var(--grad-simp); }}
  .i-loved {{ background: var(--grad-love); }}
  .i-cold {{ background: var(--grad-cold); }}
  .i-tool {{ background: linear-gradient(90deg, #374151, #6b7280); }}
  .ingredient-pct {{ font-size: 14px; font-weight: 700; text-align: right; }}

  /* ── Stat Grid ── */
  .stat-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }}
  @media(min-width:640px) {{ .stat-grid {{ grid-template-columns: repeat(4, 1fr); }} }}
  .stat-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 20px 16px;
    transition: border-color .2s;
  }}
  .stat-card:hover {{ border-color: var(--border-hover); }}
  .stat-meta {{ font-size: 11px; font-weight: 500; color: var(--text-subtle); letter-spacing: .05em; text-transform: uppercase; margin-bottom: 10px; }}
  .stat-main {{ font-size: 28px; font-weight: 800; letter-spacing: -.02em; line-height: 1; }}
  .stat-sub {{ font-size: 11px; color: var(--text-muted); margin-top: 6px; line-height: 1.5; }}

  /* ── Compare Bars ── */
  .compare-list {{ display: flex; flex-direction: column; gap: 20px; }}
  .compare-row {{ }}
  .compare-header {{
    display: flex;
    justify-content: space-between;
    font-size: 12px;
    font-weight: 600;
    color: var(--text-muted);
    margin-bottom: 8px;
  }}
  .compare-track {{
    position: relative;
    height: 8px;
    background: var(--surface-2);
    border-radius: 99px;
    overflow: hidden;
  }}
  .compare-you {{
    position: absolute;
    left: 0; top: 0; bottom: 0;
    border-radius: 99px;
    background: var(--grad-simp);
  }}
  .compare-them {{
    position: absolute;
    right: 0; top: 0; bottom: 0;
    border-radius: 99px;
    background: var(--grad-love);
  }}

  /* ── Danger Warnings ── */
  .warning-card {{
    border: 1px solid;
    border-radius: var(--radius-sm);
    padding: 18px 20px;
    margin-bottom: 12px;
  }}
  .warning-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
  }}
  .warning-type {{
    font-size: 14px;
    font-weight: 700;
    color: var(--text);
  }}
  .warning-badge {{
    font-size: 11px;
    font-weight: 700;
    border: 1px solid;
    border-radius: 99px;
    padding: 3px 10px;
    letter-spacing: .06em;
  }}
  .warning-evidence {{
    font-size: 13px;
    line-height: 1.7;
    color: var(--text-muted);
  }}

  /* ── Sternberg ── */
  .sternberg-wrap {{ display: flex; flex-direction: column; gap: 16px; }}
  .sternberg-row {{
    display: grid;
    grid-template-columns: 130px 1fr 40px;
    align-items: center;
    gap: 14px;
  }}
  .sternberg-label {{ font-size: 12px; font-weight: 600; color: var(--text-muted); }}
  .sternberg-track {{
    height: 8px;
    background: var(--surface-2);
    border-radius: 99px;
    overflow: hidden;
  }}
  .sternberg-fill {{ height: 100%; border-radius: 99px; }}
  .s-passion    {{ background: linear-gradient(90deg, #ec4899, #f97316); }}
  .s-intimacy   {{ background: linear-gradient(90deg, #a855f7, #3b82f6); }}
  .s-commitment {{ background: linear-gradient(90deg, #22c55e, #06b6d4); }}
  .sternberg-val {{ font-size: 14px; font-weight: 700; text-align: right; color: var(--text-muted); }}
  .sternberg-type {{
    margin-top: 8px;
    font-size: 14px;
    font-weight: 600;
    color: var(--accent-1);
    padding: 10px 16px;
    background: rgba(168,85,247,.08);
    border: 1px solid rgba(168,85,247,.15);
    border-radius: var(--radius-sm);
  }}

  /* ── Gottman ── */
  .gottman-wrap {{ display: flex; flex-direction: column; gap: 14px; }}
  .gottman-ratio-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}
  .gottman-ratio-val {{
    font-size: 40px;
    font-weight: 900;
    letter-spacing: -.03em;
    color: var(--text);
  }}
  .gottman-ratio-label {{ font-size: 11px; color: var(--text-muted); margin-top: 4px; }}
  .gottman-risk-badge {{
    font-size: 12px;
    font-weight: 700;
    border: 1px solid;
    border-radius: 99px;
    padding: 6px 14px;
    letter-spacing: .06em;
  }}
  .gottman-bar-track {{
    height: 6px;
    background: var(--surface-2);
    border-radius: 99px;
    overflow: hidden;
  }}
  .gottman-bar-fill {{ height: 100%; border-radius: 99px; }}
  .gottman-horsemen-label {{ font-size: 11px; font-weight: 600; color: var(--text-subtle); letter-spacing: .08em; text-transform: uppercase; margin-top: 4px; }}
  .gottman-horsemen {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 4px; }}
  .horseman-chip {{
    font-size: 12px;
    font-weight: 600;
    color: #ef4444;
    background: rgba(239,68,68,.1);
    border: 1px solid rgba(239,68,68,.2);
    border-radius: 99px;
    padding: 4px 12px;
  }}

  /* ── Personality Table ── */
  .personality-table {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    overflow: hidden;
    margin-bottom: 16px;
  }}
  .pt-row {{
    display: grid;
    grid-template-columns: 90px 1fr 1fr;
    border-bottom: 1px solid var(--border);
  }}
  .pt-row:last-child {{ border-bottom: none; }}
  .pt-cell {{
    padding: 14px 16px;
    font-size: 13px;
    color: var(--text-muted);
    border-right: 1px solid var(--border);
  }}
  .pt-cell:last-child {{ border-right: none; }}
  .pt-header .pt-cell {{ font-size: 11px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: var(--text-subtle); }}
  .pt-you   {{ color: #f59e0b !important; font-weight: 600; }}
  .pt-them  {{ color: #a855f7 !important; font-weight: 600; }}
  .pt-label {{ font-weight: 600; color: var(--text-subtle) !important; font-size: 11px !important; text-transform: uppercase; letter-spacing: .06em; }}
  .pursue-alert {{
    font-size: 13px;
    line-height: 1.7;
    color: #f97316;
    background: rgba(249,115,22,.08);
    border: 1px solid rgba(249,115,22,.2);
    border-radius: var(--radius-sm);
    padding: 14px 16px;
    margin-bottom: 12px;
  }}
  .lang-mismatch-alert {{
    font-size: 13px;
    line-height: 1.7;
    color: #eab308;
    background: rgba(234,179,8,.08);
    border: 1px solid rgba(234,179,8,.2);
    border-radius: var(--radius-sm);
    padding: 14px 16px;
  }}

  /* ── Strategist ── */
  .strategist-wrap {{ display: flex; flex-direction: column; gap: 16px; }}
  .core-problem-card {{
    background: rgba(168,85,247,.06);
    border: 1px solid rgba(168,85,247,.15);
    border-radius: var(--radius-sm);
    padding: 20px;
  }}
  .core-problem-label {{ font-size: 11px; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; color: var(--accent-1); margin-bottom: 10px; }}
  .core-problem-text {{ font-size: 14px; line-height: 1.8; color: var(--text-muted); }}
  .strategy-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
  @media(max-width:560px) {{ .strategy-grid {{ grid-template-columns: 1fr; }} }}
  .strategy-col {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 18px;
  }}
  .strategy-col-title {{ font-size: 11px; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; margin-bottom: 14px; }}
  .stop-title  {{ color: #ef4444; }}
  .start-title {{ color: #22c55e; }}
  .strategy-list {{ list-style: none; display: flex; flex-direction: column; gap: 10px; }}
  .strategy-stop-item,
  .strategy-start-item {{ font-size: 13px; line-height: 1.7; color: var(--text-muted); }}
  .roadmap-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 20px;
  }}
  .roadmap-label {{ font-size: 11px; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; color: var(--accent-3); margin-bottom: 10px; }}
  .roadmap-text {{ font-size: 14px; line-height: 1.9; color: var(--text-muted); }}

  /* ── Findings ── */
  .findings-list {{ display: flex; flex-direction: column; gap: 12px; }}
  .finding-card {{
    display: grid;
    grid-template-columns: 40px 1fr;
    gap: 16px;
    align-items: start;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 20px;
    transition: border-color .2s;
  }}
  .finding-card:hover {{ border-color: var(--border-hover); }}
  .finding-index {{
    font-size: 11px;
    font-weight: 700;
    color: var(--text-subtle);
    font-variant-numeric: tabular-nums;
    letter-spacing: .05em;
    padding-top: 2px;
  }}
  .finding-title {{ font-size: 14px; font-weight: 700; color: var(--text); margin-bottom: 10px; }}
  .finding-quote {{
    font-size: 13px;
    font-style: italic;
    color: var(--accent-1);
    border-left: 2px solid rgba(168,85,247,.4);
    padding-left: 12px;
    margin-bottom: 10px;
    line-height: 1.6;
  }}
  .finding-analysis {{ font-size: 13px; line-height: 1.7; color: var(--text-muted); }}

  /* ── Verdict ── */
  .verdict-card {{
    position: relative;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 48px 40px;
    text-align: center;
    overflow: hidden;
  }}
  .verdict-card::before {{
    content: '';
    position: absolute;
    inset: 0;
    background: radial-gradient(ellipse 80% 60% at 50% 100%, rgba(168,85,247,.08) 0%, transparent 70%);
    pointer-events: none;
  }}
  .verdict-meta-row {{
    display: flex;
    justify-content: center;
    gap: 10px;
    flex-wrap: wrap;
    margin-bottom: 20px;
  }}
  .verdict-type-badge {{
    display: inline-block;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: .12em;
    text-transform: uppercase;
    color: var(--accent-1);
    background: rgba(168,85,247,.12);
    border: 1px solid rgba(168,85,247,.2);
    border-radius: 99px;
    padding: 6px 14px;
  }}
  .verdict-trend-badge {{
    display: inline-block;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: .08em;
    color: var(--text-muted);
    background: var(--surface-2);
    border: 1px solid var(--border);
    border-radius: 99px;
    padding: 6px 14px;
  }}
  .verdict-type {{
    font-size: clamp(32px, 6vw, 52px);
    font-weight: 900;
    letter-spacing: -.03em;
    background: var(--grad-love);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 8px;
  }}
  .verdict-label {{
    font-size: 15px;
    color: var(--text-muted);
    margin-bottom: 28px;
  }}
  .verdict-divider {{
    width: 40px;
    height: 1px;
    background: var(--border);
    margin: 0 auto 28px;
  }}
  .verdict-text {{
    font-size: 16px;
    line-height: 1.8;
    color: var(--text-muted);
    max-width: 600px;
    margin: 0 auto;
  }}

  /* ── Charts ── */
  .chart-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 28px;
  }}
  .chart-title {{ font-size: 13px; font-weight: 600; color: var(--text-muted); margin-bottom: 20px; }}
  .chart-wrap {{ position: relative; height: 180px; }}
  .charts-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}

  /* ── Analysis Row ── */
  .analysis-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
  @media(max-width:560px) {{ .analysis-row {{ grid-template-columns: 1fr; }} }}
  .analysis-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 24px;
  }}
  .analysis-card-title {{
    font-size: 11px;
    font-weight: 700;
    letter-spacing: .1em;
    text-transform: uppercase;
    color: var(--text-subtle);
    margin-bottom: 16px;
  }}

  /* ── Footer ── */
  .footer {{
    text-align: center;
    padding: 32px 24px;
    font-size: 11px;
    color: var(--text-subtle);
    border-top: 1px solid var(--border);
    letter-spacing: .03em;
  }}

  @media (max-width: 500px) {{
    .score-grid {{ grid-template-columns: 1fr; }}
    .charts-row {{ grid-template-columns: 1fr; }}
    .ingredient-row {{ grid-template-columns: 90px 1fr 40px; }}
    .verdict-card {{ padding: 32px 20px; }}
    .analysis-row {{ grid-template-columns: 1fr; }}
  }}
</style>
</head>
<body>

<!-- Hero -->
<header class="hero">
  <p class="hero-eyebrow">舔狗鉴定所 · 聊天记录分析报告</p>
  <h1 class="hero-title">她爱你吗？</h1>
  <p class="hero-contact">与 <span>{escape_html(contact_name)}</span> 的聊天记录</p>
  <p class="hero-date">{date_range[0]} — {date_range[1]} · {total_days} 天 · {basic.get('total_messages', 0):,} 条消息</p>
</header>

<main class="container">

  <!-- 三大指数 -->
  <section class="section">
    <p class="section-label">鉴定指数</p>
    <div class="score-grid">
      <div class="score-card simp">
        <div class="score-emoji">🐶</div>
        <div class="score-label">舔狗指数</div>
        <div class="score-value">{simp}</div>
        <div class="score-bar"><div class="score-bar-fill" style="width:{simp}%"></div></div>
      </div>
      <div class="score-card loved">
        <div class="score-emoji">💜</div>
        <div class="score-label">被爱指数</div>
        <div class="score-value">{loved}</div>
        <div class="score-bar"><div class="score-bar-fill" style="width:{loved}%"></div></div>
      </div>
      <div class="score-card cold">
        <div class="score-emoji">🧊</div>
        <div class="score-label">冷淡指数</div>
        <div class="score-value">{cold}</div>
        <div class="score-bar"><div class="score-bar-fill" style="width:{cold}%"></div></div>
      </div>
    </div>
  </section>

  <!-- 恋爱成分表 -->
  <section class="section">
    <p class="section-label">恋爱成分表</p>
    <div class="ingredient-list">
      <div class="ingredient-row">
        <span class="ingredient-name">🐶 舔犬成分</span>
        <div class="ingredient-track"><div class="ingredient-fill i-simp" style="width:{simp}%"></div></div>
        <span class="ingredient-pct">{simp}%</span>
      </div>
      <div class="ingredient-row">
        <span class="ingredient-name">💜 被爱成分</span>
        <div class="ingredient-track"><div class="ingredient-fill i-loved" style="width:{loved}%"></div></div>
        <span class="ingredient-pct">{loved}%</span>
      </div>
      <div class="ingredient-row">
        <span class="ingredient-name">🧊 冷淡成分</span>
        <div class="ingredient-track"><div class="ingredient-fill i-cold" style="width:{cold}%"></div></div>
        <span class="ingredient-pct">{cold}%</span>
      </div>
      <div class="ingredient-row">
        <span class="ingredient-name">🔧 工具人成分</span>
        <div class="ingredient-track"><div class="ingredient-fill i-tool" style="width:{max(0, simp - loved - 10)}%"></div></div>
        <span class="ingredient-pct">{max(0, simp - loved - 10)}%</span>
      </div>
    </div>
  </section>

  <!-- 关键数据 -->
  <section class="section">
    <p class="section-label">关键数据</p>
    <div class="stat-grid">
      <div class="stat-card">
        <div class="stat-meta">消息占比</div>
        <div class="stat-main">{my_ratio}<span style="font-size:.5em;font-weight:500;color:var(--text-muted)">%</span></div>
        <div class="stat-sub">你 · 对方 {their_ratio}%</div>
      </div>
      <div class="stat-card">
        <div class="stat-meta">主动发起</div>
        <div class="stat-main">{initiative.get('my_starts', 0)}<span style="font-size:.4em;font-weight:500;color:var(--text-muted)"> 次</span></div>
        <div class="stat-sub">对方 {initiative.get('their_starts', 0)} 次</div>
      </div>
      <div class="stat-card">
        <div class="stat-meta">你的回复速度</div>
        <div class="stat-main" style="font-size:20px;font-weight:800">{reply.get('my_avg_human', 'N/A')}</div>
        <div class="stat-sub">对方 {reply.get('their_avg_human', 'N/A')}</div>
      </div>
      <div class="stat-card">
        <div class="stat-meta">回速差距</div>
        <div class="stat-main">{speed_ratio}<span style="font-size:.45em;font-weight:500;color:var(--text-muted)">x</span></div>
        <div class="stat-sub">对方比你慢这么多倍</div>
      </div>
      <div class="stat-card">
        <div class="stat-meta">你的轰炸次数</div>
        <div class="stat-main">{bombing.get('my_bomb_count', 0)}</div>
        <div class="stat-sub">最多连发 {bombing.get('my_max_consecutive', 0)} 条</div>
      </div>
      <div class="stat-card">
        <div class="stat-meta">先说晚安</div>
        <div class="stat-main">{goodnight.get('my_goodnight', 0)}<span style="font-size:.4em;font-weight:500;color:var(--text-muted)"> 次</span></div>
        <div class="stat-sub">对方先说 {goodnight.get('their_goodnight', 0)} 次</div>
      </div>
      <div class="stat-card">
        <div class="stat-meta">你的平均字数</div>
        <div class="stat-main">{msg_len.get('my_avg_chars', 0)}<span style="font-size:.4em;font-weight:500;color:var(--text-muted)"> 字</span></div>
        <div class="stat-sub">对方 {msg_len.get('their_avg_chars', 0)} 字</div>
      </div>
      <div class="stat-card">
        <div class="stat-meta">日均消息</div>
        <div class="stat-main">{basic.get('avg_daily', 0)}</div>
        <div class="stat-sub">条 / 天</div>
      </div>
    </div>
  </section>

  <!-- 对比分析 -->
  <section class="section">
    <p class="section-label">双方对比</p>
    <div class="compare-list">
      <div class="compare-row">
        <div class="compare-header">
          <span>你 · 消息量 {my_ratio}%</span>
          <span>{their_ratio}% · 对方</span>
        </div>
        <div class="compare-track">
          <div class="compare-you" style="width:{my_ratio}%"></div>
          <div class="compare-them" style="width:{their_ratio}%"></div>
        </div>
      </div>
      <div class="compare-row">
        <div class="compare-header">
          <span>你 · 主动发起 {initiative.get('my_starts', 0)}次</span>
          <span>{initiative.get('their_starts', 0)}次 · 对方</span>
        </div>
        <div class="compare-track">
          <div class="compare-you" style="width:{int(initiative.get('my_starts',0)/(max(initiative.get('my_starts',0)+initiative.get('their_starts',0),1))*100)}%"></div>
          <div class="compare-them" style="width:{int(initiative.get('their_starts',0)/(max(initiative.get('my_starts',0)+initiative.get('their_starts',0),1))*100)}%"></div>
        </div>
      </div>
      <div class="compare-row">
        <div class="compare-header">
          <span>你 · 先说晚安 {goodnight.get('my_goodnight', 0)}次</span>
          <span>{goodnight.get('their_goodnight', 0)}次 · 对方</span>
        </div>
        <div class="compare-track">
          <div class="compare-you" style="width:{int(goodnight.get('my_goodnight',0)/(max(goodnight.get('my_goodnight',0)+goodnight.get('their_goodnight',0),1))*100)}%"></div>
          <div class="compare-them" style="width:{int(goodnight.get('their_goodnight',0)/(max(goodnight.get('my_goodnight',0)+goodnight.get('their_goodnight',0),1))*100)}%"></div>
        </div>
      </div>
    </div>
  </section>

  <!-- 趋势图表 -->
  <section class="section">
    <p class="section-label">数据可视化</p>
    <div class="chart-card" style="margin-bottom:12px">
      <div class="chart-title">消息趋势（最近60天）</div>
      <div class="chart-wrap"><canvas id="trendChart"></canvas></div>
    </div>
    <div class="charts-row">
      <div class="chart-card">
        <div class="chart-title">活跃时段分布</div>
        <div class="chart-wrap"><canvas id="hourChart"></canvas></div>
      </div>
      <div class="chart-card">
        <div class="chart-title">消息占比</div>
        <div class="chart-wrap"><canvas id="pieChart"></canvas></div>
      </div>
    </div>
  </section>

  <!-- ⚠️ 危险预警 -->
  <section class="section">
    <p class="section-label">⚠️ 危险预警</p>
    {danger_warnings_html}
  </section>

  <!-- 关系分析：Sternberg + Gottman -->
  <section class="section">
    <p class="section-label">关系诊断</p>
    <div class="analysis-row">
      <div class="analysis-card">
        <div class="analysis-card-title">Sternberg 爱情三角</div>
        {sternberg_html}
      </div>
      <div class="analysis-card">
        <div class="analysis-card-title">Gottman 关系健康度</div>
        {gottman_html}
      </div>
    </div>
  </section>

  <!-- 人格分析 -->
  <section class="section">
    <p class="section-label">人格与依恋分析</p>
    {personality_html}
  </section>

  <!-- 军师建议 -->
  <section class="section">
    <p class="section-label">🎯 军师建议</p>
    {strategist_html}
  </section>

  <!-- 鉴定发现 -->
  <section class="section">
    <p class="section-label">鉴定发现</p>
    <div class="findings-list">
      {findings_html}
    </div>
  </section>

  <!-- 最终鉴定 -->
  <section class="section">
    <p class="section-label">最终鉴定</p>
    <div class="verdict-card">
      <div class="verdict-meta-row">
        <span class="verdict-type-badge">舔狗鉴定所 · 官方认证</span>
        {f'<span class="verdict-trend-badge">{trend_icon} {relationship_trend}</span>' if relationship_trend else ''}
      </div>
      <div class="verdict-type">{relationship_type}</div>
      <div class="verdict-label">{relationship_label}</div>
      <div class="verdict-divider"></div>
      <div class="verdict-text">{verdict}</div>
    </div>
  </section>

</main>

<footer class="footer">
  仅供娱乐 · 数据本地处理，不上传任何服务器 · 她爱你吗？舔狗鉴定所 · {date_str}
</footer>

<script>
const d = {chart_data_js};
const base = {{
  responsive: true,
  maintainAspectRatio: false,
  plugins: {{
    legend: {{ display: false }},
    tooltip: {{
      backgroundColor: '#18181f',
      borderColor: 'rgba(255,255,255,0.06)',
      borderWidth: 1,
      titleColor: '#f0f0f5',
      bodyColor: '#6b6b80',
      padding: 12,
    }}
  }}
}};

new Chart(document.getElementById('trendChart'), {{
  type: 'line',
  data: {{
    labels: d.trend_labels,
    datasets: [{{
      data: d.trend_data,
      borderColor: '#a855f7',
      backgroundColor: 'rgba(168,85,247,.08)',
      fill: true,
      tension: 0.4,
      pointRadius: 0,
      borderWidth: 2,
    }}]
  }},
  options: {{
    ...base,
    scales: {{
      x: {{ ticks: {{ color: '#3a3a4a', maxTicksLimit: 8, font: {{ size: 11 }} }}, grid: {{ color: 'rgba(255,255,255,0.03)' }}, border: {{ display: false }} }},
      y: {{ ticks: {{ color: '#3a3a4a', font: {{ size: 11 }} }}, grid: {{ color: 'rgba(255,255,255,0.03)' }}, border: {{ display: false }} }}
    }}
  }}
}});

new Chart(document.getElementById('hourChart'), {{
  type: 'bar',
  data: {{
    labels: d.hour_labels,
    datasets: [{{
      data: d.hour_data,
      backgroundColor: 'rgba(168,85,247,.5)',
      borderColor: 'rgba(168,85,247,.8)',
      borderWidth: 1,
      borderRadius: 3,
    }}]
  }},
  options: {{
    ...base,
    scales: {{
      x: {{ ticks: {{ color: '#3a3a4a', font: {{ size: 10 }}, maxTicksLimit: 8 }}, grid: {{ display: false }}, border: {{ display: false }} }},
      y: {{ ticks: {{ color: '#3a3a4a', font: {{ size: 10 }} }}, grid: {{ color: 'rgba(255,255,255,0.03)' }}, border: {{ display: false }} }}
    }}
  }}
}});

new Chart(document.getElementById('pieChart'), {{
  type: 'doughnut',
  data: {{
    labels: ['你', '{escape_html(contact_name)}'],
    datasets: [{{
      data: d.pie_data,
      backgroundColor: ['rgba(245,158,11,.8)', 'rgba(168,85,247,.8)'],
      borderColor: ['#f59e0b', '#a855f7'],
      borderWidth: 2,
    }}]
  }},
  options: {{
    ...base,
    plugins: {{
      ...base.plugins,
      legend: {{
        display: true,
        position: 'bottom',
        labels: {{ color: '#6b6b80', font: {{ size: 11 }}, padding: 16, boxWidth: 10 }}
      }}
    }},
    cutout: '65%'
  }}
}});
</script>
</body>
</html>"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stats", required=True)
    parser.add_argument("--analysis", required=True)
    parser.add_argument("--contact", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    stats = load_json(args.stats)
    analysis = load_json(args.analysis)

    html = render_html(stats, analysis, args.contact)

    os.makedirs(args.output, exist_ok=True)
    date_tag = datetime.now().strftime("%Y%m%d_%H%M")
    safe_name = re.sub(r'[^\w\-]', '_', args.contact) if args.contact else "contact"
    out_path = os.path.join(args.output, f"{safe_name}_{date_tag}.html")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"[+] 报告已生成: {out_path}", file=sys.stderr)
    print(json.dumps({"status": "ok", "path": out_path}))


if __name__ == "__main__":
    main()
