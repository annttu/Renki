# encoding: utf-8


from lib import threads, renki_settings as settings
from lib.exceptions import RenkiSocketTimeout, RenkiSocketClosed, \
    RenkiSocketError
import socket
import logging
import time
import ssl

logger = logging.getLogger("RenkiSocket")


class MsgTypes:
    HELLO = 1
    ACL = 2
    HEARTBEAT = 3
    TICKET = 4


class RenkiSocketConnection(threads.RenkiThread):
    def __init__(self, sock, address):
        threads.RenkiThread.__init__(self)
        self.sock = sock
        self.beat_interval = 5
        self.address = address
        self.sock.setblocking(False)
        self.sock.settimeout(1)
        # Tune keepalive
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        # TCP_KEEPX options works only in Linux :/
        #self.sock.setsockopt(socket.SOL_TCP, socket.TCP_KEEPIDLE, 1)
        #self.sock.setsockopt(socket.SOL_TCP, socket.TCP_KEEPINTVL, 1)
        #self.sock.setsockopt(socket.SOL_TCP, socket.TCP_KEEPCNT, 5)

    def recv(self):
        msg = []
        closed = False
        error = False
        while not self.is_stopped() and len(msg) < 1048576:
            try:
                m = self.sock.recv(10240)
                logger.info("M: %s" % str(m))
                if m:
                    msg.append(m.decode("utf-8"))
                elif len(msg) == 0:
                    # Socket is closed if message is 0 bytes long
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
            self.sock = None
            s.setblocking(False)
            s.shutdown(socket.SHUT_RDWR)
            s.close()
        except Exception as e:
            logger.exception(e)

    def send(self, msg):
        if type(msg) == dict:
            msg = json.dumps(msg)
        if type(msg) == str:
            msg = msg.encode("utf-8")
        self.sock.send(msg)

    def handle_msg(self, msg):
        logger.info("%s: Got message %s" % (str(self), msg))

    def run(self):
        while not self.is_stopped():
            #try:
            #    self.heartbeat()
            #except RenkiSocketTimeout:
            #    logger.info("%s: Connection timeouted" % (str(self),))
            #    break
            #except Exception as e:
            #    logger.exception(e)
            #    break
            logger.debug("%s: Waiting for data" % str(self))
            try:
                msg = self.recv()
            except RenkiSocketClosed as e:
                logger.warn("Connection %s closed" % str(self))
                break
            except RenkiSocketError as e:
                logger.exception(e)
                break
            except Exception as e:
                logger.exception(e)
                break
            if not msg:
                time.sleep(0.1)
            else:
                try:
                    self.last_beat_received = time.time()
                    self.handle_msg(msg)
                except Exception as e:
                    logger.exception(e)
                    logger.error("%s: Cannot handle message %s" % (str(self), msg))
                    break
            self.close()

    def __str__(self):
        return "RenkiSocket %s:%s" % self.address


#class RenkiSocket(threads.RenkiThread):
class RenkiSocket(object):
    def __init__(self):
        #threads.RenkiThread.__init__(self)
        self.sock = None
        self.threads = []

    def connect(self):
        if self.sock:
            return
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.bind((settings.RENKISRV_LISTEN_ADDRESS,
                        settings.RENKISRV_LISTEN_PORT))
            self.sock.listen(5)
        except Exception as e:
            self.sock = None
            raise


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
            while True:
                self.handle_threads()
                (clientsocket, address) = self.sock.accept()
                print("Connection from %s" % str(address))
                t = RenkiSocketConnection(clientsocket, address)
                t.start()
                self.threads.append(t)
        except KeyboardInterrupt as e:
            pass
        except Exception as e:
            logger.exception(e)
        self.post_stop()
