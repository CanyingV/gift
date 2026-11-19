# 礼单管家

轻量本地礼单记录应用，使用 Python 标准库提供页面与 API，数据保存在当前目录的 SQLite 文件 `gift`。应用直接使用已有 `gift`（礼单）、`income`（礼单明细，按 `gift_id` 关联）、`cate` 和 `relation` 表，不创建业务表。随礼数据使用 `expensex`；兼容当前数据库中的旧表名 `expenses`。

## 启动

需要 Python 3.9 或更新版本。在此目录运行：

```sh
python3 app.py
```

然后打开 http://127.0.0.1:8765。页面、服务和 SQLite 均在本机运行，无需网络连接。建议先备份 `gift` 数据库文件。

## 打包

桌面版可用 PyInstaller 将 Python 服务和页面资源打成可执行文件；各平台需在对应系统分别构建。Android APK 需要 WebView 壳并配置 Android SDK。当前提供离线可运行源码，尚未生成安装包。
