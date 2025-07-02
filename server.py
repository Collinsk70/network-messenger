# server.py
import socket, threading, os, logging
from config import *
from utils import load_data, save_data

logging.basicConfig(level=logging.INFO)
users = load_data("users.pkl")
contacts = load_data("contacts.pkl")

clients = {}  # {username: conn}
lock = threading.Lock()

def handle_client(conn, addr):
    username = None
    try:
        auth_data = conn.recv(BUFFER_SIZE).decode(ENCODING)
        action, username, password = auth_data.split(SEPARATOR)

        with lock:
            if action == "REGISTER":
                if username in users:
                    conn.send("ERROR: Username already exists.".encode(ENCODING))
                    conn.close()
                    return
                users[username] = password
                contacts[username] = []
                save_data("users.pkl", users)
                save_data("contacts.pkl", contacts)
                conn.send("Registered successfully.".encode(ENCODING))

            elif action == "LOGIN":
                if username not in users or users[username] != password:
                    conn.send("ERROR: Invalid credentials.".encode(ENCODING))
                    conn.close()
                    return
                conn.send("Login successful.".encode(ENCODING))

            else:
                conn.send("ERROR: Invalid action.".encode(ENCODING))
                conn.close()
                return

        clients[username] = conn
        logging.info(f"{username} connected from {addr}")

        while True:
            msg = conn.recv(BUFFER_SIZE).decode(ENCODING)
            if not msg or msg.strip().lower() == "exit":
                break

            if msg.startswith("SENDTO"):
                _, to_user, content = msg.split(SEPARATOR, 2)
                if to_user in clients:
                    clients[to_user].send(f"{username}: {content}".encode(ENCODING))
                else:
                    conn.send(f"{to_user} is offline.".encode(ENCODING))

            elif msg.startswith("FILE"):
                _, to_user, filename, filesize = msg.split(SEPARATOR)
                filesize = int(filesize)
                received_data = b""
                remaining = filesize
                while remaining > 0:
                    chunk = conn.recv(min(BUFFER_SIZE, remaining))
                    if not chunk:
                        break
                    received_data += chunk
                    remaining -= len(chunk)

                if to_user in clients:
                    clients[to_user].send(f"FILE{SEPARATOR}{filename}{SEPARATOR}{filesize}".encode(ENCODING))
                    clients[to_user].sendall(received_data)
                else:
                    conn.send(f"{to_user} is offline. File not delivered.".encode(ENCODING))

            elif msg.startswith("ADD_CONTACT"):
                _, new_contact = msg.split(SEPARATOR)
                with lock:
                    if new_contact in users:
                        if new_contact not in contacts[username]:
                            contacts[username].append(new_contact)
                            save_data("contacts.pkl", contacts)
                            conn.send(f"Added {new_contact} to your contacts.".encode(ENCODING))
                        else:
                            conn.send(f"{new_contact} is already in your contacts.".encode(ENCODING))
                    else:
                        conn.send(f"User {new_contact} does not exist.".encode(ENCODING))

            elif msg.startswith("REMOVE_CONTACT"):
                _, contact = msg.split(SEPARATOR)
                with lock:
                    if contact in contacts[username]:
                        contacts[username].remove(contact)
                        save_data("contacts.pkl", contacts)
                        conn.send(f"Removed {contact} from your contacts.".encode(ENCODING))
                    else:
                        conn.send(f"{contact} is not in your contacts.".encode(ENCODING))

            elif msg.startswith("LIST_CONTACTS"):
                with lock:
                    user_contacts = contacts.get(username, [])
                    if user_contacts:
                        conn.send(f"Your contacts: {', '.join(user_contacts)}".encode(ENCODING))
                    else:
                        conn.send("You have no contacts.".encode(ENCODING))

    except Exception as e:
        logging.error(f"Error with {username or addr}: {e}")
    finally:
        with lock:
            if username in clients:
                del clients[username]
        conn.close()
        logging.info(f"{username} disconnected.")

def start_server():
    server_socket = socket.socket()
    server_socket.bind((SERVER_HOST, SERVER_PORT))
    server_socket.listen(5)
    logging.info(f"Server listening on {SERVER_HOST}:{SERVER_PORT}")

    try:
        while True:
            conn, addr = server_socket.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
    except KeyboardInterrupt:
        logging.info("Shutting down server...")
    finally:
        server_socket.close()
        with lock:
            for user_conn in clients.values():
                try:
                    user_conn.shutdown(socket.SHUT_RDWR)
                    user_conn.close()
                except:
                    pass
        logging.info("Server closed.")

if __name__ == "__main__":
    start_server()
