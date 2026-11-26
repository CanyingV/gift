# 礼记

轻量本地礼单记录应用，页面与 API 由 Python 标准库提供，数据库操作使用 peewee ORM，数据保存在当前目录的 SQLite 文件中。

## 启动

需要 Python 3.9 或更新版本。首次运行先安装依赖：

```sh
pip install -r requirements.txt
python3 app.py
```

然后打开 http://127.0.0.1:8765。页面、服务和 SQLite 均在本机运行，无需网络连接。建议先备份 `gift` 数据库文件。

## 项目结构

```
app.py              薄入口（兼容桌面版 / Android 版）
server/             后端按模块拆分
  config.py         路径与环境变量
  models.py         peewee ORM 模型
  repository.py     数据访问（增删改查、聚合、排序）
  importer.py       Excel 导入
  exporter.py       Excel 导出与模板
  xlsx.py           xlsx 读写工具
  handler.py        HTTP 路由与静态资源
templates/          前端页面模板（每个页面一个 HTML）
static/             样式与脚本，按页面拆分到 static/js/pages/
desktop.py          macOS / Windows 桌面壳
android/            Android 壳（构建时自动同步后端包与前端资源）
```

## 路由与数据加载

所有 RESTful 接口集中定义在 `server/routes.py`，按模块分组；`server/handler.py` 只负责通用分发，不再写 if/elif 路由。

前端使用 hash 路由，进入哪个页面才请求哪个页面的数据，不再启动时一次性拉取全部数据：

| 页面路由 | 请求接口 |
| --- | --- |
| `#/dashboard` | `GET /api/dashboard`（汇总 + 最近 5 条礼单/随礼） |
| `#/bills` | `GET /api/bills`（礼单列表） |
| `#/bills/<id>` | `GET /api/bills/<id>`（单个礼单及其人员） |
| `#/expenses` | `GET /api/expenses`（随礼记录） |
| `#/stats` | `GET /api/stats`（聚合后的统计结果） |

API 一览：

| 模块 | 方法与路径 |
| --- | --- |
| 页面聚合 | `GET /api/dashboard`、`GET /api/stats` |
| 礼单 | `GET/POST /api/bills`、`GET/PUT/DELETE /api/bills/{id}` |
| 收礼人员 | `GET/POST /api/bills/{id}/people`、`GET/PUT/DELETE /api/people/{id}` |
| 随礼 | `GET/POST /api/expenses`、`GET/PUT/DELETE /api/expenses/{id}` |
| 关系 / 分类 | `GET/POST /api/relations`、`PUT/DELETE /api/relations/{id}`；分类同理为 `/api/categories` |
| 导入 / 导出 / 模板 | `POST /api/imports/{bills,expenses}`、`GET /api/exports/{bills,expenses}`、`GET /api/templates/{bills,expenses}` |

页面模板也按路由按需加载并缓存；新增/编辑/删除后只刷新当前页，浏览器前进后退会回到对应页面并重新取数。

## 打包成 apk / exe / dmg

三个平台都通过 GitHub Actions 云端构建，无需在本机安装 Android SDK 或 Windows 环境。Chaquopy 自 12.0.1 起已开源免费，无许可限制。

**步骤**

1. 把本目录初始化为 git 仓库并推送到 GitHub（若尚未推送）：

   ```sh
   git init && git add . && git commit -m "礼单管家"
   git remote add origin <你的仓库地址>
   git push -u origin main
   ```

2. 打开仓库的 **Actions** 页，允许工作流运行；在左侧选择「打包三端安装包」，点击 **Run workflow**。也可以直接推送一个 `v` 开头的标签（如 `git tag v1.0.0 && git push origin v1.0.0`）自动触发。

3. 构建完成后，在对应本次运行的页面底部 **Artifacts** 处分别下载（对外分享请到 Releases 页）。注：Release 附件用拼音文件名，因为 GitHub 会把中文附件名改写成 `default.xxx`：

   - `礼记-Windows-exe` → `Liji-Windows.exe`（Windows）
   - `礼记-macOS-dmg` → `Liji-macOS.dmg`（macOS，双击挂载后拖入「应用程序」；首次打开需在「系统设置 → 隐私与安全性」点「仍要打开」）
   - `礼记-Android-apk` → `Liji-Android.apk`（Android，安装时允许安装未知来源应用）

**产物说明**

- 桌面版数据存于用户目录（Windows 为 `%APPDATA%/礼记`，macOS 为 `~/Library/Application Support/礼记`），首次启动会把仓库中的 `gift` 作为初始数据复制过去，之后升级不会覆盖已有记录。
- Android 版数据存于应用私有目录，同样仅首次解包数据库。
- 安装包首次构建需下载 Gradle 9.6、Android SDK 与 Python 运行时，耗时较长，属正常现象。

**本机直接运行桌面版**（需先安装依赖与 `pywebview`）：

```sh
pip install -r requirements.txt pywebview
python3 desktop.py
```
