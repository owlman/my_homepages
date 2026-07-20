# 维护指南

本文档记录 MyHome (www.owlman.cn) 的结构、设计约定、关键决策与维护要点，供日后维护参考。

## 项目概览

**定位**：以"外链聚合"为核心的个人主页，定位为内容入口（博客、GitHub、出版书籍），非原创内容站。

**技术栈**：
- 纯静态站点（HTML5 + CSS3 + 原生 JS）
- Bootstrap 5.3.3（本地化，非 CDN）
- Simple Icons / Bootstrap Icons 风格 SVG（内联 sprite）
- Noto Serif SC 衬线字体（Google Fonts CDN，`display=swap`）
- GitHub Pages 部署 + CNAME 自定义域名

**特色**：
- 衬线体（标题）+ 黑体（正文）文人风格
- 深色模式为默认，可切换
- 响应式：移动端单列、桌面端主-侧栏
- 无构建步骤

## 目录结构

```
MyHome/
├── index.htm              # 主页（head + SVG sprite + 主体）
├── books.json             # 作品数据（15 本著作）
├── posts.json             # 博客文章列表（来自博客园）
├── robots.txt             # 搜索引擎指令
├── sitemap.xml            # 站点地图
├── site.webmanifest       # PWA 配置
├── CNAME                  # 自定义域名 (www.owlman.cn)
├── css/
│   └── style.css          # 全部自定义样式（含深色模式覆写）
├── js/
│   └── main.js            # 主题切换 / 数据加载 / 滚动动画 / Tab 路由
├── img/
│   ├── me.png             # 头像（Hero / OG / JSON-LD）+ favicon 源
│   ├── owl.png            # 旧 logo（已无引用，保留作历史）
│   ├── me.jpg             # 早期从 me.png 转的 JPG（已弃用）
│   ├── books/             # 15 本封面（WebP 格式，width 400px）
│   ├── icons/             # 旧 Simple Icons 目录（已内联进 sprite）
│   ├── icon-192.png       # PWA 图标（从 me.png 生成）
│   ├── icon-512.png       # PWA 图标（从 me.png 生成）
│   ├── apple-touch-icon.png
│   ├── favicon-16.png
│   ├── favicon-32.png
│   ├── read.png / write.jpg / coding.jpg / movie.jpg
│   │                       # 兴趣图标（已弃用，未删除可作历史）
│   └── js_guide.png       # 旧精选封面（已弃用）
├── vendor/
│   ├── bootstrap/
│   │   ├── css/bootstrap.min.css
│   │   └── js/bootstrap.bundle.min.js
│   └── fonts/
│       ├── noto-serif-sc-400.woff2   # 子集化（tools/subset_font.py）
│       └── noto-serif-sc-700.woff2
├── data/
│   ├── social-links.json
│   └── social-links.schema.json
└── tools/
    ├── play_owlman.py      # 核心评估工具（4 步校验）
    ├── fetch_posts.py      # 从博客园抓取文章列表
    ├── build_sitemap.py    # 从 books/posts 合成 sitemap.xml
    ├── build_jsonld.py     # 从 books.json 生成 JSON-LD Books 列表
    ├── subset_font.py      # 下载并子集化字体
    ├── check.sh            # 预提交校验脚本
    ├── install-hook.sh     # 安装 Git 钩子
    └── pre-push            # 预推送钩子模板
```

## 内容维护

### 新增 / 修改书籍

编辑 `books.json`：

```json
{
  "title": "书名",
  "url": "https://book.douban.com/subject/12345/",
  "type": "original" | "translation",
  "cover": "img/books/封面文件名.webp",
  "w": 400,
  "h": 580,
  "year": 2026
}
```

- `type` 决定归属"原创"还是"翻译" Tab
- `w`/`h` 用于保留图片原始宽高（防 CLS）
- `year` 是出版年份，会在封面右下角显示
- 封面必须本地化（豆瓣图床防盗链，**不可直接外链**）
- 顺序：每个 type 内按 year 倒序（最新在前）

封面获取方法：服务端带 Referer 下载到 `img/books/`，转 WebP（建议 quality 80，width ≤400）。

Tab 角标的数字会自动从 JSON 计数。

### 新增 / 修改博客文章

**推荐**：`python tools/fetch_posts.py` 一行从博客园 `cnblogs.com/owlman/` 抓取首页 10 篇文章，直接覆盖 `posts.json`。原理见 `tools/fetch_posts.py` 顶部 docstring。

```bash
python tools/fetch_posts.py            # 抓首页 10 篇，直接写 posts.json
python tools/fetch_posts.py --dry-run  # 只打印 JSON 到 stdout，不写文件（先看 diff）
python tools/fetch_posts.py --pages 2  # 抓首页 + 第 2 页（按 date 去重）
python tools/fetch_posts.py --url <URL>  # 自定义博客首页
```

或者一次性"抓取 + 校验"：`python tools/play_owlman.py --fetch --skip-live` —— `play_owlman.py` 会先调用 `fetch_posts.py` 再跑 schema 校验。

**手动维护**（仅在脚本失效时退回）：编辑 `posts.json`：

```json
{
  "title": "文章标题",
  "url": "https://www.cnblogs.com/owlman/p/12345",
  "date": "2026-07-08"
}
```

`date` 必填，文章卡片会显示。

### 修改个人简介 / 荣誉 / 技能

直接编辑 `index.htm` 的 `#about` section（搜索 `个人简介`、`专长领域`、`曾获荣誉`）。

- 个人简介：单段文字（`max-width: 70ch` 限制行长）
- 专长：用 `.skill-tag` 标签胶囊呈现
- 荣誉：用 `.timeline > li` 时间线，年份用 `<span class="timeline-year">` 强调

### 修改购买链接

代表作卡片（`index.htm` 搜索 `JavaScript 全栈开发`）的 `.shop-badge` 区，目前有 `异步社区` + `当当网` + `京东` 三个链接，按 `<!-- 顺序：异步社区 → 当当网 → 京东 -->` 这种"出版社 → 综合电商 → 自营电商"的逻辑排列。每个 badge 都是 `<a class="shop-badge" target="_blank" rel="noopener noreferrer" href="...">text</a>` 形态，**京东链接必须去掉推广追踪参数**（`extension_id` / `jd_pop` / `abt`），只留商品页主体 `https://item.jd.com/<id>.html`，避免把联盟账号标识暴露到公开仓库的 commit 历史里。

### 修改联系区邮箱

联系区展示两个邮箱（QQ + Gmail）并列：
- QQ 邮箱：`owl2008@qq.com` + 国内 标签
- Gmail：`jie.owl2008@gmail.com` + 国际 标签

`index.htm` 搜索 `contact-email` 修改对应 `<p>` 块。

### 修改社交链接

**两处展示位置**，顺序必须保持一致（QQ → GitHub → 码云 → 微博 → 豆瓣 → X → Facebook）：
- Hero 区（`index.htm` 搜索 `class="hero-social"`）
- 联系区（搜索 `class="contact-social"`）

图标定义在 SVG sprite 顶部（搜索 `<svg xmlns`）。新增图标：到 simple-icons CDN 下载对应 `.svg`，提取 `<path d="...">` 内联为 `<symbol id="i-xxx">`。

## 关键设计约定

### 字体

- **标题（`.content-heading` h2 / `.sub-heading` h3/h4）**：`var(--font-serif)` = `Noto Serif SC` → `Source Han Serif SC` → `Songti SC` → `STSong` → `SimSun` → Georgia → serif
- **正文**：`var(--font-sans)` = `Noto Sans SC` → `PingFang SC` → `Microsoft YaHei` → `Helvetica Neue` → Arial → sans-serif

若 Noto Serif SC 在国内访问慢，可考虑：1) 增加 preload，2) 用国内字体镜像，3) 仅用系统衬线字体。

### 颜色变量

`style.css` 的 `:root` 定义浅色变量；`[data-bs-theme="dark"]` 覆写深色。**深色为默认**（首次访问即深色），用户切换后会存 localStorage。

主要变量：
- `--tw-bg` / `--tw-surface`：背景
- `--tw-text` / `--tw-muted`：正文 / 弱化
- `--tw-accent` / `--tw-accent-light`：强调色（棕色系）
- `--tw-heading`：标题色
- `--tw-border` / `--tw-code-bg`：边框 / 代码块背景

### 间距

- `section` 上下 padding 3rem
- `content-card` padding 2rem
- 区块标题 `.content-heading`：宋体 1.5rem，无下边框（已移除）
- 区块子标题 `.sub-heading`：宋体 1.1rem，`margin-top: 1.5rem; margin-bottom: 1rem`
- 段落行高 1.8，`.content-card p` 限宽 `max-width: 70ch`

### 交互

- **入场动画**：`section` 滚动到视口时渐入（IntersectionObserver）
- **Hero 入场**：元素依次上滑（CSS `@keyframes`，0.1s/0.2s/.../0.6s 错峰）
- **主题切换**：CSS `transition` 0.4s 颜色过渡
- **滚动**：CSS `scroll-behavior: smooth`，section 有 `scroll-margin-top: 70px` 防 sticky 导航遮挡
- **阅读进度条**：顶部 3px 渐变细线（`#readingProgress`）
- **回到顶部**：滚动 > 400px 时显示
- **Tab hash 路由**：URL `#works-original` / `#works-translation` 直接激活对应 Tab

## 关键文件说明

### `index.htm`

- `<head>`：SEO meta、OG、Twitter Card、JSON-LD（Person + 15 Books）、preconnect、Bootstrap CSS、Google Fonts、style.css
- `<body>` 开头：阅读进度条 `<div id="readingProgress">`
- SVG sprite：所有图标内联（`<symbol id="i-xxx">`），通过 `<use href="#i-xxx">` 引用
- 主体结构：
  - `<header>`：sticky 导航（锚点：#about / #works / #posts / #contact）+ 主题切换 + 移动汉堡菜单
  - `<section class="hero" id="top">`：Hero 首屏
  - `<main>`：#about（简介+侧栏） / #works（作品） / #posts（文章） / #contact（联系）
  - `<button id="backToTop">`：回到顶部
  - `<footer>`：快速锚点 + 版权
- `<script>`：bootstrap.bundle.min.js → main.js

### `css/style.css`

组织顺序：变量 → 基础样式 → 响应式 → 导航 → Hero → 区块 → 时间线 → 技能 → 文章 → 联系 → 回到顶部 → 页脚 → 滚动动画。

每节有 `/* ---------- */` 注释，便于定位。

### `js/main.js`

IIFE 形式，关键函数：
- `getPreferredTheme()`：返回 "dark" 为默认（除非 localStorage 有）
- `applyTheme()`：切换 `data-bs-theme`
- `loadBooks()` / `loadPosts()`：fetch JSON + 渲染
- `initReveal()` / `initBackToTop()` / `initReadingProgress()` / `initTabHash()`：交互初始化

### `books.json` / `posts.json`

- books 按 type 过滤（original/translation）
- posts 直接渲染
- 加载失败时控制台会报错，页面降级为空

## 社交图标顺序约定

**数据源**：`data/social-links.json` 是社交图标的唯一数据源；`js/main.js` 的 `renderSocial()` 会把同一份 JSON 渲染到 Hero（`#hero-social`）和联系区（`#contact-social`）。修改顺序只需编辑该 JSON，不要在 `index.htm` 中重复维护——空 `<ul>` 占位即可。

**统一顺序**（Hero 与联系区必须一致，由 JSON 决定）：
1. QQ 邮箱（mailto）
2. GitHub
3. 码云
4. 微博
5. 豆瓣
6. X (Twitter)
7. Facebook

Gmail 不在图标列表（已用文字邮箱地址 + 标签在联系区独立展示）。

新增条目：到 simple-icons CDN 下载对应 `.svg`，提取 `<path d="...">` 内联为 `<symbol id="i-xxx">`，再在 `data/social-links.json` 加一项（id 必须与 symbol 一致）。

## 易踩坑点

1. **豆瓣图床防盗链**：**不可** 直接在 `<img src="https://img.doubanio.com/...">` 外链，403。必须下载到本地 `img/books/`。
2. **微信公众号/微博链接**：`target="_blank"` 必加 `rel="noopener noreferrer"`。
3. **头像/favicon**：源文件是 `me.png`，favicon 系列（16/32/180/192/512）必须**用 Pillow 从 me.png 重新生成**，否则浏览器标签页与实际头像不一致。
4. **深色模式默认**：用户首次访问就是深色，主题切换会存 localStorage。如需重置，清除 localStorage 即可。
5. **GitHub Pages 部署**：gh-pages 分支，push 后自动部署。
6. **CNAME 文件**：保持不变（`www.owlman.cn`），删除会导致域名失效。
7. **本地测试 CSS 修改**：浏览器可能缓存旧 CSS，刷新时**加查询参数**（如 `index.htm?v=2`）强制重新加载，避免看到陈旧版本误导。
8. **联系区分隔线**：用 `border-top` 不用 `::before + position: absolute`（后者在 `inline-flex` 父元素中会出现 60% 宽度居中偏移问题）。
9. **社交图标顺序**：Hero 和联系区两处必须保持完全一致。

## 数据获取小贴士

### 书籍封面（服务端下载 + 转换）

```powershell
$headers = @{Referer="https://book.douban.com/"; UserAgent="Mozilla/5.0"}
Invoke-WebRequest "https://img.doubanio.com/view/subject/l/public/s<id>.jpg" `
  -OutFile "img/books/<id>.jpg" -Headers $headers
```

```python
# 转 WebP、限宽 400
from PIL import Image
im = Image.open("img/books/<id>.jpg").convert("RGB")
w, h = im.size
if w > 400:
    h = round(h * 400 / w); w = 400
    im = im.resize((w, h), Image.LANCZOS)
im.save("img/books/<id>.webp", "WEBP", quality=80, method=6)
```

### 出版年份（批量）

```powershell
$ids = @(10483528, 11580452, 21372235, ...)
foreach ($id in $ids) {
  $html = Invoke-WebRequest "https://book.douban.com/subject/$id/" -UserAgent $ua
  $year = if ($html.Content -match "(\d{4})[-/]\d{1,2}[-/]\d{1,2}") { $matches[1] }
  Write-Output "$id => $year"
}
```

### 文章日期

`博客园` 列表页不显示日期，需访问每篇文章页，正文前有 `20\d{2}-\d{2}-\d{2}` 格式。

## 主要重构历史

| 日期 | 改动 |
|------|------|
| 2019-2022 | 原版（无依赖，纯 HTML+CSS） |
| 2026-07 | Bootstrap 5 重构响应式布局 |
| 2026-07 | 全面设计重构：Hero / 衬线体 / 时间线 / 作品墙 / 文章 / 联系 |
| 2026-07 | 技术优化：本地化 Bootstrap / SVG sprite / 字体优化 / SEO / JSON-LD / WebP |
| 2026-07 | 交互增强：深色模式 / 滚动动画 / 阅读进度 / 回到顶部 / Tab hash 路由 |
| 2026-07 | 头像从 owl.png 改为 me.png（人像） |
| 2026-07 | 深色模式设为默认 |
| 2026-07 | 作品封面加出版年份徽章 + 正文阅读宽度优化 |
| 2026-07 | favicon 重新生成自 me.png |
| 2026-07 | QQ 邮箱加入社交图标首位 |
| 2026-07 | 联系区双邮箱并列（国内/国际 标签） |
| 2026-07 | 社交图标顺序统一（Hero 与联系区一致） |
| 2026-07 | 修复联系我标题下方横线歪斜（border-top 替代 ::before） |
| 2026-07 | 移除一级标题下边框（更简洁） |
| 2026-07 | 新增 MAINTENANCE.md 维护指南 |
| 2026-07 | 引入 books.schema.json / posts.schema.json 校验数据 |
| 2026-07 | 社交图标改由 data/social-links.json 数据驱动（消除两处硬编码） |
| 2026-07 | 修复 about 侧栏多余 `</ul>` 闭合 |
| 2026-07 | 统一书籍封面命名（OpenClaw 改为豆瓣 ID `38549104.webp`） |
| 2026-07 | 引入 `tools/play_owlman.py` 作为项目专用评估工具（Playwright 抓取 + JSON Schema 校验 + 报告输出） |
| 2026-07 | 引入 `tools/fetch_posts.py` 抓取博客园首页同步 `posts.json`，`play_owlman.py --fetch` 一键串起抓取+校验 |
| 2026-07 | 代表作新增京东购买链接（异步社区 → 当当网 → 京东） |
| 2026-07 | 清理 `.gitignore` Eclipse/JDT/CDT 模板残留，仅保留项目相关条目 |
| 2026-07 | 引入 `tools/build_sitemap.py` 从 books/posts 合成 sitemap.xml（26 URL），`play_owlman.py` 内建一致性校验 |
| 2026-07 | 引入 `tools/build_jsonld.py` 从 books.json 生成 JSON-LD Books 列表（消除 15 本书的双源 drift），`check.sh` 加校验 |
| 2026-07 | 字体本地化：Noto Serif SC 子集化到 633 CJK + 52 Latin 字符，woff2 存放 `vendor/fonts/`，告别 Google Fonts CDN |
| 2026-07 | 修复 HTML skill-tag 与 JSON-LD knowsAbout 字面不一致（`AI / Agent` → `AI 与 Agent`） |

## 评估工具

`tools/play_owlman.py` 是本项目的专用评估工具，四步校验一次完成：

1. **JSON Schema 校验**：`books.json`、`posts.json`、`data/social-links.json` 必须通过各自的 schema。
2. **文件存在性校验**：`books.json` 中 `cover` 字段指向的图片必须真实存在。
3. **sitemap 一致性**：`sitemap.xml` 必须包含 `books.json` + `posts.json` 的全部 URL。
4. **Playwright 抓取线上版**：访问 `https://owlman.cn`，渲染后输出 Markdown 摘要 + 全页截图，便于发现仅在运行时显现的问题。

默认输出落在 `D:\Documents\working\notes\owlman_cn_render.md` 与 `owlman_cn_full.png`；可用 `--output-dir` 改写到项目内 `out/`：

```bash
python tools/play_owlman.py --output-dir out
```

加 `--fetch` 会先调用 `tools/fetch_posts.py` 同步博客园数据再校验；`--skip-live` 只跑本地校验、不开浏览器。脚本结束会在 stdout 给出汇总表；任何 schema 校验失败都会以非 0 退出码报错。

## 博客同步工具

`tools/fetch_posts.py` 是博客园文章列表的同步工具。从 `https://www.cnblogs.com/owlman/` 抓取首页（或前 N 页）文章，按发布时间降序排列，生成符合 `posts.schema.json` 的 JSON，默认直接覆盖 `MyHome/posts.json`。

内部解析策略：

- 标题 + URL：`<a class="postTitle2 ..." href="...">...</a>`，去标签后 trim 空白
- 日期：`posted @ YYYY-MM-DD HH:MM`（cnblogs footer 行内），只取日期部分
- 分页：`?page=N`，按 URL 去重合并
- 写文件前过一遍 `jsonschema.validate()`，失败不写

依赖 `requests`（环境装一下即可）。一次命令等价于原来手工粘贴标题/URL/日期的流程。

## 字体子集化工具

`tools/subset_font.py` 管理 Noto Serif SC 本地字体。

**原理**：Google Fonts API v1 的 `text=` 参数做服务端子集化，下载预子集 TTF → 本地转 woff2 存 `vendor/fonts/`。

**触发条件**：新增文章或修改 HTML 引入了新 CJK 字符时，需要重跑。

```bash
python tools/subset_font.py              # 下载 + 子集化
python tools/subset_font.py --dry-run    # 只看字符统计
```

字体引用在 `css/style.css` 顶部的 `@font-face`，指向 `vendor/fonts/noto-serif-sc-{400,700}.woff2`。`index.htm` 已移除 Google Fonts CDN 的 `<link>` 和 `preconnect`。

## 已知限制

- **Noto Serif SC 走 Google Fonts CDN**，国内访问可能较慢
- **Noto Serif SC 已本地化**：`tools/subset_font.py` 从 Google Fonts 下载预子集 TTF，覆盖项目中全部 633 个 CJK + 52 个 Latin 字符，转 woff2 存放于 `vendor/fonts/`（400 + 700 两规格）。`style.css` 顶部 `@font-face` 引用本地路径，`index.htm` 不再引入 Google Fonts CDN
- **字体会随内容增加而漂移**：若新增文章或修改 HTML 引入了新字符，需重跑 `python tools/subset_font.py` 更新字体（`play_owlman.py` 会检查缺失字符但不会自动重建字体）
- **Bootstrap 227KB 未裁剪**（PurgeCSS Windows 路径兼容问题已放弃，缓存后问题不大）
- **无 PWA Service Worker**（仅 manifest）
- **无评论/留言功能**（个人主页不必要）