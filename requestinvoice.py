from lnd_grpc import lightning_pb2 as ln
from lnd_grpc import lightning_pb2_grpc as lnrpc
import grpc
import os
import codecs
from os.path import join, dirname
from dotenv import load_dotenv
from google.protobuf.json_format import MessageToDict

load_dotenv(verbose=True)

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

os.environ["GRPC_SSL_CIPHER_SUITES"] = 'HIGH+ECDSA'

def metadata_callback(context, callback):
    callback([('macaroon', macaroon)], None)

endpoint = os.getenv("LND_GRPC_ENDPOINT")
port = int(os.getenv("LND_GRPC_PORT"))
cert = open(os.getenv("LND_GRPC_CERT"), 'rb').read()
with open(os.getenv("LND_GRPC_MACAROON"), 'rb') as f:
    macaroon_bytes = f.read()
    macaroon = codecs.encode(macaroon_bytes, 'hex')

cert_creds = grpc.ssl_channel_credentials(cert)
auth_creds = grpc.metadata_call_credentials(metadata_callback)
combined_creds = grpc.composite_channel_credentials(cert_creds, auth_creds)
channel = grpc.secure_channel(f"{endpoint}:{port}", combined_creds)
stub = lnrpc.LightningStub(channel)


import flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import uuid

app = flask.Flask(__name__)
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["2000 per day", "20 per minute"]
)


@limiter.limit("20 per minute")
@app.route('/invoice/<int:amount>/<description>')
def getinvoice(amount, description):
    # Call LND gRPC
    response = stub.AddInvoice(ln.Invoice(value=amount,memo=description,))
    invoice = {
        "bolt11": response.payment_request,
        "payment_hash": response.r_hash.hex(),
        }
    return invoice

@app.route('/listchannels')
def listchannels():
    # Call LND gRPC
    response = stub.ListChannels(ln.ListChannelsRequest())
    channels = MessageToDict(response)
    return channels

def event_stream():
    # TODO: handle client disconnection.
    print('event_stream...')
    for invoice in stub.SubscribeInvoices(ln.InvoiceSubscription()):
        if(invoice.state == 1):
            print(invoice.r_hash.hex())
            yield 'data:"Invoice paid"\n\n'

@app.route('/stream')
def stream():
    print('streaming...')
    return flask.Response(event_stream(),
                          mimetype="text/event-stream")

@app.route('/')
def home():
    return """
        <!doctype html>
        <head>
        <meta name='viewport' content='width=device-width,initial-scale=1'>
        <title>hi, bitcoiner</title>
        <script src='https://ajax.googleapis.com/ajax/libs/jquery/1.7.1/jquery.min.js'></script>
	    <script src='https://cdn.jsdelivr.net/npm/kjua@0.6.0/dist/kjua.min.js'></script>
        <style>
        body { max-width: 500px; margin: auto; padding: 1em; background: #777799; color: #fff; font: 16px/1.6 menlo, monospace; }
        pre { white-space: pre-wrap; word-wrap: break-word; }
        </style>
        </head>
        <p><b>hi, bitcoiner</b></p>
        <p>Amount: <input type='number' id='in' /> sats</p>
        <pre id='out'></pre>
        <a id='link-invoice' href=''><div id='invoice'></div></a>
        <script>
            function sse() {
                var source = new EventSource('/stream');
                var out = document.getElementById('out');
                source.onmessage = function(e) {
                    // XSS in chat is fun (let's prevent that)
                    out.textContent =  e.data + '\\n' + out.textContent;
                };
            }
            $('#in').keyup(function(e){
                if (e.keyCode == 13) {
                    $.get('/invoice/' + $(this).val() + '/request')
                    .done(function( data ) {
                        out.textContent = data.bolt11;
                        $('#invoice').empty();
                        $('#invoice').append(kjua({text: data.bolt11}));
                        $('#link-invoice').attr('href', 'lightning:' + data.bolt11)
                    });
                    $(this).val('');
                }
            });
            sse();
        </script>
    """

if __name__ == '__main__':
    print('Starting server on port {port}'.format(
        port=port
    ))
    app.config['SECRET_KEY'] = os.getenv(
        "REQUEST_INVOICE_SECRET",
        default=uuid.uuid4())
    app.debug = True
    app.run(host='0.0.0.0', port=8809)