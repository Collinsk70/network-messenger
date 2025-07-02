# utils.py
import pickle
import os

def load_data(file):
    if os.path.exists(file):
        with open(file, 'rb') as f:
            return pickle.load(f)
    return {}

def save_data(file, data):
    with open(file, 'wb') as f:
        pickle.dump(data, f)
