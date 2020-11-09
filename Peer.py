from enum import Flag
import random
from sys import platform
import threading
import os
import platform
import sys
import socket
import time
from base import (VERSION, SERVER_ADDR,
                  LOCALHOST, END_DELIMITER,)
from base import receive_request, send_response

DEFAULT_RFC_DIR = "."
HOSTNAME = "sample_" + str(random.choice(list(range(10)))) + ".ncsu.edu"
OS_NAME = str(platform.system())
upload_port = None
exit_ = False


def peer_to_server_comm():
    global exit_
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as skt:
        try:
            skt.connect(SERVER_ADDR)
        except socket.error as message:
            print("Error occurred while connecting server: " + str(message))

        try:
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
                    get_rfc()
                else:
                    print("ERROR: Select a valid option(1-5)")
        except socket.error as message:
            print("Error occurred: " + str(message))
            skt.close()
        except KeyboardInterrupt:
            skt.close()
        sys.exit(0)


def upload_server_target():
    global exit_
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as skt:
        try:
            skt.bind((LOCALHOST, upload_port))
        except socket.error as message:
            print("Error occurred while binding socket: " + str(message))

        try:
            while not exit_:
                skt.listen()
                conn, _addr = skt.accept()
                client_thread = threading.Thread(
                    target=spawn_worker, args=(conn,))
                client_thread.start()
                client_thread.join()
                show_menu()
                print("Input choice: ")
        except socket.error as message:
            print("Error occurred during listening phase: " + str(message))
        except KeyboardInterrupt:
            skt.close()


def spawn_worker(socket_):
    with socket_:
        request = receive_request(socket_)
        print("\n\n***Received Request***\n" + request + "\n\n")
        serve_get_request(socket_, request)
    socket_.close()


def serve_get_request(socket_, request):
    rfc_number = request.split()[2]
    if not validate_rfc(rfc_number):
        send_response(socket_, "404")
    rfc_filename = "RFC" + rfc_number + ".txt"
    time_now = time.strftime(
        "%a, %d %b %Y %H:%M:%S", time.gmtime()) + "GMT"
    last_modified = time.strftime("%a, %d %b %Y %H:%M:%S ", time.gmtime(
        os.path.getmtime(rfc_filename))) + "GMT"
    response = "Date: " + str(time_now) + "\n"
    response += "OS: " + str(OS_NAME) + "\n"
    response += "Last-Modified: " + str(last_modified) + "\n"
    response += "Content-Length: " + str(os.path.getsize(rfc_filename)) + "\n"
    response += "Content-Type: text/text\n"
    send_response(socket_, "200", response_message=response)
    with open(rfc_filename, "r") as f:
        data = f.read(1024)
        socket_.send(data.encode())
        while data:
            data = f.read(1024)
            socket_.send(data.encode())


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


def get_rfc():
    server_upload_port = int(input("\n\nEnter download server port: "))
    rfc_number = int(input("Enter RFC number to request: "))
    request = "GET RFC " + str(rfc_number) + " P2P-CI/" + VERSION + "\n"
    request += "Host: " + HOSTNAME + "\n"
    request += "OS: " + OS_NAME + "\n"
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socket_:
        socket_.connect((LOCALHOST, server_upload_port))
        print("\n\n***Request***\n" + request + "\n\n")
        request += END_DELIMITER
        response = send_recv(socket_, request)
        print("\n\n***Response***\n" + response + "\n\n")
        if response.split()[1] == "200":
            with open("RFC" + str(rfc_number) + "_.txt", "w+") as f:
                data = socket_.recv(1024).decode("utf-8")
                while data:
                    f.write(data)
                    data = socket_.recv(1024).decode("utf-8")
    socket_.close()


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
    rfc_title = input("Enter the corresponding RFC title(optional): ")
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

    upload_server_thread = threading.Thread(target=upload_server_target)
    upload_server_thread.daemon = True
    upload_server_thread.start()

    peer_to_server_comm()
