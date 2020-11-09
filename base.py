import socket

VERSION = "1.0"
LOCALHOST = "127.0.0.1"
SERVER_ADDR = (LOCALHOST, 7734)
END_DELIMITER = "\&!"

PHRASES = {"200": "OK", "400": "BAD REQUEST",
           "404": "NOT FOUND", "505": "P2P-CI VERSION NOT SUPPORTED"}


def receive_request(socket_):
    raw_request = socket_.recv(1024).decode("utf-8")
    if raw_request is None or not raw_request.strip():
        return ""
    end_index = raw_request.find(END_DELIMITER)
    end_index = len(raw_request) if end_index == -1 else end_index
    request = raw_request[:end_index]
    return request


def send_response(socket_, response_code, response_message=""):
    response = "P2P-CI/" + VERSION + " " + \
        response_code + " " + PHRASES[response_code] + "\n"
    response += response_message
    print("\n\n***Sending Response***\n" + response + "\n\n")
    response += END_DELIMITER
    try:
        socket_.send(response.encode())
    except socket.error as message:
        print("Error occurred while sending response: " + str(message))


class Peer(object):
    """
    A Peer is an active peer that is alive and connected to the server
     at the given point of time.
    """

    def __init__(self, hostname, upload_port):
        self.hostname = hostname
        self.upload_port = upload_port

    def __eq__(self, other):
        return self.to_dict() == other.to_dict()

    def to_dict(self):
        """
        Transforms the object to a Python dictionary.
        """
        peer = {
            "hostname": self.hostname,
            "upload_port": self.upload_port,
        }
        return peer


class RFC(object):
    """
    A RFC is a mapping between RFC document and the active peer that
    contains the corresponding RFC.
    """

    def __init__(self, rfc_number, rfc_title, peer):
        self.rfc_number = rfc_number
        self.rfc_title = rfc_title
        self.peer = peer

    def __eq__(self, other):
        return self.to_dict() == other.to_dict()

    def to_dict(self):
        """
        Transforms the object to a Python dictionary.
        """
        rfc_ = {
            "rfc_number": self.rfc_number,
            "rfc_title": self.rfc_title,
            "peer": self.peer.to_dict(),
        }
        return rfc_

    def __str__(self):
        return "RFC " + str(self.rfc_number) + " " + self.rfc_title \
            + " " + self.peer.hostname + " " + str(self.peer.upload_port)


class DataStoreSingleton(object):
    """
    A singleton class for storing active peer and RFC index list.
    """

    __shared_instance = None

    @staticmethod
    def get_instance():
        if DataStoreSingleton.__shared_instance is None:
            DataStoreSingleton()
        return DataStoreSingleton.__shared_instance

    def __init__(self):
        if DataStoreSingleton.__shared_instance is not None:
            raise Exception("Singleton class")
        DataStoreSingleton.__shared_instance = self
        self.peer_list = []
        self.rfc_list = []

    def check_and_add(self, instance, is_peer=True):
        if is_peer:
            if instance not in self.peer_list:
                self.peer_list.append(instance)
        else:
            if instance not in self.rfc_list:
                self.rfc_list.append(instance)
