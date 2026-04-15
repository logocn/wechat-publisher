# 微信公众号自动发布

用 GitHub Actions 自动发布文章到微信公众号草稿箱，解决 IP 白名单问题。

## 使用方法

### 1. 准备文章

把 Markdown 文章放到 `articles/` 文件夹：

```
articles/
  ├── 2024-01-15-文章标题.md
  └── cover.jpg  # 封面图（可选）
```

### 2. 手动发布

1. 进入 GitHub 仓库页面
2. 点 `Actions` 标签
3. 选 `发布微信公众号文章`
4. 点 `Run workflow`
5. 输入文章文件名（如 `articles/文章标题.md`）
6. 点 `Run`

### 3. 自动发布

直接 push 文章到 `articles/` 文件夹，会自动触发发布。

## 文章格式

```markdown
# 文章标题

正文内容...

## 小标题

更多内容...
```

## 配置

在仓库 Settings → Secrets → Actions 里设置：

- `WECHAT_APPID`: 微信公众号 AppID
- `WECHAT_SECRET`: 微信公众号 AppSecret
