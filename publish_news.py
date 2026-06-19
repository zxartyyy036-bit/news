#!/usr/bin/env python3
"""家庭新闻 — 统一发布器 (David 2026-06-19 归档结构定稿)
职责: 把 pipeline 生成的成品, 同时落到两个地方:
  1. 本地中文归档 ~/news/<中文名>/HTML|PDF/  ← 你自己浏览方便
  2. GitHub 仓库根 ~/news/<英文短名>.html      ← 家人在线看(干净URL)
然后生成入口页 index.html, 用 token 推送(token从本地文件读, 不写死)。

用法:
  python3 publish_news.py            # 发布今天
  python3 publish_news.py 20260619   # 发布指定日期
token 来源(按优先级): 环境变量 GH_TOKEN / ~/.config/news_gh_token (chmod 600)
"""
import os, sys, json, shutil, subprocess, datetime, glob

HOME = os.path.expanduser("~")
NEWS = os.path.join(HOME, "news")                       # GitHub 仓库根 = 归档根
FAMILY = os.path.join(HOME, "HermesWork/PROJECTS/FAMILY_NEWS")
OUT = os.path.join(FAMILY, "out")                       # render.py 的输出
REPO_URL = "github.com/zxartyyy036-bit/news.git"

# 中文 key → (英文短名, 显示名)
PEOPLE = {
    "姥爷":   ("laoye", "姥爷"),
    "爸爸":   ("baba", "爸爸"),
    "妈妈":   ("mama", "妈妈"),
    "阳阳":   ("yangyang", "阳阳"),
    "小姨夫": ("xiaoyifu", "小姨夫"),
    "小姨":   ("xiaoyi", "小姨"),
}


def get_token():
    t = os.environ.get("GH_TOKEN")
    if t:
        return t.strip()
    f = os.path.join(HOME, ".config/news_gh_token")
    if os.path.exists(f):
        return open(f).read().strip()
    return None


def archive_and_stage(date_token):
    """把 out/<中文>_<日期>.html|pdf 归档到 ~/news/<中文>/HTML|PDF, 并把英文短名HTML放仓库根。"""
    counts = {}
    mf = os.path.join(OUT, f"manifest_{date_token}.json")
    if os.path.exists(mf):
        m = json.load(open(mf, encoding="utf-8"))
        counts = {u["key"]: u["count"] for u in m.get("users", [])}

    staged = []
    for cn, (slug, disp) in PEOPLE.items():
        src_html = os.path.join(OUT, f"{cn}_{date_token}.html")
        src_pdf = os.path.join(OUT, f"{cn}_{date_token}.pdf")
        if not os.path.exists(src_html):
            continue
        # 1) 中文归档(本地浏览)
        zh_html_dir = os.path.join(NEWS, cn, "HTML")
        zh_pdf_dir = os.path.join(NEWS, cn, "PDF")
        os.makedirs(zh_html_dir, exist_ok=True)
        os.makedirs(zh_pdf_dir, exist_ok=True)
        shutil.copy(src_html, os.path.join(zh_html_dir, f"{date_token}.html"))
        if os.path.exists(src_pdf):
            shutil.copy(src_pdf, os.path.join(zh_pdf_dir, f"{date_token}.pdf"))
        # 2) 英文短名放仓库根(GitHub线上, 最新版覆盖 <slug>.html, 历史存 <slug>_<日期>.html)
        shutil.copy(src_html, os.path.join(NEWS, f"{slug}.html"))
        shutil.copy(src_html, os.path.join(NEWS, f"{slug}_{date_token}.html"))
        staged.append((cn, slug, disp, counts.get(cn, "")))
    return staged


def write_index(staged, date_str):
    cards = []
    # "全部"放最顶
    cards.append('    <a class="card all" href="all.html"><span class="name">📰 全部</span>'
                 '<span><span class="meta">所有人 · 所有日期</span><span class="arrow"> ›</span></span></a>')
    for cn, slug, disp, n in staged:
        meta = f"{n} 条" if n != "" else "查看"
        cards.append(f'    <a class="card" href="{slug}.html"><span class="name">{disp}</span>'
                     f'<span><span class="meta">{meta}</span><span class="arrow"> ›</span></span></a>')
    html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>家庭每日简报</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0;-webkit-text-size-adjust:100%;}}
body{{font-family:-apple-system,"PingFang SC","Heiti SC",sans-serif;background:linear-gradient(160deg,#3aab9a,#2b8fa0);min-height:100vh;color:#fff;}}
.wrap{{max-width:560px;margin:0 auto;padding:34px 20px 50px;}}
h1{{font-size:30px;font-weight:800;text-align:center;letter-spacing:1px;}}
.date{{text-align:center;opacity:.9;margin-top:8px;font-size:16px;}}
.tip{{text-align:center;opacity:.82;margin:18px 0 26px;font-size:14px;line-height:1.7;}}
.grid{{display:flex;flex-direction:column;gap:13px;}}
a.card{{display:flex;align-items:center;justify-content:space-between;background:rgba(255,255,255,.96);color:#1f2937;text-decoration:none;padding:20px 22px;border-radius:16px;box-shadow:0 4px 16px rgba(0,0,0,.13);transition:transform .12s;}}
a.card:active{{transform:scale(.97);}}
a.card.all{{background:rgba(255,255,255,.99);border:2px solid #f0c14b;}}
.name{{font-size:22px;font-weight:700;}}
.meta{{font-size:14px;color:#3aab9a;font-weight:700;}}
.arrow{{color:#3aab9a;font-size:20px;font-weight:700;margin-left:8px;}}
footer{{text-align:center;opacity:.75;font-size:12px;margin-top:30px;line-height:1.8;}}
</style></head><body><div class="wrap">
<h1>家庭每日简报</h1>
<div class="date">{date_str} · 冰见为全家整理</div>
<div class="tip">点你的名字,看为你定制的新闻 ☀️<br>每条都标了来源和媒体立场,自己判断</div>
<div class="grid">
{chr(10).join(cards)}
</div>
<footer>每天上午自动更新 · 链接不变,收藏即可<br>新闻来自公开媒体,仅供家人阅读参考</footer>
</div></body></html>"""
    open(os.path.join(NEWS, "index.html"), "w", encoding="utf-8").write(html)


def push(date_str):
    tok = get_token()
    if not tok:
        print("⚠️ 没有 token, 跳过推送。把成品本地准备好了。")
        print("   token 放 ~/.config/news_gh_token (chmod 600) 或设 GH_TOKEN 环境变量后重跑。")
        return False
    env = dict(os.environ)
    subprocess.run(["git", "add", "-A"], cwd=NEWS, check=False)
    subprocess.run(["git", "-c", "user.name=himi", "-c", "user.email=himi@local",
                    "commit", "-m", f"家庭每日简报 {date_str}"], cwd=NEWS, check=False,
                   capture_output=True)
    url = f"https://zxartyyy036-bit:{tok}@{REPO_URL}"
    r = subprocess.run(["git", "push", url, "main"], cwd=NEWS,
                       capture_output=True, text=True)
    ok = r.returncode == 0
    print("✅ 推送成功" if ok else f"❌ 推送失败: {r.stderr[-300:].replace(tok,'<TOKEN>')}")
    return ok


def main():
    date_token = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().strftime("%Y%m%d")
    date_str = f"{date_token[:4]}年{date_token[4:6]}月{date_token[6:]}日"
    print(f"=== 发布 {date_str} ===")
    staged = archive_and_stage(date_token)
    if not staged:
        print(f"⚠️ out/ 里没有 {date_token} 的成品, 先跑 pipeline.py")
        return
    print(f"归档+暂存 {len(staged)} 人: {[s[1] for s in staged]}")
    write_index(staged, date_str)
    print("入口页 index.html 已生成(含'全部'入口)")
    push(date_str)
    print(f"\n线上: https://zxartyyy036-bit.github.io/news/")


if __name__ == "__main__":
    main()
