import sys
import os
import socket
import threading
from base import Peer, RFC, DataStoreSingleton, VERSION, SERVER_ADDR, END_DELIMITER, PHRASES
from base import receive_request, send_response

ADD = "ADD"
LOOKUP = "LOOKUP"
LIST = "LIST"
LEAVE = "LEAVE"
ALLOWED_OPERATIONS = (
    ADD, LOOKUP, LIST, LEAVE,
)

data_store = DataStoreSingleton.get_instance()


def spawn_worker(socket_, addr):
    with socket_:
        print("Connected to", addr)
        while True:
            request = receive_request(socket_)
            if not request:
                print("Terminating connection", addr)
                # TODO: serve_leave(socket_)
                break
            print("\n\n***Received Request***\n" + request + "\n\n")
            parse_request(socket_, request)
    socket_.close()


def parse_request(socket_, response):
    # FIXME: Check request format or raise 400 error
    split_ = response.split()
    operation = split_[0]
    if operation not in ALLOWED_OPERATIONS:
        return

    if operation == ADD:
        serve_add(socket_=socket_, rfc_number=split_[2], version_str=split_[3],
                  hostname=split_[5], upload_port=split_[7],
                  rfc_title=" ".join(split_[9:]))
    elif operation == LOOKUP:
        serve_lookup(socket_, rfc_number=split_[2], version_str=split_[3],
                     rfc_title=" ".join(split_[9:]))
    elif operation == LIST:
        serve_list(socket_, version_str=split_[2])
    else:  # LEAVE
        serve_leave(socket_, version_str=split_[
                    1], hostname=split_[3], upload_port=split_[5])


def validate_str(inp_str):
    return inp_str and inp_str.strip()


def validate_version(version_str):
    split_ = version_str.split("/")
    return len(split_) == 2 and split_[-1].strip() == VERSION


def serve_add(socket_, rfc_number=None, hostname=None, upload_port=None, rfc_title=None, version_str=None):
    if not (validate_str(rfc_number) and validate_str(hostname)
            and validate_str(upload_port) and validate_str(rfc_title)
            and validate_str(version_str)):
        send_response(socket_, "400")
    elif not validate_version(version_str):
        send_response(socket_, "505")
    else:
        peer = Peer(hostname, upload_port)
        data_store.check_and_add(peer)
        rfc = RFC(rfc_number, rfc_title, peer)
        data_store.check_and_add(rfc, is_peer=False)
        response_message = str(rfc)
        send_response(socket_, "200", response_message)


def serve_lookup(socket_, rfc_number, version_str, rfc_title="NA"):
    print(version_str)
    if not (validate_str(rfc_number) and validate_str(version_str)):
        send_response(socket_, "400")
    elif not validate_version(version_str):
        send_response(socket_, "505")
    else:
        response_message = ""
        for i, rfc in enumerate(data_store.rfc_list):
            if rfc.rfc_number == rfc_number and (rfc_title == "NA" or rfc.rfc_title == rfc_title):
                response_message += str(rfc) + "\n"
        if not response_message:
            send_response(socket_, "404", response_message)
        else:
            send_response(socket_, "200", response_message)


def serve_list(socket_, version_str):
    if not validate_str(version_str):
        send_response(socket_, "400")
    elif not validate_version(version_str):
        send_response(socket_, "505")
    else:
        response_message = ""
        for i, rfc in enumerate(data_store.rfc_list):
            response_message += str(rfc) + "\n"
        send_response(socket_, "200", response_message)


def serve_leave(socket_, version_str, hostname, upload_port):
    if not (validate_str(version_str) and validate_str(hostname)
            and validate_str(upload_port)):
        send_response(socket_, "400")
    elif not validate_version(version_str):
        send_response(socket_, "505")
    else:
        peer = Peer(hostname, upload_port)
        if peer in data_store.peer_list:
            data_store.peer_list = list(
                filter(lambda p: p != peer, data_store.peer_list))
        data_store.rfc_list = list(
            filter(lambda rfc: rfc.peer != peer, data_store.rfc_list))
        response_message = "Disconnected"
        send_response(socket_, "200", response_message)


if __name__ == "__main__":
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as skt:
        try:
            skt.bind(SERVER_ADDR)
        except socket.error as message:
            print("Error occurred while binding socket: " + str(message))

        try:
            print("Accepting connections on port " + str(SERVER_ADDR[1]))
            while True:
                skt.listen()
                conn, addr = skt.accept()

                client_thread = threading.Thread(
                    target=spawn_worker, args=(conn, addr))
                # client_thread.daemon = True
                client_thread.start()

        except socket.error as message:
            print("Error occurred during listening phase: " + str(message))
        except KeyboardInterrupt:
            skt.close()
