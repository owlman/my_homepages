# 项目说明

> 最后更新：2026-08-11

www.owlman.cn 是一个以"外链聚合"为核心的个人主页，汇聚本人日常使用的博客、GitHub、出版书籍等信息，以供交流之用。

## 技术说明

- 纯静态站点（HTML5 + CSS3 + 原生 JavaScript）
- 布局与组件：Bootstrap 5.3.3（本地化到 `vendor/`）
- 图标：内联 SVG sprite
- 字体：Noto Serif SC（Google Fonts CDN，系统字体后备）
- 部署：GitHub Pages + `CNAME` 自定义域名
- 响应式布局，桌面端双栏、移动端单列

## 维护

请参考 [MAINTENANCE.md](./MAINTENANCE.md)：
- 内容更新（书籍、文章、个人简介）
- 设计约定与配色变量
- 关键文件说明
- 常见坑（豆瓣图床防盗链等）

### 同步博客园文章

`posts.json` 由 `tools/fetch_posts.py` 自动从博客园抓取，无需手工维护：

```bash
python tools/fetch_posts.py            # 抓首页 10 篇，直接写 posts.json
python tools/play_owlman.py --fetch    # 抓取 + 校验（schema + 封面 + 可选线上渲染）
```

### 新增一本书

新书条目要同步 3 处（以最近新增的《OpenClaw 快速上手》subject `38549104` 为例）：

1. **`books.json`**：追加 `{ "title": ..., "url": "https://book.douban.com/subject/38549104/", "type": "original", "cover": "img/books/38549104.webp", "w": 400, "h": 580, "year": 2026 }` 等字段
2. **`img/books/38549104.webp`**：与 `books.json` 中 `cover` 字段路径一致；文件名采用豆瓣 subject ID
3. **`index.htm`** JSON-LD：在 `@graph` 数组（约第 94 行起）追加对应 `{@type: "Book"}` 条目

### 启用 pre-push 校验

clone 出新工作区后手动安装钩子，让 push 前自动跑 schema / 链接校验：

```bash
bash tools/install-hook.sh
```

## 联系方式

如对项目有兴趣或有任何意见，可通过以下方式联系：
- E-mail: `jie.owl2008[at]gmail[dot]com`
- 微博: [凌杰](https://weibo.com/owlman)
- X: [@lingjieowl](https://twitter.com/lingjieowl)

## 版权

本项目过于简单，不作任何声明，任何人都可以随意使用项目中的代码，不必告知本人。
