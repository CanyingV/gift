"""路径与全局配置。

桌面版 / Android 版会在导入本包之前设置 GIFT_BASE_DIR、GIFT_DB_PATH，
因此这里只在模块加载时读取一次环境变量。
"""
import os

# 静态资源根目录；默认是项目根目录（app.py 所在位置）
BASE = os.environ.get('GIFT_BASE_DIR') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# SQLite 数据库路径；默认位于静态资源根目录，与旧版保持一致
DB_PATH = os.environ.get('GIFT_DB_PATH') or os.path.join(BASE, 'gift')

TEMPLATES_DIR = os.path.join(BASE, 'templates')
STATIC_DIR = os.path.join(BASE, 'static')
