# 执笔惊鸿 · 网文写作智库

> 一个纯静态的网文写作知识站生成器。写完 22 篇原创文章、2 个可直接用的在线工具、
> 50 个逐项核实过的 GitHub 开源项目导航后，跑一行命令生成整站。

A static site generator for a Chinese web-novel writing knowledge base.
Pure Python + Markdown, output is plain HTML with no runtime dependency.

---

## 它解决什么问题

网上讲「怎么写网文」的内容很多，但大多有两个毛病：**要么是空泛的鸡汤**（「要坚持」「要有代入感」），
**要么是散落一地的碎片**（这条在某个公众号、那条在某个论坛）。

这个项目把「能直接照做」的那部分沉淀成一个站：开书前的准备、黄金三章、大纲与伏笔、
爽点与钩子节奏、连载中期救火，再叠上 AI 写作的实操与去 AI 味。**每一篇都落在一个具体动作上。**

另外补了两样竞品普遍没有的东西 —— **工具**。

---

## 两个在线工具（纯浏览器运行）

| 工具 | 说明 |
|------|------|
| **AI 味检测器** | 粘贴一章正文，本地即时扫出 AI 高频词、套路句式、重复词与破折号密度，给出可落地评分。**规则不上云、正文不上传、不留存。** |
| **平台规则速查** | 番茄 / 起点 / 晋江 / 七猫 / 知乎盐选的签约门槛、稿费、全勤与 AI 政策，一表可搜可筛。 |

AI 味检测器的规则集是从一个真实写作工具中移植过来的，包含：

- 29 个 AI 高频词（「不可否认」「值得注意的是」「总的来说」一类）
- 3 类套路句式正则（不仅是 / 不是……而是 / 排比式收尾）
- 100+ 停用词与虚词密度统计
- 破折号、省略号等标点滥用检测
- 综合成 0–100 的可读评分与分项定位

移植后全部跑在浏览器里，所以可以放心把未发表的书稿粘进去。

---

## 内容规模

| 栏目 | 说明 | 篇数 |
|------|------|------|
| 新手入门 | 开书前准备、黄金三章、书名与简介、大纲搭建 | 5 |
| 写作技法 | 爽点、钩子、人设、节奏、毒点、场景与感情戏 | 8 |
| AI 写作 | AI 工具、提示词、协作流程与去 AI 味实操 | 7 |
| 平台指南 | 番茄 / 起点 / 晋江 / 七猫 / 知乎盐选规则 | 2 |
| 行业资讯 | 平台动态、榜单、征文赛事与合规政策 | — |
| 开源工具 | 50 个经核实的 GitHub 项目，分 6 类 | 导航页 |
| 在线工具 | AI 味检测器、平台规则速查 | 2 |

合计 **22 篇文章 + 50 个开源项目数据 + 2 个在线工具**。

---

## 目录结构

```
webnovel-writer-kb/
├── gen.py              # 生成器：读 content/*.md → 输出 site/
├── oss.json            # 开源项目导航数据（6 分类 / 50 项）
├── content/            # 22 篇文章（Markdown + frontmatter）
│   ├── golden-three-chapters.md
│   ├── remove-ai-flavor.md
│   └── ...
├── assets/             # 样式与两个工具的脚本
│   ├── style.css
│   ├── ai-flavor.js    # AI 味检测器
│   ├── cheatsheet.js   # 平台规则速查
│   └── oss.js
└── site/               # 生成的成品（可直接部署）
```

---

## 用法

### 生成站点

```bash
pip install markdown
python gen.py
```

生成的 `site/` 即为完整静态站，直接丢给 nginx 或 GitHub Pages 即可。

### 本地预览

```bash
cd site
python3 -m http.server 8080
# 打开 http://localhost:8080/
```

### 新增一篇文章

在 `content/` 下新建 `.md`，带 frontmatter：

```markdown
---
title: 文章标题
desc: 一两句话的摘要，用于列表页与 SEO 描述
tags: 标签一, 标签二
date: 2026-10-11
cat: skill
---

正文……
```

`cat` 取值对应「栏目 id」：`guide` / `skill` / `ai` / `platform` / `news`。
文件名即 slug（除非 frontmatter 里显式指定 `slug`）。重新跑 `gen.py` 即可。

### 改域名与备案号

`gen.py` 顶部：

```python
BASE = "https://your-domain.com"
SITE_NAME = "站点名"
ICP = "你的备案号"     # 不需要就置为空串
```

---

## 开源项目导航数据（oss.json）

```json
{
  "cats": [ { "id": "skills", "name": "技能包", "order": 1 }, ... ],
  "items": [
    {
      "repo": "owner/repo",
      "name": "项目名",
      "stars": 1234,
      "lang": "Python",
      "lic": "MIT",
      "pushed": "2026-09-01",
      "cat": "skills",
      "tags": ["标签"],
      "what": "这个项目做什么",
      "who": "适合谁用",
      "note": "值得注意的一点",
      "url": "https://github.com/owner/repo"
    }
  ]
}
```

六个分类：技能包 / 去 AI 味 / 桌面软件 / 语料与模型 / 海外与研究 / 拆书研究。
收录标准是「**能直接用**」，纯论文或已停更的项目不收入。

---

## 部署

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    root /var/www/webnovel-writer-kb/site;
    index index.html;

    location / { try_files $uri $uri/ $uri.html =404; }
    location ~* \.(css|js|png|jpg|svg|woff2)$ {
        expires 7d;
        add_header Cache-Control "public";
    }
}
```

---

## 许可

[MIT](LICENSE) —— 代码与文章均可自由使用。文中涉及的各平台规则以平台官方最新说明为准。
