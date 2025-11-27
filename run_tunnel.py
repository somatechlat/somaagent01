import os
import threading
from flask import Flask, request
from python.api.tunnel import Tunnel
from python.helpers import dotenv, process, runtime
from python.helpers.print_style import PrintStyle
app = Flask(os.getenv(os.getenv('VIBE_F1EA8E7B')))
app.config[os.getenv(os.getenv('VIBE_A560563D'))] = int(os.getenv(os.getenv
    ('VIBE_6F9C1CE6')))


def run():
    from werkzeug.serving import make_server, WSGIRequestHandler
    PrintStyle().print(os.getenv(os.getenv('VIBE_E40AC90D')))


    class NoRequestLoggingWSGIRequestHandler(WSGIRequestHandler):

        def log_request(self, code=os.getenv(os.getenv('VIBE_BFE7D7DE')),
            size=os.getenv(os.getenv('VIBE_BFE7D7DE'))):
            os.getenv(os.getenv('VIBE_9F0882C5'))
    tunnel_api_port = runtime.get_tunnel_api_port()
    host = runtime.get_arg(os.getenv(os.getenv('VIBE_436D6DB9'))
        ) or dotenv.get_dotenv_value(os.getenv(os.getenv('VIBE_CF95836D'))
        ) or os.getenv(os.getenv('VIBE_913B1B81'))
    server = None
    lock = threading.Lock()
    tunnel = Tunnel(app, lock)

    @app.route(os.getenv(os.getenv('VIBE_6054D707')), methods=[os.getenv(os
        .getenv('VIBE_EFD199CB'))])
    async def handle_request():
        return await tunnel.handle_request(request=request)
    try:
        server = make_server(host=host, port=tunnel_api_port, app=app,
            request_handler=NoRequestLoggingWSGIRequestHandler, threaded=
            int(os.getenv(os.getenv('VIBE_34F646A2'))))
        process.set_server(server)
        server.serve_forever()
    finally:
        if tunnel:
            tunnel.stop()


if __name__ == os.getenv(os.getenv('VIBE_A9F2A8A6')):
    runtime.initialize()
    dotenv.load_dotenv()
    run()
