# encoding: utf-8


from lib import threads, renki_settings as settings
from lib.exceptions import RenkiSocketTimeout, RenkiSocketClosed, \
    RenkiSocketError
import socket
import logging
import time
import ssl
from datetime import datetime
import json


logger = logging.getLogger("RenkiSocket")


class MsgTypes(object):
    OK = 1
    ERROR = 2
    HELLO = 3
    ACL = 4
    TICKET = 6
    NOP = 99 # For timeout testing

    @property
    def values(self):
        out = []
        for i in self.__class__.__dict__:
            if i.startswith('_') and type(i) in [int, str]:
                continue
            val = self.__class__.__dict__[i]
            out.append(val)
        return out

MsgTypes = MsgTypes()

class MessageStates(object):
    NotSent = 1
    WaitingOK = 2
    Sent = 3

MessageStates = MessageStates()

class Message(object):
    def __init__(self, msg):
        self.msg = msg
        self._state = MessageStates.NotSent
        self._changed = None

    def is_sent(self):
        return self._state == MessageStates.Sent

    def mark_sent(self):
        self._state = MessageStates.WaitingOK
        self._changed = datetime.now()

    def mark_ok(self):
        self._state = MessageStates.Sent
        self._changed = datetime.now()


class RenkiSocketConnection(threads.RenkiThread):
    def __init__(self, sock, address, sslcontext=None):
        threads.RenkiThread.__init__(self)
        self.sock = sock
        self.send_queue = []
        
        self.sslcontext = sslcontext
        #self.beat_interval = 5
        self.address = address
        self.sock.setblocking(False)
        self.sock.settimeout(1)
        # Tune keepalive
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 3)
        # TCP_KEEPX options works only in Linux :/
        #self.sock.setsockopt(socket.SOL_TCP, socket.TCP_KEEPIDLE, 1)
        #self.sock.setsockopt(socket.SOL_TCP, socket.TCP_KEEPINTVL, 1)
        #self.sock.setsockopt(socket.SOL_TCP, socket.TCP_KEEPCNT, 5)

    def recv(self):
        msg = []
        closed = False
        error = False
        if not self.sock:
            return
        while not self.is_stopped() and len(msg) < 1048576:
            try:
                m = self.sock.recv(10240)
                logger.info("M: %s" % str(m))
                if m:
                    msg.append(m.decode("utf-8"))
                elif len(msg) == 0:
                    # Socket is closed if message is 0 bytes long
                    logger.debug("Got msg with length 0")
                    closed = True
                    break
                else:
                    # Previous message was just 10240 bytes.
                    break
            except socket.timeout:
                break
            except socket.gaierror as e:
                logger.error("%s: Got error from socket" % (str(self)))
                logger.exception(e)
                self.stop()
                break
            except BlockingIOError:
                break
            except Exception as e:
                logger.exception(e)
                error = True
                break
        if closed:
            raise RenkiSocketClosed("Socket closed")
        if error:
            raise RenkiSocketError("Got error, cannot continue")
        if msg:
            return ''.join(msg) 
        return None


    def post_stop(self):
        self.close()

    def close(self):
        """
        Close socket if not closed
        """
        if not self.sock:
            return
        try:
            logger.debug("%s: Closing socket" % str(self))
            s = self.sock
            self._sock = None
            self.sock = None
            s.setblocking(False)
            s.shutdown(socket.SHUT_RDWR)
        except Exception as e:
            logger.exception(e)
        try:
            s.close()
        except Exception as e:
            logger.exception(e)

    def _send(self, msg):
        if type(msg) == dict:
            msg = json.dumps(msg)
        if type(msg) == str:
            msg = msg.encode("utf-8")
        self.sock.send(msg)
        # TODO: wait for OK

    def send(self, msg):
        msg = (Message(msg)
        self.send_queue.append(msg)
        return msg

    def respond_ok(self, msg_id, *args, **kwargs):
        c = {'type': MsgTypes.OK, 'id': msg_id}
        for arg in args:
            if type(arg) == dict:
                c.update(dict(arg))
            else:
                raise ValueError("%s is invalid argument for respond_ok")
        c.update(dict(**kwargs))
        self._send(c)
        return

    def respond_error(self, msg_id=None, reason=None):
        msg = {'type': 'ERROR'}
        if msg_id:
            msg['id'] = msg_id
        if reason:
            msg['reason'] = reason
        self._send(msg)

    def handle_msg(self, msg):
        msg = msg.strip()
        if not msg:
            return
        logger.info("%s: Got message %s" % (str(self), msg))
        try:
            msg = json.loads(msg)
        except Exception as e:
            logger.exception(e)
            logger.error("Cannot parse message, not valid json")
            self.respond_error(reason="Invalid JSON")
            return

        if 'id' not in msg:
            logger.error("Message does not contain id")
            self.respond_error()
            return
        msg_id = msg['id']
        if type(msg_id) != int:
            try:
                msg_id = int(msg_id)
            except Exception as e:
                logger.error("Message id type (%s) is wrong" % type(msg_id))
                self.respond_error(reason="Invalid ID")
                return

        if 'type' not in msg:
            logger.error("Message does not contain type")
            self.respond_error(msg_id=msg_id, reason="type missing")
            return

        msg_type = msg['type']

        if msg_type not in MsgTypes.values:
            logger.error("Message type %s is unknown" % msg_type)
            self.respond_error(msg_id=msg_id, reason="Unknown message type")
            return

        if msg_type == MsgTypes.NOP:
            # No operation
            return

        self.respond_ok(msg_id = msg_id, status="Dummy")

    def handle_sent(self):
        for msg

    def handle_recv(self):
        logger.debug("%s: Waiting for data" % str(self))
        try:
            msg = self.recv()
        except RenkiSocketClosed as e:
            logger.warning("Connection %s closed" % str(self))
            return False
        except RenkiSocketError as e:
            logger.exception(e)
            return False
        except Exception as e:
            logger.exception(e)
            return False
        if not msg:
            time.sleep(0.1)
        else:
            try:
                self.handle_msg(msg)
            except Exception as e:
                logger.exception(e)
                logger.error("%s: Cannot handle message %s" % (
                                                            str(self), msg))
                self.respond_error(reason="Internal server error")
                return False
        return True

    def run(self):
        try:
            if self.sslcontext:
                self.sock = self.sslcontext.wrap_socket(self.sock,
                                                        server_side=True)
            else:
                self.sock = self._sock
        except Exception as e:
            logger.exception(e)
            return
        while not self.is_stopped():
            if not self.handle_recv():
                break
            if not self.handle_sent():
                break
        self.close()

    def __str__(self):
        return "RenkiSocket %s:%s" % self.address


class RenkiSocket(threads.RenkiThread):
#class RenkiSocket(object):
    def __init__(self):
        threads.RenkiThread.__init__(self)
        self.sock = None
        self.threads = []

    def connect(self):
        if self.sock:
            return
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind((settings.RENKISRV_SOCKET_ADDRESS,
                        settings.RENKISRV_SOCKET_PORT))
            sock.listen(5)
        except Exception as e:
            logger.exception(e)
            try:
                sock.close()
            except Exception as e:
                pass
            raise
        self.sock = sock


    def post_stop(self):
        for t in self.threads:
            try:
                t.stop()
            except Exception as e:
                logger.exception(e)
        for t in self.threads:
            logger.info("Waiting for thread %s to stop" % str(t))
            try:
                t.join()
            except Exception as e:
                logger.exception(e)
        if self.sock:
            try:
                self.sock.shutdown(socket.SHUT_RD)
                self.sock.close()
            except Exception as e:
                logger.exception(e)

    def handle_threads(self):
        logger.info("Handling threads")
        for t in reversed(range(len(self.threads))):
            try:
                thread = self.threads[t]
                if not thread.is_alive():
                    logger.info("Removing stopped thread %s" % str(thread))
                    self.threads.pop(t)
                    del(t)
            except Exception as e:
                logger.exception(e)


    def run(self):
        while not self.sock:
            try:
                self.connect()
            except OSError as e:
                logger.error("Socket in use, waiting to free")
                time.sleep(2)
        try:
            if settings.RENKISRV_SOCKET_SSL:
                sslcontext = ssl.SSLContext(ssl.PROTOCOL_SSLv3)
                sslcontext.load_cert_chain(certfile=settings.RENKISRV_SOCKET_CERT,
                                           keyfile=settings.RENKISRV_SOCKET_KEY)
            else:
                sslcontext = None
            while True:
                self.handle_threads()
                (clientsocket, address) = self.sock.accept()
                logger.info("Connection from %s" % str(address))
                t = RenkiSocketConnection(clientsocket, address,
                                          sslcontext=sslcontext)
                t.start()
                self.threads.append(t)
        except KeyboardInterrupt as e:
            pass
        except Exception as e:
            logger.exception(e)
        self.post_stop()
