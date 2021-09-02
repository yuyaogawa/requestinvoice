# Http Invoice Request Server


It starts a minimal, rate limited HTTP Server and returns a invoice on the following GET request:

``/invoice/<amount>/<description>``

### Installing
```
git clone https://github.com/yuyaogawa/requestinvoice.git
cd requestinvoice
pip3 install -r requirements.txt
```

### Running
```
$ python3 requestinvoice.py
started server successfully on port 8089

$ curl http://localhost:8809/invoice/100000/some-text-here
{"bolt11":"lnbc100000n1p0yr9sxpp50t9rnvw5slcjn6m97fmujpp9xd6w0h26dpvajcv8xwhu42xk5vlqdq8vej8xcgxqyj...","expires_at":1581961350,"payment_hash":"7aca39b1d487f129eb65f277c904253374e7dd5a6859d9618733afcaa8d6a33e", ...}
```

The webserver is rate-limited, meaning that only a certain amount of request per minute is allowed (to prevent DoS attacks).

The json invoice can be used by other services, for example a service for tipping, donations, PoS devices, ...


### Onion routing
Exposing the url using Onion routing is easy. Install tor and 
add the service to `/etc/tor/torrc`
```
HiddenServiceDir /var/lib/tor/request-invoice-service_v2/
HiddenServicePort 80 127.0.0.1:8809

```
and restart tor to create the url
```
$ systemctl stop tor && systemctl start tor
$ cat /var/lib/tor/request-invoice-service_v2/hostname
2hlqgasrad74nx6eadtgtf7wsvqwoqizvejva4qdik7gihquxexndtyd.onion
```

Use tor browser to visit the url and create a invoice (and make a donation?).
http://2hlqgasrad74nx6eadtgtf7wsvqwoqizvejva4qdik7gihquxexndtyd.onion/invoice/1000/donation


### Docker

```
docker run -v $HOME:/root -p 8809:8809 --network=host -t yuya207503/requestinvoice
```

### Python gRPC
This tool uses a Python gRPC to communicate with lnd. Follow the instruction below.

https://github.com/lightningnetwork/lnd/blob/master/docs/grpc/python.md
