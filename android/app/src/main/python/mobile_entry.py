"""在 Android 进程内启动礼单管家本地服务，立即返回监听端口。"""
import os
import socket
import threading

_server = None
_port = None


def _free_port():
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port


def start(base_dir, db_path):
    """base_dir: assets 解包后的静态资源目录；db_path: 可写数据库路径。"""
    global _server, _port
    if _server is not None:
        return _port
    os.environ['GIFT_BASE_DIR'] = base_dir
    os.environ['GIFT_DB_PATH'] = db_path
    import app  # 环境变量设置完成后再导入
    from http.server import ThreadingHTTPServer
    _port = _free_port()
    _server = ThreadingHTTPServer(('127.0.0.1', _port), app.Handler)
    threading.Thread(target=_server.serve_forever, daemon=True).start()
    return _port
