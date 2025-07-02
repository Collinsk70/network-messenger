# utils.py
import pickle
import os

# Load serialized data from a file using pickle
# Returns an empty dictionary if the file does not exist
def load_data(file):
    if os.path.exists(file):
        with open(file, 'rb') as f:
            return pickle.load(f)
    return {}

# Save data to a file by serializing it with pickle
def save_data(file, data):
    with open(file, 'wb') as f:
        pickle.dump(data, f)
