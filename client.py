# client.py
import socket, threading, os
from tkinter import Tk, filedialog
from config import *

def receive_messages(sock):
    while True:
        try:
            header = sock.recv(BUFFER_SIZE)
            if not header:
                break
            decoded = header.decode(ENCODING)
            if decoded.startswith("FILE"):
                _, filename, filesize = decoded.split(SEPARATOR)
                filesize = int(filesize)
                received_data = b""
                while len(received_data) < filesize:
                    chunk = sock.recv(min(BUFFER_SIZE, filesize - len(received_data)))
                    if not chunk:
                        break
                    received_data += chunk
                with open("received_" + filename, "wb") as f:
                    f.write(received_data)
                print(f">> File received: received_{filename}")
            else:
                print(">>", decoded)
        except:
            print("Disconnected from server.")
            break

def send_messages(sock, username):
    while True:
        cmd = input("Type (msg/file/add_contact/remove_contact/list_contacts/exit): ").strip().lower()
        if cmd == "msg":
            to = input("Send to: ")
            text = input("Message: ")
            sock.send(f"SENDTO{SEPARATOR}{to}{SEPARATOR}{text}".encode(ENCODING))

        elif cmd == "file":
            to = input("Send file to: ")

            # File picker popup with reliable Tk handling
            try:
                root = Tk()
                root.withdraw()
                root.attributes('-topmost', True)
                path = filedialog.askopenfilename(title="Select File to Send")
                root.destroy()
            except Exception as e:
                print(f"Failed to open file picker: {e}")
                continue

            if not path or not os.path.exists(path):
                print("Invalid or no file selected.")
                continue

            filesize = os.path.getsize(path)
            sock.send(f"FILE{SEPARATOR}{to}{SEPARATOR}{os.path.basename(path)}{SEPARATOR}{filesize}".encode(ENCODING))
            with open(path, "rb") as f:
                while True:
                    chunk = f.read(BUFFER_SIZE)
                    if not chunk:
                        break
                    sock.sendall(chunk)
            print(f"File '{path}' sent to {to}.")

        elif cmd == "add_contact":
            contact = input("Enter contact username to add: ")
            sock.send(f"ADD_CONTACT{SEPARATOR}{contact}".encode(ENCODING))

        elif cmd == "remove_contact":
            contact = input("Enter contact username to remove: ")
            sock.send(f"REMOVE_CONTACT{SEPARATOR}{contact}".encode(ENCODING))

        elif cmd == "list_contacts":
            sock.send("LIST_CONTACTS".encode(ENCODING))

        elif cmd == "exit":
            sock.send("exit".encode(ENCODING))
            print("Logging out and closing connection.")
            sock.close()
            break

        else:
            print("Invalid command.")

def start_client():
    s = socket.socket()
    try:
        s.connect((SERVER_HOST, SERVER_PORT))
    except:
        print("Could not connect to server.")
        return

    # Input validation for REGISTER or LOGIN
    action = ""
    while action not in ("REGISTER", "LOGIN"):
        print("Choose: REGISTER or LOGIN")
        action = input("Enter action: ").strip().upper()
        if action not in ("REGISTER", "LOGIN"):
            print("Invalid input. Please type REGISTER or LOGIN.")

    username = input("Username: ")
    password = input("Password: ")

    s.send(f"{action}{SEPARATOR}{username}{SEPARATOR}{password}".encode(ENCODING))
    response = s.recv(BUFFER_SIZE).decode(ENCODING)
    if response.startswith("ERROR"):
        print(response)
        s.close()
        return
    else:
        print(response)

    threading.Thread(target=receive_messages, args=(s,), daemon=True).start()
    send_messages(s, username)

if __name__ == "__main__":
    start_client()
