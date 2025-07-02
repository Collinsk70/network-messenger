# config.py

# IP address of the server (localhost for local testing)
SERVER_HOST = '127.0.0.1'

# Port number on which the server will listen for connections
SERVER_PORT = 5002

# Maximum size (in bytes) for receiving chunks of data
BUFFER_SIZE = 4096

# Custom separator used to split protocol messages between command and data
SEPARATOR = "<SEPARATOR>"

# Character encoding used for all text-based communication
ENCODING = "utf-8"
