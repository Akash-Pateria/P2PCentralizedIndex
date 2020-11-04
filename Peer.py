import threading
import os
import socket
import time

HOSTNAME = "sample.ncsu.edu"
LOCALHOST = "127.0.0.1"
SERVER_ADDR = (LOCALHOST, 7734)
DEFAULT_RFC_DIR = "."
END_DELIMITER = "\&!"
VERSION = "1.0"
upload_port = None


def peer_to_server_target():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as skt:
        try:
            skt.connect(SERVER_ADDR)
        except socket.error as message:
            print("Error occurred while connecting server: " + str(message))

        try:
            exit_ = False
            while not exit_:
                show_menu()
                choice = input("Input choice: ")
                if choice == "5":
                    leave(skt)
                    exit_ = True
                elif choice == "4":
                    list_all(skt)
                elif choice == "3":
                    lookup_rfc(skt)
                elif choice == "2":
                    add_rfc(skt)
                elif choice == "1":
                    pass
                else:
                    print("ERROR: Select a valid option(1-5)")
        except socket.error as message:
            print("Error occurred: " + str(message))
            skt.close()
        except KeyboardInterrupt:
            skt.close()


def show_menu():
    print("\n\nP2P-Centralized-Index: Choose 1 of 5 choices")
    print("1. GET RFC")
    print("2. ADD RFC")
    print("3. LOOKUP RFC")
    print("4. LIST RFCs")
    print("5. EXIT")


def validate_rfc(rfc_number):
    from os.path import isfile, join
    all_files = [f for f in os.listdir(
        DEFAULT_RFC_DIR) if isfile(join(DEFAULT_RFC_DIR, f))]
    return "RFC" + rfc_number + ".txt" in all_files


def validate_upload_port(upload_port):
    return not(upload_port is None or upload_port < 1
               or (upload_port > 1 and upload_port < 1023))


def send_recv(socket_, request):
    status, error = send_request(socket_, request)
    if error is not None:
        print("Error occurred while sending request: " + error)
        return
    return receive_response(socket_)


def add_rfc(socket_):
    rfc_number = input("\n\nEnter RFC number: ")
    while not validate_rfc(rfc_number):
        print("ERROR: Entered RFC could not found in the DEFAULT_RFC_DIR[" +
              DEFAULT_RFC_DIR + "]")
        rfc_number = input("Try again with a valid RFC number: ")
    rfc_title = input("Enter RFC title: ")
    request = "ADD RFC " + rfc_number + " P2P-CI/" + VERSION + "\n"
    request += "Host: " + HOSTNAME + "\n"
    request += "Port: " + str(upload_port) + "\n"
    request += "Title: " + rfc_title
    print("\n\n***Request***\n" + request + "\n\n")
    request += END_DELIMITER
    response = send_recv(socket_, request)
    print("\n\n***Response***\n" + response + "\n\n")


def lookup_rfc(socket_):
    rfc_number = input("\n\nEnter RFC number for lookup: ")
    rfc_title = input("Enter the corresponding RFC title: ")
    if not rfc_title:
        rfc_title = "NA"
    request = "LOOKUP RFC " + rfc_number + " P2P-CI/" + VERSION + "\n"
    request += "Host: " + HOSTNAME + "\n"
    request += "Port: " + str(upload_port) + "\n"
    request += "Title: " + rfc_title
    print("\n\n***Request***\n" + request + "\n\n")
    request += END_DELIMITER
    response = send_recv(socket_, request)
    print("\n\n***Response***\n" + response + "\n\n")


def list_all(socket_):
    request = "LIST ALL P2P-CI/" + VERSION + "\n"
    request += "Host: " + HOSTNAME + "\n"
    request += "Port: " + str(upload_port) + "\n"
    print("\n\n***Request***\n" + request + "\n\n")
    request += END_DELIMITER
    response = send_recv(socket_, request)
    print("\n\n***Response***\n" + response + "\n\n")


def leave(socket_):
    request = "LEAVE P2P-CI/" + VERSION + "\n"
    request += "Host: " + HOSTNAME + "\n"
    request += "Port: " + str(upload_port) + "\n"
    print("\n\n***Request***\n" + request + "\n\n")
    request += END_DELIMITER
    response = send_recv(socket_, request)
    print("\n\n***Response***\n" + response + "\n\n")


def receive_response(socket_):
    raw_response = socket_.recv(1024).decode("utf-8")
    if raw_response is None or not raw_response.strip():
        return ""
    end_index = raw_response.find(END_DELIMITER)
    end_index = len(raw_response) if end_index == -1 else end_index
    response = raw_response[: end_index]
    return response


def send_request(socket_, request):
    if request is None or not request.strip():
        return (False, "Empty request string")
    try:
        socket_.send(request.encode())
    except socket.error as message:
        return (False, str(message))
    return (True, None)


if __name__ == "__main__":
    upload_port = int(input("Enter upload port number: "))
    while not validate_upload_port(upload_port):
        upload_port = int(input("Enter a valid upload port number: "))

    peer_to_server_thread = threading.Thread(target=peer_to_server_target)
    peer_to_server_thread.daemon = True
    peer_to_server_thread.start()

    # upload_server_thread = threading.Thread(target=upload_server_target)
    # upload_server_thread.daemon = True
    # upload_server_thread.start()
