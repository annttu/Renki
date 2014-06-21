#!/usr/bin/env python
# encoding: utf-8

from lib.test_utils import *
from lib.communication.renkisocket import *
from lib import renki_settings as settings
import socket
import ssl
import json
import os
import time
import logging
import random


#logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
logger = logging.getLogger("RenkiSocket")
logger.setLevel(logging.DEBUG)


# Default settings

settings.RENKISRV_SOCKET_ADDRESS = '127.0.0.1'
settings.RENKISRV_SOCKET_PORT = random.randint(60000, 64000)
settings.RENKISRV_SOCKET_CERT = os.path.join(os.path.dirname(__file__), 
                                                   'ssl/server.crt')
settings.RENKISRV_SOCKET_KEY = os.path.join(os.path.dirname(__file__), 
                                                   'ssl/server.key')

class RenkiSocketClient(object):
    def __init__(self, host=None, port=None):
        if host:
            self.host = host
        else:
            self.host = settings.RENKISRV_SOCKET_ADDRESS
        if port:
            self.port = port
        else:
            self.port = settings.RENKISRV_SOCKET_PORT
        self.conn = None
        self._id = 1

    def connect(self):
        if self.conn:
            return
        # Wait for server
        for i in range(10):
            try:
                c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            except Exception:
                try:
                    c.close()
                except Exception:
                    pass
                time.sleep(0.1)
            else:
                break
        if not c:
            raise AssertionError("Cannot connect to server")
        sc = ssl.wrap_socket(c,
                             ca_certs=os.path.join(os.path.dirname(__file__), 
                                                   'ssl/ca.crt'),
                             cert_reqs=ssl.CERT_REQUIRED,
                             ssl_version=ssl.PROTOCOL_SSLv3)
        try:
            sc.connect((self.host, self.port))
        except Exception as e:
            raise AssertionError("Cannot connect to server")
        self.conn = sc

    def send(self, msg):
        self.connect()
        self.conn.sendall(msg.encode("utf-8"))

    def recv(self):
        self.conn.settimeout(5)
        try:
            msg = self.conn.recv(10240)
        except socket.timeout:
            self.conn.settimeout(0)
            raise
        self.conn.settimeout(0)
        try:
            msg = msg.decode("utf-8")
        except Exception as e:
            raise AssertionError("Server response is not utf-8 encoded")
        try:
            return json.loads(msg)
        except Exception as e:
            raise AssertionError("Server response is not valid json message")

    def make_msg(self, **kwargs):
        kwargs.update({'id': self._id})
        self._id += 1
        return json.dumps(kwargs)

    def close(self):
        try:
            self.conn.close()
        except Exception:
            pass

class TestRenkiSocketBasic(BasicTest):

    def setUp(self):
        #Closing socket and opening new with same port is too slow!
        settings.RENKISRV_SOCKET_PORT = random.randint(60000, 64000)
        self.socket = RenkiSocket()
        self.client = RenkiSocketClient()
        self.socket.start()

    def test_connect(self):
        self.client.connect()

    def test_hello(self):
        msg = {
            'id': 1,
            'type': MsgTypes.HELLO,
            'version': "0.0.1",
            'name': 'testclient',
            'password': 'testclient'
        }
        msg = json.dumps(msg)
        self.client.connect()
        self.client.send(msg)
        msg = self.client.recv()
        if not msg:
            self.fail("Didn't get response from server")
        if 'type' not in msg:
            self.fail("Server response didn't contain type")
        if msg['type'] != MsgTypes.OK:
            self.fail("Server response wasn't OK")

    def test_invalid_type(self):
        self.client.send(self.client.make_msg(type=999999, msg='asdf'))
        error = self.client.recv()
        if not error:
            self.fail("Invalid type doesn't return error message")
        if 'reason' not in error:
            self.fail("Reason missing from error")
        if error['reason'] != "Unknown message type":
            self.fail("Wrong reason given")

    def test_timeout(self):
        """
        Actually tests RenkiSocketClient
        """
        self.client.send(self.client.make_msg(type=MsgTypes.NOP))
        try:
            out = self.client.recv()
            self.fail("NOP shouldn't return without exception")
        except socket.timeout:
            pass

    def test_invalid_input(self):
        self.client.send("asdf")
        try:
            msg = self.client.recv()
        except Exception as e:
            self.fail("Invalid message shouldn't return exception")
        if msg['type'] != MsgTypes.ERROR:
            self.fail("Server response wasn't ERROR")

    def tearDown(self):
        self.client.close()
        self.socket.stop()


class TestRenkiSocketServer(BasicTest):
    def setUp(self):
        #Closing socket and opening new with same port is too slow!
        settings.RENKISRV_SOCKET_PORT = random.randint(60000, 64000)
        self.socket = RenkiSocket()
        self.client = RenkiSocketClient()
        self.socket.start()

    def test_send_message(self):
        time.sleep(5)
        self.client.connect()
        if len(self.socket.threads) < 1:
            self.fail("Number of threads (%s) is not correct, should be 1" %
                      (len(self.socket.threads),))
        s = self.socket.threads[0]
        s.send({'id': 1, 'type': MsgTypes.HELLO})
        try:
            msg = self.client.recv()
        except Exception as e:
            self.fail("receiving message shouldn't return exception")
        if msg['type'] != MsgTypes.HELLO:
            self.fail("Server response wasn't HELLO")

    def tearDown(self):
        self.client.close()
        self.socket.stop()

if __name__ == "__main__":
    import unittest
    unittest.main()