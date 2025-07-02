# client.py
import socket, threading, os
from tkinter import Tk, filedialog
from config import *

# Function to receive incoming messages or files from the server
def receive_messages(sock):
    while True:
        try:
            header = sock.recv(BUFFER_SIZE)
            if not header:
                break
            decoded = header.decode(ENCODING)
            
            # Handle incoming file transfer
            if decoded.startswith("FILE"):
                _, filename, filesize = decoded.split(SEPARATOR)
                filesize = int(filesize)
                received_data = b""
                
                # Read the file data in chunks until complete
                while len(received_data) < filesize:
                    chunk = sock.recv(min(BUFFER_SIZE, filesize - len(received_data)))
                    if not chunk:
                        break
                    received_data += chunk
                
                # Save the received file locally
                with open("received_" + filename, "wb") as f:
                    f.write(received_data)
                print(f">> File received: received_{filename}")
            
            # Print regular text messages
            else:
                print(">>", decoded)

        except:
            print("Disconnected from server.")
            break

# Function to handle user input and send commands/messages to the server
def send_messages(sock, username):
    while True:
        cmd = input("Type (msg/file/add_contact/remove_contact/list_contacts/exit): ").strip().lower()

        # Send a text message to another user
        if cmd == "msg":
            to = input("Send to: ")
            text = input("Message: ")
            sock.send(f"SENDTO{SEPARATOR}{to}{SEPARATOR}{text}".encode(ENCODING))

        # Send a file to another user
        elif cmd == "file":
            to = input("Send file to: ")

            # Open file picker window
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

            # Send file metadata followed by actual file data
            filesize = os.path.getsize(path)
            sock.send(f"FILE{SEPARATOR}{to}{SEPARATOR}{os.path.basename(path)}{SEPARATOR}{filesize}".encode(ENCODING))
            with open(path, "rb") as f:
                while True:
                    chunk = f.read(BUFFER_SIZE)
                    if not chunk:
                        break
                    sock.sendall(chunk)
            print(f"File '{path}' sent to {to}.")

        # Add a user to contact list
        elif cmd == "add_contact":
            contact = input("Enter contact username to add: ")
            sock.send(f"ADD_CONTACT{SEPARATOR}{contact}".encode(ENCODING))

        # Remove a user from contact list
        elif cmd == "remove_contact":
            contact = input("Enter contact username to remove: ")
            sock.send(f"REMOVE_CONTACT{SEPARATOR}{contact}".encode(ENCODING))

        # Request the list of saved contacts
        elif cmd == "list_contacts":
            sock.send("LIST_CONTACTS".encode(ENCODING))

        # Disconnect from the server and exit
        elif cmd == "exit":
            sock.send("exit".encode(ENCODING))
            print("Logging out and closing connection.")
            sock.close()
            break

        else:
            print("Invalid command.")

# Function to connect to the server and handle authentication
def start_client():
    s = socket.socket()
    try:
        s.connect((SERVER_HOST, SERVER_PORT))
    except:
        print("Could not connect to server.")
        return

    # Prompt user to either register or log in
    action = ""
    while action not in ("REGISTER", "LOGIN"):
        print("Choose: REGISTER or LOGIN")
        action = input("Enter action: ").strip().upper()
        if action not in ("REGISTER", "LOGIN"):
            print("Invalid input. Please type REGISTER or LOGIN.")

    # Prompt for user credentials
    username = input("Username: ")
    password = input("Password: ")

    # Send authentication data to server
    s.send(f"{action}{SEPARATOR}{username}{SEPARATOR}{password}".encode(ENCODING))
    response = s.recv(BUFFER_SIZE).decode(ENCODING)

    # Handle login/register result
    if response.startswith("ERROR"):
        print(response)
        s.close()
        return
    else:
        print(response)

    # Start receiving messages in a background thread
    threading.Thread(target=receive_messages, args=(s,), daemon=True).start()

    # Start interactive command loop
    send_messages(s, username)

# Entry point of the client application
if __name__ == "__main__":
    start_client()
