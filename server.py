# server.py
import socket, threading, os, logging
from config import *
from utils import load_data, save_data

# Configure logging for server events
logging.basicConfig(level=logging.INFO)

# Load user credentials and contact lists from persistent storage
users = load_data("users.pkl")
contacts = load_data("contacts.pkl")

# Dictionary to hold currently connected clients {username: socket connection}
clients = {}

# Lock for synchronizing access to shared resources
lock = threading.Lock()

# Function to handle communication with a connected client
def handle_client(conn, addr):
    username = None
    try:
        # First message from client must be authentication data
        auth_data = conn.recv(BUFFER_SIZE).decode(ENCODING)
        action, username, password = auth_data.split(SEPARATOR)

        # Register or authenticate user
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

        # Store the connection for active communication
        clients[username] = conn
        logging.info(f"{username} connected from {addr}")

        # Listen for client messages in a loop
        while True:
            msg = conn.recv(BUFFER_SIZE).decode(ENCODING)
            if not msg or msg.strip().lower() == "exit":
                break

            # Direct message to another user
            if msg.startswith("SENDTO"):
                _, to_user, content = msg.split(SEPARATOR, 2)
                if to_user in clients:
                    clients[to_user].send(f"{username}: {content}".encode(ENCODING))
                else:
                    conn.send(f"{to_user} is offline.".encode(ENCODING))

            # Receive file and forward to another user
            elif msg.startswith("FILE"):
                _, to_user, filename, filesize = msg.split(SEPARATOR)
                filesize = int(filesize)
                received_data = b""
                remaining = filesize

                # Receive file data in chunks
                while remaining > 0:
                    chunk = conn.recv(min(BUFFER_SIZE, remaining))
                    if not chunk:
                        break
                    received_data += chunk
                    remaining -= len(chunk)

                # Forward the file to the recipient if they are online
                if to_user in clients:
                    clients[to_user].send(f"FILE{SEPARATOR}{filename}{SEPARATOR}{filesize}".encode(ENCODING))
                    clients[to_user].sendall(received_data)
                else:
                    conn.send(f"{to_user} is offline. File not delivered.".encode(ENCODING))

            # Add a contact to the user's contact list
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

            # Remove a contact from the user's contact list
            elif msg.startswith("REMOVE_CONTACT"):
                _, contact = msg.split(SEPARATOR)
                with lock:
                    if contact in contacts[username]:
                        contacts[username].remove(contact)
                        save_data("contacts.pkl", contacts)
                        conn.send(f"Removed {contact} from your contacts.".encode(ENCODING))
                    else:
                        conn.send(f"{contact} is not in your contacts.".encode(ENCODING))

            # List all contacts for the user
            elif msg.startswith("LIST_CONTACTS"):
                with lock:
                    user_contacts = contacts.get(username, [])
                    if user_contacts:
                        conn.send(f"Your contacts: {', '.join(user_contacts)}".encode(ENCODING))
                    else:
                        conn.send("You have no contacts.".encode(ENCODING))

    # Handle unexpected exceptions gracefully
    except Exception as e:
        logging.error(f"Error with {username or addr}: {e}")
    
    # Clean up client connection on disconnect or error
    finally:
        with lock:
            if username in clients:
                del clients[username]
        conn.close()
        logging.info(f"{username} disconnected.")

# Function to start the server and accept incoming client connections
def start_server():
    server_socket = socket.socket()
    server_socket.bind((SERVER_HOST, SERVER_PORT))
    server_socket.listen(5)
    logging.info(f"Server listening on {SERVER_HOST}:{SERVER_PORT}")

    try:
        # Continuously accept new client connections
        while True:
            conn, addr = server_socket.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

    # Graceful shutdown on keyboard interrupt
    except KeyboardInterrupt:
        logging.info("Shutting down server...")

    # Close all connections and clean up on shutdown
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

# Entry point for server script
if __name__ == "__main__":
    start_server()
