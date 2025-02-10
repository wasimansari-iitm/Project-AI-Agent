import os

DATA_DIR = os.path.abspath('../data')

def secure_read(file_path):
    # Get absolute path
    abs_path = os.path.abspath(file_path)
    
    # Check if the file is inside the /data folder
    if abs_path.startswith(DATA_DIR):
        with open(abs_path, 'r') as file:
            return file.read()
    else:
        raise PermissionError("Access Denied: You can only access files in the /data folder.")

# Test it
try:
    print(secure_read('../data/sample.txt'))  # Allowed
    print(secure_read('../app/secret.txt'))   # Should raise an error
except Exception as e:
    print(e)