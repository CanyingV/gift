"""礼记桌面版入口：用原生窗口承载本地 HTTP 服务。"""
import os
import sys
import shutil
import socket
import threading


def resource_path(rel=''):
    """PyInstaller 打包后资源释放到 _MEIPASS，开发态直接用脚本目录。"""
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, rel) if rel else base


def user_data_dir():
    name = '礼记'
    if sys.platform == 'win32':
        base = os.environ.get('APPDATA') or os.path.expanduser('~')
    elif sys.platform == 'darwin':
        base = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support')
    else:
        base = os.environ.get('XDG_DATA_HOME') or os.path.join(os.path.expanduser('~'), '.local', 'share')
    path = os.path.join(base, name)
    os.makedirs(path, exist_ok=True)
    return path


def prepare():
    """把随包分发的初始数据库复制到用户目录，后续数据都写这里。"""
    data_dir = user_data_dir()
    db = os.path.join(data_dir, 'gift')
    if not os.path.exists(db):
        seed = resource_path('gift')
        if os.path.exists(seed):
            shutil.copy2(seed, db)
    os.environ['GIFT_BASE_DIR'] = resource_path()
    os.environ['GIFT_DB_PATH'] = db
    return db


def pick_port():
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port


def main():
    prepare()
    import app  # 必须在设置环境变量之后导入
    from http.server import ThreadingHTTPServer

    port = pick_port()
    server = ThreadingHTTPServer(('127.0.0.1', port), app.Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    import webview
    webview.create_window('礼记', 'http://127.0.0.1:%d/' % port,
                          width=1240, height=820, min_size=(900, 600))
    try:
        webview.start()
    finally:
        server.shutdown()
        server.server_close()


if __name__ == '__main__':
    main()
