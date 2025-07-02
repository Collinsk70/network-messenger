# Python Network Messaging App

This is a client-server messaging application built in Python. It supports user registration, login, real-time text messaging, file transfer, and contact management.

## Requirements
- Python 3.7+
- Tkinter (included in standard Python)

## How to Run

1. **Start the Server**  
   In one terminal via:
   python server.py

2. **Start the Client(s)**  
In another terminal via:
python client.py

## Client Usage
- Choose `REGISTER` or `LOGIN`
- Commands:
- `msg` – send message
- `file` – send file (GUI picker)
- `add_contact` – add user to contacts
- `remove_contact` – remove a contact
- `list_contacts` – view contact list
- `exit` – disconnect

## Notes
- Ensure the server is running before launching clients.
- `users.pkl` and `contacts.pkl` are auto-created for persistence.
- Create two or more client then message each via selecting one at a time.