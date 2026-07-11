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
│   ├── me.png             # 头像（Hero / OG / JSON-LD / 苹果设备除外）
│   ├── owl.png            # 旧 logo（已无引用，保留以备）
│   ├── books/             # 15 本封面（WebP 格式，width 400px）
│   ├── icons/             # SVG 图标（备用，未被 sprite 引用）
│   ├── icon-192.png       # PWA 图标
│   ├── icon-512.png       # PWA 图标
│   ├── apple-touch-icon.png
│   ├── favicon-16.png
│   ├── favicon-32.png
│   ├── read.png / write.jpg / coding.jpg / movie.jpg
│                          # 兴趣图标（已弃用，未删除可作历史）
│   ├── js_guide.png       # 旧精选封面（已弃用，未删除可作历史）
│   └── icons/*.svg        # Simple Icons（已内联进 sprite）
└── vendor/
    └── bootstrap/
        ├── css/bootstrap.min.css
        └── js/bootstrap.bundle.min.js
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

封面获取方法：服务端带 Referer 下载到 `img/books/`，转 WebP（建议 quality 80，width ≤400）。

Tab 角标的数字会自动从 JSON 计数。

### 新增 / 修改博客文章

编辑 `posts.json`：

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

代表作卡片（`index.htm` 搜索 `JavaScript 全栈开发`）的 `.shop-badge` 区。

### 修改社交链接

- Hero 区（`index.htm` 搜索 `class="hero-social"`）和联系区（搜索 `class="contact-social"`）
- 这两处是仅有的社交图标展示位置，**已精简**到 2 处
- 图标定义在 SVG sprite 顶部（搜索 `<svg xmlns`）

## 关键设计约定

### 字体

- **标题（h1-h3）**：`var(--font-serif)` = `Noto Serif SC` → `Source Han Serif SC` → `Songti SC` → `STSong` → `SimSun` → Georgia → serif
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
- 区块标题 `content-heading`：宋体 1.5rem，2px 棕色下划线
- 区块子标题 `sub-heading`：宋体 1.15rem
- 段落行高 1.8

### 交互

- **入场动画**：`section` 滚动到视口时渐入（IntersectionObserver）
- **Hero 入场**：元素依次上滑（CSS `@keyframes`）
- **主题切换**：CSS `transition` 0.4s 颜色过渡
- **滚动**：CSS `scroll-behavior: smooth`，section 有 `scroll-margin-top: 70px` 防 sticky 导航遮挡
- **阅读进度条**：顶部 3px 渐变细线
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

组织顺序：变量 → 基础样式 → 导航 → Hero → 区块 → 时间线 → 技能 → 文章 → 联系 → 回到顶部 → 页脚 → 滚动动画。

每节有 `/* ---------- */` 注释，便于定位。

### `js/main.js`

IIFE 形式，关键函数：
- `getPreferredTheme()`：返回 "dark" 为默认（除非 localStorage 有）
- `applyTheme()`：切换 `data-bs-theme`
- `loadBooks()` / `loadPosts()`：fetch JSON + 渲染
- `initReveal()` / `initBackToTop()` / `initReadingProgress()` / `initTabHash()`：交互初始化

### `books.json` / `posts.json`

- 都按 type 过滤（books）或直接渲染（posts）
- 加载失败时控制台会报错，页面降级为空

## 易踩坑点

1. **豆瓣图床防盗链**：**不可** 直接在 `<img src="https://img.doubanio.com/...">` 外链，403。必须下载到本地 `img/books/`。
2. **微信公众号/微博链接**：`target="_blank"` 必加 `rel="noopener noreferrer"`。
3. **Hero 头像**：必须用 `me.png`（1024×1360），`owl.png` 已弃用但作为 favicon 源文件保留。
4. **深色模式默认**：用户首次访问就是深色，主题切换会存 localStorage。如需重置，清除 localStorage 即可。
5. **GitHub Pages 部署**：gh-pages 分支，push 后自动部署。
6. **CNAME 文件**：保持不变（`www.owlman.cn`），删除会导致域名失效。

## 数据获取小贴士

### 书籍封面

```bash
Invoke-WebRequest "https://img.doubanio.com/view/subject/l/public/s<id>.jpg" `
  -OutFile "img/books/<id>.jpg" `
  -Headers @{Referer="https://book.douban.com/"}
# 然后用 Python PIL 转为 WebP、限宽 400：
# im = Image.open(src).convert("RGB")
# im = im.resize((400, h), Image.LANCZOS)
# im.save(dst, "WEBP", quality=80)
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

## 已知限制

- **Noto Serif SC 走 Google Fonts CDN**，国内访问可能较慢
- **Bootstrap 227KB 未裁剪**（PurgeCSS Windows 路径兼容问题已放弃，缓存后问题不大）
- **社交媒体仅 Hero + 联系区两处**（已精简），如需添加回导航/页脚，需改 `<li class="navbar-social">` 类
- **无 PWA Service Worker**（仅 manifest）
- **无评论/留言功能**（个人主页不必要）
- **lang="zh-cn"**：规范推荐 `zh-CN`（大写），但浏览器均能识别
