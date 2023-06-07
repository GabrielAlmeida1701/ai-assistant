import json
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
from assistant import conversation_handler, logger
from assistant.data_manager import load_settings, save_settings
from assistant.gpt_loader import model_loader


SERVER_PORT = 6969

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/chat':
            anwser = conversation_handler.get_last_message()
            response = json.dumps(anwser)

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(response.encode('utf-8'))

        if self.path.startswith('/api/settings'):
            parsed_url = urlparse(self.path)
            params = parse_qs(parsed_url.query)

            key = params['key'][0]
            settings = load_settings(key)
            result = {
                'key': key,
                'settings': settings
            }
            response = json.dumps(result)

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(response.encode('utf-8'))
        else:
            self.send_error(404)

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        decoded_data = urllib.parse.unquote(post_data)
        body = json.loads(decoded_data)

        if self.path == '/api/chat':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()

            message = body['text']
            anwser = conversation_handler.ask_yumi(message)
            response = json.dumps(anwser)

            self.wfile.write(response.encode('utf-8'))
        if self.path == '/api/settings':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()

            key = body['key']
            settings = body['settings']
            save_settings(key, settings)

            response = json.dumps({ 'success': True })
            self.wfile.write(response.encode('utf-8'))
        else:
            self.send_error(404)

try:
    server = ThreadingHTTPServer(('127.0.0.1', SERVER_PORT), Handler)
    logger.info(f'Starting server at http://127.0.0.1:{SERVER_PORT}')
    server.serve_forever()
except KeyboardInterrupt:
    pass
except Exception as e:
    logger.error(str(e))
finally:
    model_loader.clear_torch_cache()