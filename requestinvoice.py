from lnd_grpc import lightning_pb2 as ln
from lnd_grpc import lightning_pb2_grpc as lnrpc
import grpc
import os
import codecs

os.environ["GRPC_SSL_CIPHER_SUITES"] = 'HIGH+ECDSA'

def metadata_callback(context, callback):
    callback([('macaroon', macaroon)], None)

cert = open(os.path.expanduser('~/.lnd/tls.cert'), 'rb').read()
with open(os.path.expanduser('~/.lnd/data/chain/bitcoin/testnet/admin.macaroon'), 'rb') as f:
    macaroon_bytes = f.read()
    macaroon = codecs.encode(macaroon_bytes, 'hex')

cert_creds = grpc.ssl_channel_credentials(cert)
auth_creds = grpc.metadata_call_credentials(metadata_callback)
combined_creds = grpc.composite_channel_credentials(cert_creds, auth_creds)
channel = grpc.secure_channel('localhost:10009', combined_creds)
stub = lnrpc.LightningStub(channel)


from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from pathlib import Path
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.wsgi import WSGIContainer

app = Flask(__name__)
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["2000 per day", "20 per minute"]
)

import asyncio
import uuid

@limiter.limit("20 per minute")
@app.route('/invoice/<int:amount>/<description>')
def getinvoice(amount, description):
    global plugin
    label = "ln-getinvoice-{}".format(uuid.uuid4())
    #invoice = plugin.rpc.invoice(int(amount)*1000, label, description)
    #gRPC
    response = stub.AddInvoice(ln.Invoice(value=amount,memo=description,))
    invoice = str(response.payment_request)
    return invoice


if __name__ == '__main__':
    port = os.getenv("REQUEST_INVOICE_PORT", default = 8809)
    asyncio.set_event_loop(asyncio.new_event_loop())

    print('Starting server on port {port}'.format(
        port=port
    ))
    app.config['SECRET_KEY'] = os.getenv(
        "REQUEST_INVOICE_SECRET",
        default=uuid.uuid4())

    http_server = HTTPServer(WSGIContainer(app))
    http_server.listen(port)
    IOLoop.instance().start()
