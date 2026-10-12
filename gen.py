# -*- coding: utf-8 -*-
"""执笔惊鸿 · 网文写作智库 —— 静态站生成器
用法：python gen.py
读取 content/*.md（frontmatter + markdown）→ 输出 site/
"""
import os, re, html, json, datetime, shutil

import markdown

ROOT = os.path.dirname(os.path.abspath(__file__))
CONTENT = os.path.join(ROOT, "content")
SITE = os.path.join(ROOT, "site")

BASE = "https://zbjh.top"
SITE_NAME = "执笔惊鸿"
SITE_SUB = "网文写作智库"
SITE_DESC = "写给网文作者的写作智库：从开书、黄金三章到大纲、爽点、钩子与连载中期救火，外加 AI 写作实操与全网工具，附可直接使用的免费在线工具。"
ICP = "苏ICP备2026033843号-1"  # 站点备案号，改成你自己的或置为空串即可

CATS = [
    {"id": "guide",    "name": "新手入门", "desc": "开书前的准备、黄金三章、书名与简介、大纲搭建"},
    {"id": "skill",    "name": "写作技法", "desc": "爽点、钩子、人设、节奏、毒点、场景与感情戏"},
    {"id": "ai",       "name": "AI 写作",  "desc": "AI 工具、提示词、协作流程与去 AI 味实操"},
    {"id": "oss",      "name": "开源工具", "desc": "GitHub 上经过逐项核实的网文写作项目与资料"},
    {"id": "platform", "name": "平台指南", "desc": "番茄 / 起点 / 晋江 / 七猫 / 知乎盐选的签约、稿费与规则"},
    {"id": "news",     "name": "行业资讯", "desc": "平台动态、榜单、征文赛事与合规政策"},
]

OSS = json.load(open(os.path.join(ROOT, "oss.json"), encoding="utf-8"))
OSS_CATS = OSS["cats"]
OSS_ITEMS = OSS["items"]
CATMAP = {c["id"]: c for c in CATS}

TOOLS = [
    {
        "id": "ai-flavor", "name": "AI 味检测器",
        "desc": "粘贴一章正文，本地即时扫出 AI 高频词、套路句式、重复词与破折号，给出可落地评分。纯浏览器运行，不上传、不留存。",
    },
    {
        "id": "cheatsheet", "name": "平台规则速查",
        "desc": "番茄 / 起点 / 晋江 / 七猫 / 知乎盐选 的签约门槛、稿费、全勤与 AI 政策，一表可搜可筛。",
    },
]


# ---------------- 工具函数 ----------------
def esc(s):
    return html.escape(str(s), quote=True)


def parse(path):
    raw = open(path, encoding="utf-8").read()
    m = re.match(r"^---\s*\r?\n(.*?)\r?\n---\s*\r?\n(.*)$", raw, re.S)
    if not m:
        raise ValueError("缺少 frontmatter: %s" % path)
    fm, body = m.group(1), m.group(2)
    meta = {}
    for line in fm.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    meta["tags"] = [t.strip() for t in meta.get("tags", "").split(",") if t.strip()]
    meta["slug"] = meta.get("slug") or os.path.splitext(os.path.basename(path))[0]
    meta.setdefault("cat", "skill")
    meta.setdefault("date", "2026-10-11")
    return meta, body.strip()


def md2html(text):
    md = markdown.Markdown(extensions=["tables", "fenced_code", "toc", "attr_list", "sane_lists"])
    out = md.convert(text)
    # 首段提升为 lead（若未手动标注）
    if out.startswith("<p>") and 'class="lead"' not in out:
        out = out.replace("<p>", '<p class="lead">', 1)
    return out


def load_articles():
    arts = []
    for fn in sorted(os.listdir(CONTENT)):
        if not fn.endswith(".md"):
            continue
        meta, body = parse(os.path.join(CONTENT, fn))
        meta["html"] = md2html(body)
        meta["words"] = len(re.sub(r"\s", "", body))
        arts.append(meta)
    arts.sort(key=lambda a: (a["date"], a["slug"]), reverse=True)
    return arts


def nav_html(active):
    items = [("", "首页")] + [(c["id"] + "/", c["name"]) for c in CATS] + [("tools/", "实用工具")]
    out = []
    for href, name in items:
        on = ' class="on"' if href.rstrip("/") == active.rstrip("/") else ""
        out.append('<a href="/%s"%s>%s</a>' % (href, on, esc(name)))
    return "".join(out)


def shell(title, desc, active, body, canonical, extra_head=""):
    full_title = "%s · %s" % (title, SITE_SUB) if title else "%s · %s" % (SITE_NAME, SITE_SUB)
    icp_line = ""
    if ICP:
        icp_line = '<a href="https://beian.miit.gov.cn/" target="_blank" rel="noopener">备案号 %s</a>' % esc(ICP)
    else:
        icp_line = '<span>备案号待补</span>'
    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%s</title>
<meta name="description" content="%s">
<link rel="canonical" href="%s">
<meta property="og:title" content="%s">
<meta property="og:description" content="%s">
<meta property="og:type" content="website">
<meta property="og:site_name" content="%s">
<link rel="stylesheet" href="/assets/style.css">
%s
</head>
<body>
<header class="site-head"><div class="wrap">
  <a class="brand" href="/"><span class="seal">笔</span><span>%s<small style="margin-left:6px">%s</small></span></a>
  <nav class="nav">%s</nav>
</div></header>
%s
<footer class="site-foot"><div class="wrap">
  <div class="cols">
    <div>
      <b>%s · %s</b>
      <p style="margin:0;line-height:1.8">%s</p>
    </div>
    <div><b>栏目</b>%s</div>
    <div><b>工具与信息</b>
      <a href="/tools/ai-flavor.html">AI 味检测器</a>
      <a href="/tools/cheatsheet.html">平台规则速查</a>
      <a href="/oss/">开源工具导航</a>
      <a href="/about.html">关于本站</a>
      <a href="/sitemap.xml">站点地图</a>
    </div>
  </div>
  <div class="bottom">
    <span>© %d %s</span>
    %s
    <span style="margin-left:auto;color:#a49c8e">内容为写作经验分享，不构成平台官方承诺，规则以各平台后台为准。</span>
  </div>
</div></footer>
</body>
</html>""" % (
        esc(full_title), esc(desc), esc(canonical), esc(full_title), esc(desc),
        esc(SITE_NAME), extra_head, esc(SITE_NAME), esc(SITE_SUB), nav_html(active),
        body,
        esc(SITE_NAME), esc(SITE_SUB), esc(SITE_DESC),
        "".join('<a href="/%s/">%s</a>' % (c["id"], esc(c["name"])) for c in CATS),
        datetime.date.today().year, esc(SITE_NAME), icp_line,
    )


def card(a):
    c = CATMAP.get(a["cat"], {"name": "文章"})
    return ('<a class="card" href="/%s/%s.html">'
            '<div class="kicker">%s</div><h3>%s</h3><p>%s</p>'
            '<div class="meta"><span>%s</span><span>约 %d 字</span></div></a>') % (
        a["cat"], a["slug"], esc(c["name"]), esc(a["title"]), esc(a.get("desc", "")),
        esc(a.get("date", "")), a.get("words", 0))


def write(path, content):
    full = os.path.join(SITE, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    open(full, "w", encoding="utf-8").write(content)


# ---------------- 页面构建 ----------------
def build_index(arts):
    tool_cards = "".join(
        '<div class="toolcard"><h3>%s</h3><p>%s</p>'
        '<a class="btn primary" href="/tools/%s.html">打开工具</a></div>' % (esc(t["name"]), esc(t["desc"]), t["id"])
        for t in TOOLS)
    blocks = ""
    for c in CATS:
        items = [a for a in arts if a["cat"] == c["id"]][:4]
        if not items:
            continue
        blocks += ('<section><div class="sec-head"><h2>%s</h2>'
                   '<span class="more" style="color:#a49c8e">%s</span>'
                   '<a class="more" href="/%s/">全部 →</a></div>'
                   '<div class="grid">%s</div></section>') % (
            esc(c["name"]), esc(c["desc"]), c["id"], "".join(card(a) for a in items))
    body = """
<section class="hero"><div class="wrap">
  <h1>写网文这件事，<br>把该踩的坑先讲清楚</h1>
  <p>%s</p>
  <div class="cta">
    <a class="btn primary" href="/tools/ai-flavor.html">先用 AI 味检测器看看稿子</a>
    <a class="btn" href="/guide/">从新手入门读起</a>
  </div>
</div></section>
<div class="wrap">
  <section>
    <div class="sec-head"><h2>免费在线工具</h2><span class="more" style="color:#a49c8e">纯浏览器运行，不上传你的稿子</span></div>
    <div class="grid two">%s</div>
  </section>
  %s
</div>""" % (esc(SITE_DESC), tool_cards, blocks)
    return shell("", SITE_DESC, "", body, BASE + "/")


def build_cat(c, arts):
    items = [a for a in arts if a["cat"] == c["id"]]
    cards = "".join(card(a) for a in items) if items else '<p style="color:#7a746a">本栏目内容正在整理中。</p>'
    body = ('<div class="wrap"><section><div class="sec-head"><h2>%s</h2>'
            '<span class="more" style="color:#a49c8e">%s</span></div>'
            '<div class="grid">%s</div></section></div>') % (esc(c["name"]), esc(c["desc"]), cards)
    desc = "%s——%s。%s" % (c["name"], c["desc"], SITE_DESC)
    return shell(c["name"], desc, c["id"] + "/", body, "%s/%s/" % (BASE, c["id"]))


def build_article(a):
    c = CATMAP.get(a["cat"], {"name": "文章", "id": ""})
    tags = "".join('<span class="tag">%s</span>' % esc(t) for t in a.get("tags", []))
    body = """<div class="wrap"><article class="article">
  <div class="crumb"><a href="/">首页</a> / <a href="/%s/">%s</a></div>
  <h1>%s</h1>
  <div class="ameta"><span>%s</span><span>约 %d 字</span>%s</div>
  %s
</article></div>""" % (
        c["id"], esc(c["name"]), esc(a["title"]), esc(a.get("date", "")), a.get("words", 0),
        ('<span style="margin-left:auto">' + tags + '</span>') if tags else "",
        a["html"])
    return shell(a["title"], a.get("desc", SITE_DESC), c["id"] + "/", body,
                 "%s/%s/%s.html" % (BASE, a["cat"], a["slug"]))


def build_oss(arts):
    """开源工具栏目页：项目导航（可搜索、可筛选）+ 本栏目文章。"""
    items = OSS_ITEMS
    catmap = {c["id"]: c["name"] for c in OSS_CATS}
    btns = '<button class="btn chip on" data-cat="all">全部</button>' + "".join(
        '<button class="btn chip" data-cat="%s">%s</button>' % (c["id"], esc(c["name"]))
        for c in OSS_CATS)
    cards = ""
    for it in items:
        tags = "".join('<span class="tag">%s</span>' % esc(t) for t in it.get("tags", []))
        meta = " · ".join([x for x in [it.get("lang"), it.get("lic"),
                                       "更新 " + it.get("pushed", "")] if x and x != "—"])
        cards += ('<div class="osscard" data-cat="%s" data-k="%s">'
                  '<div class="osshead"><h3>%s</h3><span class="star">%s ★</span></div>'
                  '<div class="osstags">%s</div>'
                  '<p class="osswhat">%s</p>'
                  '<p class="osswho"><b>适合</b> %s</p>'
                  '<p class="ossnote">%s</p>'
                  '<div class="ossfoot"><span>%s</span>'
                  '<a href="%s" target="_blank" rel="noopener nofollow">查看仓库 →</a></div>'
                  '</div>') % (
            it["cat"], esc(it["name"] + " " + it["repo"] + " " + " ".join(it.get("tags", []))),
            esc(it["name"]), it.get("stars", 0), tags, esc(it["what"]),
            esc(it.get("who", "")), esc(it.get("note", "")), esc(meta), esc(it["url"]))
    arts_of_cat = [a for a in arts if a["cat"] == "oss"]
    art_html = ("<section><div class='sec-head'><h2>本栏目文章</h2></div><div class='grid'>%s</div></section>"
                % "".join(card(a) for a in arts_of_cat)) if arts_of_cat else ""
    body = """<div class="wrap">
<section>
  <div class="sec-head"><h2>开源工具</h2><span class="more" style="color:#a49c8e">%d 个项目 · 逐项核实 · 数据截至 %s</span></div>
  <p class="lead">这里收录 GitHub 上与中文网文写作直接相关的开源项目。每一个都拉过源码正文核实：确认它真的做什么、星数与许可证、以及最后一次更新时间。名目对不上或查不到实际内容的，一律不收。</p>
  <p style="color:#7a746a;font-size:14.5px">说明：星数来自 GitHub 接口，随时会变；<b>最后更新日期比星数更值得看</b>——这批项目迭代很快，三个月没动的可能已经跟不上模型变化。点击标题进入仓库，本站不代理任何下载。</p>
  <div class="toolbar" style="margin:18px 0 6px">
    <input id="ossq" type="search" placeholder="搜索项目名、用途、标签……" style="flex:1;min-width:220px;padding:10px 14px;border:1px solid var(--line);border-radius:10px;font-size:15px;font-family:inherit">
    %s
  </div>
  <div class="ossgrid" id="osslist">%s</div>
  <p id="ossempty" style="display:none;color:#7a746a;padding:30px 0;text-align:center">没有匹配的项目，换个词试试。</p>
</section>
%s
</div>""" % (len(items), esc(OSS["updated"]), btns, cards, art_html)
    cat_names = "、".join(c["name"] for c in OSS_CATS)
    desc = "中文网文写作相关的 GitHub 开源项目与资料导航：%s，共 %d 个，逐项核实星数、许可证与更新状态。" % (cat_names, len(items))
    return shell("开源工具", desc, "oss/", body, BASE + "/oss/",
                 extra_head='<script src="/assets/oss.js" defer></script>')


def build_about():
    body = """<div class="wrap"><article class="article">
  <h1>关于本站</h1>
  <p class="lead">执笔惊鸿是一个写给网文作者的写作智库。这里不讲玄学，只讲能落地的技术与可查证的规则。</p>
  <h2>这里有什么</h2>
  <ul>
    <li><b>新手入门</b>：开书前的准备、黄金三章、书名与简介的写法、大纲与细纲的搭法。</li>
    <li><b>写作技法</b>：爽点节奏、章末钩子、人设与代入感、毒点排查、连载中期救火。</li>
    <li><b>平台指南</b>：番茄 / 起点 / 晋江 / 七猫 / 知乎盐选 的签约门槛、稿费结构、全勤与 AI 政策。</li>
    <li><b>AI 写作</b>：AI 辅助写作的协作流程、提示词写法与去 AI 味实操。</li>
    <li><b>实用工具</b>：AI 味检测器、平台规则速查，全部免费、纯浏览器运行。</li>
  </ul>
  <h2>两条原则</h2>
  <p>其一，<b>规则以平台后台为准</b>。各平台政策会调整，本站写下的都是整理时的状态，签约前请以作者后台与官方公告为最终依据。</p>
  <p>其二，<b>工具不上传你的稿子</b>。站内所有在线工具均在浏览器本地运算，正文不经过服务器，不做留存。</p>
  <h2>联系与纠错</h2>
  <p>若发现规则过时、链接失效或内容有误，欢迎通过站内渠道反馈，我们会尽快核实更正。</p>
</article></div>"""
    return shell("关于本站", "关于执笔惊鸿网文写作智库：内容范围、两条原则与纠错方式。", "about", body, BASE + "/about.html")


def build_tools_index():
    cards = "".join(
        '<div class="toolcard"><h3>%s</h3><p>%s</p>'
        '<a class="btn primary" href="/tools/%s.html">打开</a></div>' % (esc(t["name"]), esc(t["desc"]), t["id"])
        for t in TOOLS)
    body = ('<div class="wrap"><section><div class="sec-head"><h2>实用工具</h2>'
            '<span class="more" style="color:#a49c8e">全部免费、纯浏览器运行、不上传稿件</span></div>'
            '<div class="grid two">%s</div></section></div>') % cards
    return shell("实用工具", "免费在线写作工具：AI 味检测器、平台规则速查。纯浏览器运行，稿件不上传。",
                 "tools/", body, BASE + "/tools/")


def build_tool_ai_flavor():
    body = """<div class="wrap">
<section>
  <div class="sec-head"><h2>AI 味检测器</h2><span class="more" style="color:#a49c8e">纯浏览器运行 · 稿件不上传 · 免费</span></div>
  <div class="toolbox">
    <textarea id="src" placeholder="把一章正文粘贴到这里（建议 2000 字以上），检测会自动开始……"></textarea>
    <div class="toolbar">
      <button class="btn primary" id="run">开始检测</button>
      <button class="btn" id="sample">填入示例</button>
      <button class="btn" id="clear">清空</button>
      <span class="hint">检测项：AI 高频词 · 套路句式 · 重复词 · 破折号与省略号</span>
    </div>
    <div class="resultbox" id="result"></div>
  </div>
</section>
<section>
  <div class="article" style="padding-top:0;max-width:760px;margin:0 auto">
    <h2>它查什么</h2>
    <p>网文被编辑或读者判定为「AI 写的」，往往不是因为情节，而是因为一批反复出现的词汇和句式。本工具照这套判据，把一章正文里最容易被机器腔拖累的地方挑出来：</p>
    <ul>
      <li><b>AI 高频词</b>：仿佛、似乎、忽然、瞬间、然而、这一刻、嘴角勾起、眼中闪过一丝一类。这类词本身不错，问题在密度——一章里出现十几次，读者立刻出戏。</li>
      <li><b>套路句式</b>：「不是…而是…」的绕圈句、「愤怒地说」式的副词句、「既…又…」的对称排比句。</li>
      <li><b>重复词</b>：同一个人名、动作或形容词在短距离内反复出现，读起来像复读机。</li>
      <li><b>破折号与省略号</b>：过量使用是机器生成文本的典型特征。</li>
    </ul>
    <h2>怎么用才有效</h2>
    <p>它给的是一个<b>筛查清单，不是判决书</b>。分数低不代表稿子不好，只说明有机器腔的痕迹需要清理。正确用法是：先看「问题清单」，把高危项逐条改掉，再复检看分数有没有回升。改稿时优先处理重复次数最多的那几处，收益最大。</p>
    <div class="tip"><b>隐私说明</b>：所有计算都在你的浏览器里完成，正文不会发送到任何服务器，关闭页面即消失。可以放心粘贴未发布的稿子。</div>
  </div>
</section>
</div>"""
    return shell("AI 味检测器", "免费在线 AI 味检测器：粘贴网文正文，即时扫出 AI 高频词、套路句式、重复词与破折号，给出评分与逐条修改建议。纯浏览器运行，稿件不上传。",
                 "tools/", body, BASE + "/tools/ai-flavor.html",
                 extra_head='<script src="/assets/ai-flavor.js" defer></script>')


def build_tool_cheatsheet():
    rows = [
        ("番茄小说", "free", "约 2 万字可申请签约（以后台为准）", "广告分成 + 全勤奖", "日更达标且听读分成达标方可得全勤", "要求人工润色，纯 AI 直接发布风险高", "新人、快节奏爽文与脑洞文"),
        ("七猫小说", "free", "约 3 万字（以后台为准）", "保底稿费 + 超出部分分成", "按更新与数据达标发放", "以官方最新公告为准", "想要稳定保底的兼职作者"),
        ("起点中文网", "paid", "约 3 万字并达到一定收藏", "订阅分成 + 打赏 + IP 衍生", "月更达标领奖", "审核严格，禁止纯 AI 直发", "男频长篇、硬核世界观"),
        ("晋江文学城", "paid", "约 5 万字并有读者反馈", "订阅 + 版权开发", "日更达标", "重原创，AI 痕迹重会被下架", "女频言情、古言与情感向"),
        ("知乎盐选", "short", "短篇 1–2 万字", "单篇稿费或分账", "不适用", "对 AI 辅助相对宽松", "写不了长篇、想做短篇试水"),
    ]
    trs = "".join(
        '<tr data-type="%s"><td><b>%s</b></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (
            t, esc(a), esc(b), esc(c), esc(d), esc(e), esc(f))
        for a, t, b, c, d, e, f in rows)
    body = """<div class="wrap">
<section>
  <div class="sec-head"><h2>平台规则速查</h2><span class="more" style="color:#a49c8e">整理时间 2026-10 · 以官方后台为准</span></div>
  <div class="toolbox">
    <div class="toolbar" style="margin:0 0 14px">
      <input id="q" type="search" placeholder="搜索平台、规则关键词……" style="flex:1;min-width:200px;padding:10px 14px;border:1px solid var(--line);border-radius:10px;font-size:15px;font-family:inherit">
      <button class="btn btn-primary chip on" data-type="all">全部</button>
      <button class="btn chip" data-type="free">免费平台</button>
      <button class="btn chip" data-type="paid">付费平台</button>
      <button class="btn chip" data-type="short">短篇</button>
    </div>
    <div style="overflow-x:auto">
    <table style="width:100%;border-collapse:collapse;font-size:14.5px;min-width:760px">
      <thead><tr style="background:#f7f4ee">
        <th style="border:1px solid var(--line);padding:9px 11px;text-align:left">平台</th>
        <th style="border:1px solid var(--line);padding:9px 11px;text-align:left">类型</th>
        <th style="border:1px solid var(--line);padding:9px 11px;text-align:left">签约门槛</th>
        <th style="border:1px solid var(--line);padding:9px 11px;text-align:left">收入结构</th>
        <th style="border:1px solid var(--line);padding:9px 11px;text-align:left">更新与全勤</th>
        <th style="border:1px solid var(--line);padding:9px 11px;text-align:left">AI 政策</th>
        <th style="border:1px solid var(--line);padding:9px 11px;text-align:left">适合人群</th>
      </tr></thead>
      <tbody>__ROWS__</tbody>
    </table>
    </div>
  </div>
</section>
<section>
  <div class="article" style="padding-top:0">
    <h2>用之前先知道的两件事</h2>
    <p>第一，<b>上表是整理时的公开信息，不是官方承诺</b>。各平台的签约门槛、稿费与 AI 政策调整频繁，有的平台一年内就改过数次。动笔前请到<b>作者后台的帮助中心与官方公告</b>核对一次，那才是最终依据。</p>
    <p>第二，<b>没有「最容易赚钱的平台」，只有「匹配你的平台」</b>。免费平台流量大、门槛低，但收入波动剧烈，断更一天可能半个月白干；付费平台上限高，但新书前期几乎零收入，需要存稿和心理准备；短篇适合试水，但不适合想写长篇的人。</p>
    <div class="tip"><b>一条实用建议</b>：先确定自己能稳定写多少字、能不能接受断更带来的数据损失，再反推该去哪个平台，而不是看别人在哪儿赚钱就跟到哪儿。</div>
  </div>
</section>
</div>"""
    body = body.replace("__ROWS__", trs)
    return shell("平台规则速查", "番茄、起点、晋江、七猫、知乎盐选等平台的签约门槛、收入结构、全勤与 AI 政策速查表，可搜索可筛选。",
                 "tools/", body, BASE + "/tools/cheatsheet.html",
                 extra_head='<script src="/assets/cheatsheet.js" defer></script>')


def build_sitemap(arts):
    urls = ["/", "/tools/", "/tools/ai-flavor.html", "/tools/cheatsheet.html", "/about.html"]
    urls += ["/%s/" % c["id"] for c in CATS]
    urls += ["/%s/%s.html" % (a["cat"], a["slug"]) for a in arts]
    today = datetime.date.today().isoformat()
    items = "".join('<url><loc>%s%s</loc><lastmod>%s</lastmod></url>' % (BASE, u, today) for u in urls)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">%s</urlset>' % items)


def build_robots():
    return ("User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n" % BASE)


# ---------------- 入口 ----------------
def main():
    arts = load_articles()
    if not os.path.isdir(SITE):
        os.makedirs(SITE)
    write("index.html", build_index(arts))
    for c in CATS:
        if c["id"] == "oss":
            continue  # oss 用专门的导航页生成
        write("%s/index.html" % c["id"], build_cat(c, arts))
    write("oss/index.html", build_oss(arts))
    for a in arts:
        write("%s/%s.html" % (a["cat"], a["slug"]), build_article(a))
    write("tools/index.html", build_tools_index())
    write("tools/ai-flavor.html", build_tool_ai_flavor())
    write("tools/cheatsheet.html", build_tool_cheatsheet())
    write("about.html", build_about())
    write("sitemap.xml", build_sitemap(arts))
    write("robots.txt", build_robots())
    # 复制静态资源（css / js）
    src_assets = os.path.join(ROOT, "assets")
    if os.path.isdir(src_assets):
        shutil.copytree(src_assets, os.path.join(SITE, "assets"), dirs_exist_ok=True)
        print("已复制 assets/")
    print("生成完成：%d 篇文章，%d 个栏目" % (len(arts), len(CATS)))
    for a in arts:
        print("  [%s] %s" % (a["cat"], a["title"]))


if __name__ == "__main__":
    main()
