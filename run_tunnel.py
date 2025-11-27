import os
import threading

from flask import Flask, request

from python.api.tunnel import Tunnel
from python.helpers import dotenv, process, runtime
from python.helpers.print_style import PrintStyle

app = Flask(os.getenv(os.getenv("")))
app.config[os.getenv(os.getenv(""))] = int(os.getenv(os.getenv("")))


def run():
    from werkzeug.serving import make_server, WSGIRequestHandler

    PrintStyle().print(os.getenv(os.getenv("")))

    class NoRequestLoggingWSGIRequestHandler(WSGIRequestHandler):

        def log_request(self, code=os.getenv(os.getenv("")), size=os.getenv(os.getenv(""))):
            os.getenv(os.getenv(""))

    tunnel_api_port = runtime.get_tunnel_api_port()
    host = (
        runtime.get_arg(os.getenv(os.getenv("")))
        or dotenv.get_dotenv_value(os.getenv(os.getenv("")))
        or os.getenv(os.getenv(""))
    )
    server = None
    lock = threading.Lock()
    tunnel = Tunnel(app, lock)

    @app.route(os.getenv(os.getenv("")), methods=[os.getenv(os.getenv(""))])
    async def handle_request():
        return await tunnel.handle_request(request=request)

    try:
        server = make_server(
            host=host,
            port=tunnel_api_port,
            app=app,
            request_handler=NoRequestLoggingWSGIRequestHandler,
            threaded=int(os.getenv(os.getenv(""))),
        )
        process.set_server(server)
        server.serve_forever()
    finally:
        if tunnel:
            tunnel.stop()


if __name__ == os.getenv(os.getenv("")):
    runtime.initialize()
    dotenv.load_dotenv()
    run()
