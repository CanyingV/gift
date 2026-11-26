"""HTTP 入口：静态资源由标准库提供，API 统一交给 routes.py 的路由表分发。"""
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from .config import BASE
from .models import db, init_db
from .routes import Response, dispatch


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=BASE, **kw)

    def _body(self):
        length = int(self.headers.get('Content-Length', 0))
        if not length:
            return {}
        try:
            return json.loads(self.rfile.read(length) or b'{}')
        except (ValueError, UnicodeDecodeError):
            return {}

    def _send(self, resp):
        self.send_response(resp.status)
        for key, value in resp.headers.items():
            self.send_header(key, value)
        self.send_header('Content-Length', str(len(resp.body)))
        self.end_headers()
        if resp.body:
            self.wfile.write(resp.body)

    def _api(self, method):
        parsed = urlparse(self.path)
        body = self._body() if method in ('POST', 'PUT', 'PATCH', 'DELETE') else {}
        try:
            with db.connection_context():
                resp = dispatch(method, parsed.path, body, parse_qs(parsed.query))
        except Exception as exc:
            payload = json.dumps({'ok': False, 'error': '服务器错误：' + str(exc)},
                                 ensure_ascii=False).encode()
            resp = Response(payload, 500, {'Content-Type': 'application/json; charset=utf-8'})
        self._send(resp)

    def do_GET(self):
        path = urlparse(self.path).path
        if path.startswith('/api/'):
            return self._api('GET')
        if path == '/':
            self.path = '/templates/index.html'  # 布局骨架在 templates 目录
        if path.startswith('/server/'):
            self.send_error(403)
            return
        return super().do_GET()

    def do_POST(self):
        self._api('POST')

    def do_PUT(self):
        self._api('PUT')

    def do_DELETE(self):
        self._api('DELETE')


def run_server(host='127.0.0.1', port=8765):
    init_db()
    print('礼单管理已启动: http://%s:%d' % (host, port))
    ThreadingHTTPServer((host, port), Handler).serve_forever()
