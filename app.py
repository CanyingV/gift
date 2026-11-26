"""礼记本地服务入口。

后端实现按模块放在 server/ 包中，本文件保留为薄入口，兼容 desktop.py、
android 端 mobile_entry.py 以及 `python3 app.py` 的既有用法。
"""
from server.handler import Handler, run_server
from server.models import init_db

# 桌面 / Android 入口会在导入本模块前设置好 GIFT_BASE_DIR / GIFT_DB_PATH
init_db()

__all__ = ['Handler', 'run_server', 'init_db']


if __name__ == '__main__':
    run_server()
