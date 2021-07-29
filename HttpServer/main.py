from email.parser import Parser
from email.message import Message
from functools import lru_cache
from json import dumps
from urllib.parse import parse_qs, urlparse
import socket
import sys


MAX_LINE = 64*1024
MAX_HEADERS = 100


class Response:
    def __init__(self, status: int, reason: str, headers: list=None, body: str=None) -> None:
        self.status = status
        self.reason = reason
        self.headers = headers
        self.body = body

class Request:
    def __init__(self, method: str, target: str, version: str, headers: Message, rfile) -> None:
        self.method = method
        self.target = target
        self.version = version
        self.headers = headers
        self.rfile = rfile

    @property    
    def path(self):
        return self.url.path

    @property
    @lru_cache(maxsize=None)
    def query(self):
        return parse_qs(self.url.query)

    @lru_cache(maxsize=None)
    def url(self):
        return urlparse(self.target)

    def body(self):
        size = self.headers.get('Content-Length')
        if not size:
            return None
        return self.rfile.read(size)

class HttpError(Exception):
    def __init__(self, status: int, reason: str, body: str=None):
        super()
        self.status = status
        self.reason = reason
        self.body = body


class HttpServer:
    def __init__(self, host: str, port: int, server_name: str) -> None:
        self._host = host
        self._port = port
        self._server_name = server_name
        self._users = {}

    def serve_forever(self) -> None:
        serv_sock = socket.socket(
            socket.AF_INET,                                 # refers to the address family ipv4
            socket.SOCK_STREAM,                             # TCP-protocol
            proto=0)                                        # protocol number \ default value

        try:
            serv_sock.bind((self._host, self._port))        # assigns an IP address and a port number 
            serv_sock.listen()                              # enable a server to accept connections
            while True:
                conn, _ = serv_sock.accept()                # new socket object for get \ put info

                try:
                    self.serve_client(conn)
                except Exception as e:
                    print('Client serving failed', e)
        finally:
            serv_sock.close()

    def serve_client(self, conn: socket.socket) -> None:
        try:
            req = self.parse_request(conn)                  # получение
            resp = self.handle_request(req)                 # обработка 
            self.send_response(conn, resp)                  # отправление
        except ConnectionResetError:
            conn = None
        except Exception as e:
            self.send_error(conn, e)

        if conn:
            conn.close()


    def parse_request(self, conn: socket.socket) -> Request:
        rfile = conn.makefile('rb')
        method, target, ver = self.parse_request_line(rfile)
        headers = self.parse_headers(rfile)

        host = headers.get('Host')
        if not host:
            raise HttpError(400, 'Bad request', 'Host header is missing')
        if host not in (self._server_name, f'{self._server_name}:{self._port}'):
            raise HttpError(404, 'Not found')

        return Request(method, target, ver, headers, rfile)

    def parse_request_line(self, rfile) -> list:
        raw = rfile.readline(MAX_LINE + 1)
        if len(raw) > MAX_LINE:
             raise HttpError(400, 'Bad request', 'Request line is too long')

        req_line = str(raw, 'iso-8859-1')
        req_line = req_line.rstrip('\r\n')
        words = req_line.split() 
        
        if len(words) != 3:
            raise HttpError(400, 'Bad request', 'Malformed request line')
        if ver != 'HTTP/1.1':
            raise HttpError(505, 'HTTP Version Not Supported')

        return words

    def parse_headers(self, rfile) -> Message:
        headers = []
        while True:
            raw = rfile.readline(MAX_LINE + 1)
            if len(raw) > MAX_LINE:
                raise HttpError(494, 'Header line is too long.')

            if line in (b'\r\n', b'\n', b''):
                break

            headers.append(line)
            if len(headers) > MAX_HEADERS:
                raise HttpError(494, 'Too many headers')

        sheaders = b''.join(headers).decode('iso-8859-1')
        return Parser().parsestr(sheaders)


    def handle_request(self, req: Request) -> Response:
        if req.path == '/users' and req.method == 'POST':
            return self.handle_post_users(req)
        elif req.path == '/users' and req.method == 'GET':
            return self.handle_get_users(req)

        if req.path.startswith('/users/'):
            user_id = req.path[len('/users/'):]
            if user_id.isdigit():
                return self.handle_get_user(req, user_id)
    
        raise HttpError(404, 'Not Found')


    def handle_post_users(self, req: Request) -> Response:
        user_id = len(self._users) + 1
        self._users[user_id] = {'id': user_id,
                                'name': req.query['name'][0],
                                'age': req.query['age'][0]
                                }

        return Response(204, 'Created')

    def handle_get_users(self, req: Request) -> Response:
        accept = req.headers.get('Accept')
        if 'text/html' in accept:
            contentType = 'text/html; charset=utf-8'
            body = '<html><head></head><body>'
            body += f'<div>Пользователи ({len(self._users)})</div>'
            body += '<ul>'
            for u in self._users.values():
                body += f'<li>#{u["id"]} {u["name"]}, {u["age"]}</li>'
            body += '</ul>'
            body += '</body></html>'

        elif 'application/json' in accept:
            contentType = 'application/json; charset=utf-8'
            body = json.dumps(self._users)

        else:
            return Response(406, 'Not Acceptable')

        body = body.encode('utf-8')
        headers = [('Content-Type', contentType), ('Content-Length', len(body))]
        return Response(200, 'OK', headers, body)

    def handle_get_user(self, req: Request, user_id: str) -> Response:
        user = self._users.get(int(user_id))
        if not user:
            return Response(404, 'Not Found')

        accept = req.headers.get('Accept')
        if 'text/html' in accept:
            contentType = 'text/html; charset=utf-8'
            body = '<html><head></head><body>'
            body += f'#{user["id"]} {user["name"]}, {user["age"]}'
            body += '</body></html>'

        elif 'application/json' in accept:
            contentType = 'application/json; charset=utf-8'
            body = json.dumps(user)

        else:
            return Response(406, 'Not Acceptable')

        body = body.encode('utf-8')
        headers = [('Content-Type', contentType), ('Content-Length', len(body))]
        return Response(200, 'OK', headers, body)


    def send_response(self, conn: socket.socket, resp: str) -> None:
        wfile = conn.makefile('wb')
        status_line = f'HTTP/1.1 {resp.status} {resp.reason}\r\n'
        wfile.write(status_line.encode('iso-8859-1'))

        if resp.headers:
            for key, value in resp.headers:
                header_line = f'{key}: {value}\r\n'
                wfile.write(header_line.encode('iso-8859-1'))

        wfile.write(b'\r\n')

        if resp.body:
            wfile.write(resp.body)

        wfile.flush()
        wfile.close()


    def send_error(self, conn: socket.socket, err: HttpError) -> None:
        try:
            status = err.status
            reason = err.reason
            body = (err.body or err.reason).encode('utf-8')
        except:
            status = 500
            reason = b'Internal Server Error'
            body = b'Internal Server Error'

        resp = Response(status, reason, [('Content-Length', len(body))], body)
        self.send_response(conn, resp)


if __name__ == '__main__':
    host = sys.argv[1]
    port = int(sys.argv[2])
    server_name = sys.argv[3]
    
    serv = HttpServer(host, port, server_name)
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        pass

