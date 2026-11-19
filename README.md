# 礼单管家

轻量本地礼单记录应用，使用 Python 标准库提供页面与 API，数据保存在当前目录的 SQLite 文件 `gift`。应用直接使用已有 `gift`（礼单）、`income`（礼单明细，按 `gift_id` 关联）、`cate` 和 `relation` 表，不创建业务表。随礼数据使用 `expensex`；兼容当前数据库中的旧表名 `expenses`。

## 启动

需要 Python 3.9 或更新版本。在此目录运行：

```sh
python3 app.py
```

然后打开 http://127.0.0.1:8765。页面、服务和 SQLite 均在本机运行，无需网络连接。建议先备份 `gift` 数据库文件。

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

3. 构建完成后，在对应本次运行的页面底部 **Artifacts** 处分别下载：

   - `礼单管家-Windows-exe` → `礼单管家.exe`（Windows）
   - `礼单管家-macOS-dmg` → `礼单管家.dmg`（macOS，双击挂载后拖入「应用程序」；首次打开需在「系统设置 → 隐私与安全性」点「仍要打开」）
   - `礼单管家-Android-apk` → `app-debug.apk`（Android，安装时允许安装未知来源应用）

**产物说明**

- 桌面版数据存于用户目录（Windows 为 `%APPDATA%/礼单管家`，macOS 为 `~/Library/Application Support/礼单管家`），首次启动会把仓库中的 `gift` 作为初始数据复制过去，之后升级不会覆盖已有记录。
- Android 版数据存于应用私有目录，同样仅首次解包数据库。
- 安装包首次构建需下载 Gradle 9.6、Android SDK 与 Python 运行时，耗时较长，属正常现象。

**本机直接运行桌面版**（需先安装 `pywebview`）：

```sh
pip install pywebview
python3 desktop.py
```
