import aes
import os
import json
import time
from multiprocessing import Process
from hmac import compare_digest
import requests

from client import PINClientECDH

from wallycore import (
    sha256,
    ec_sig_from_bytes,
    hex_from_bytes,
    hex_to_bytes,
    AES_KEY_LEN_256,
    EC_FLAG_ECDSA,
    EC_FLAG_RECOVERABLE,
    )


b2h = hex_from_bytes
h2b = hex_to_bytes

# local tor proxy, this needs a working tor proxy on your computer
session = requests.session()
session.proxies = {}
session.proxies['http'] = 'socks5h://localhost:9050'
session.proxies['https'] = 'socks5h://localhost:9050'

# update url with your tor address and fetch server public key from your board
pinserver_url = 'http://5rydchlmsjctaiotqhgpe25xhjxpxrpnxdq4gpv3p7jxdps4vtasmwad.onion:8096/'
server_public_key = 'keys/server_public_key.pub'

# generate a pair of keys for your client
client_public_key = 'keys/client_public_key.pub'
client_private_key = 'keys/client_private_key.priv'


class PinServerClient():

    @staticmethod
    def new_pin_secret():
        return os.urandom(32)

    @staticmethod
    def new_entropy():
        return os.urandom(32)

    @classmethod
    def post(cls, url='', data=None):
        if data:
            userdata = json.dumps(data)
        else:
            userdata = None
        f = session.post(pinserver_url + '/' + url,
                          data=userdata)

        if f.status_code != 200:
            raise ValueError(f.status_code)

        return f.json() if url else f.text

    # Make new logical client static keys
    @classmethod
    def new_static_client_keys(cls):
        private_key, public_key = PINClientECDH.generate_ec_key_pair()

        pubfile = open(client_public_key, 'wb')
        pubfile.write(public_key)
        pubfile.close()

        privfile = open(client_private_key, 'wb')
        privfile.write(private_key)
        privfile.close()

        # Cache the pinfile for this client key so we can ensure it is removed
        pinfile = bytes(sha256(public_key))
        #cls.pinfiles.add(bytes(pinfile))

        # Return the keys and the pin-filename
        return private_key, public_key, pinfile

    @classmethod
    def file_static_client_keys(cls):
        pubfile = open(client_public_key, 'rb')
        public_key = pubfile.read()
        pubfile.close()

        privfile = open(client_private_key, 'rb')
        private_key = privfile.read()
        privfile.close()

        # Cache the pinfile for this client key so we can ensure it is removed
        pinfile = bytes(sha256(public_key))
        #cls.pinfiles.add(bytes(pinfile))

        # Return the keys and the pin-filename
        return private_key, public_key, pinfile

    # Helpers

    # Start the client/server key-exchange handshake
    def start_handshake(self, client):
        handshake = self.post('start_handshake')
        client.handshake(h2b(handshake['ske']), h2b(handshake['sig']))
        return client

    # Make a new ephemeral client and initialise with server handshake
    def new_client_handshake(self):
        file = open(server_public_key, 'rb')
        self.static_server_public_key = file.read()
        file. close()

        client = PINClientECDH(self.static_server_public_key)
        return self.start_handshake(client)

    # Make the server call to get/set the pin - returns the decrypted response
    def server_call(self, private_key, client, endpoint, pin_secret, entropy):
        # Make and encrypt the payload (ie. pin secret)
        ske, cke = client.get_key_exchange()
        sig = ec_sig_from_bytes(private_key,
                                sha256(cke + pin_secret + entropy),
                                EC_FLAG_ECDSA | EC_FLAG_RECOVERABLE)
        payload = pin_secret + entropy + sig

        encrypted, hmac = client.encrypt_request_payload(payload)

        # Make call and parse response
        urldata = {'ske': b2h(ske),
                   'cke': b2h(cke),
                   'encrypted_data': b2h(encrypted),
                   'hmac_encrypted_data': b2h(hmac)}
        response = self.post(endpoint, urldata)
        encrypted = h2b(response['encrypted_key'])
        hmac = h2b(response['hmac'])

        # Return decrypted payload
        return client.decrypt_response_payload(encrypted, hmac)

    def get_pin(self, private_key, pin_secret, entropy):
        # Create new ephemeral client, initiate handshake, and make call
        client = self.new_client_handshake()
        return self.server_call(
            private_key, client, 'get_pin', pin_secret, entropy)

    def set_pin(self, private_key, pin_secret, entropy):
        # Create new ephemeral client, initiate handshake, and make call
        client = self.new_client_handshake()
        return self.server_call(
            private_key, client, 'set_pin', pin_secret, entropy)

if __name__ == '__main__':
    test = PinServerClient()
    # Make ourselves a static key pair for this logical client
    priv_key, _, _ = test.file_static_client_keys()

    # The 'correct' client pin
    pin_secret = bytes(sha256(b'pippo'))

    # Make a new client and set the pin secret to get a new aes key
    aeskey_s = test.set_pin(priv_key, pin_secret, test.new_entropy())
    if not len(aeskey_s) == AES_KEY_LEN_256:
        print('dimension!')

    iv = priv_key[0:16]
    encrypted = aes.AES(aeskey_s).encrypt_ctr(b'Attack at dawn', iv)
    iv = priv_key[0:16]
    print(aes.AES(aeskey_s).decrypt_ctr(encrypted, iv))
    print('---')


    # Get key with a new client, with the correct pin secret (new entropy)
    for attempt in range(5):
        aeskey_g = test.get_pin(priv_key, pin_secret, test.new_entropy())
        if not compare_digest(aeskey_g, aeskey_s):
            print('compare_digest fails')
        iv = priv_key[0:16]
        print(aes.AES(aeskey_g).decrypt_ctr(encrypted, iv))

    # Get key with a new client, with the wrong pin secret (new entropy)
    pin_secret_wrong = bytes(sha256(b'pluto'))
    for attempt in range(5):
        aeskey_g = test.get_pin(priv_key, pin_secret_wrong, test.new_entropy())
        if not compare_digest(aeskey_g, aeskey_s):
            print('compare_digest fails')
            print(aeskey_g)
        iv = priv_key[0:16]
        print(aes.AES(aeskey_g).decrypt_ctr(encrypted, iv))

    aeskey_g = test.get_pin(priv_key, pin_secret, test.new_entropy())
    if not compare_digest(aeskey_g, aeskey_s):
        print('last - compare_digest fails')
    iv = priv_key[0:16]
    print(aes.AES(aeskey_g).decrypt_ctr(encrypted, iv))
