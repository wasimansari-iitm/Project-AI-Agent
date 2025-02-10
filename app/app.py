import os

DATA_DIR = os.path.abspath('../data')

def secure_read(file_path):
    abs_path = os.path.abspath(file_path)
    if abs_path.startswith(DATA_DIR):
        with open(abs_path, 'r') as file:
            return file.read()
    else:
        raise PermissionError("Access Denied: You can only access files in the /data folder.")

def secure_write(file_path, content):
    abs_path = os.path.abspath(file_path)
    if abs_path.startswith(DATA_DIR):
        with open(abs_path, 'w') as file:
            file.write(content)
    else:
        raise PermissionError("Access Denied: You can only write files in the /data folder.")

def secure_delete(file_path):
    abs_path = os.path.abspath(file_path)
    if abs_path.startswith(DATA_DIR):
        raise PermissionError("Deletion Not Allowed: Data persistence is enforced.")
    else:
        raise PermissionError("Access Denied: You can only manage files in the /data folder.")

# Test Cases
try:
    print(secure_read('../data/sample.txt'))      # ✅ Allowed
    secure_write('../data/sample.txt', 'Updated content.')  # ✅ Allowed
    print(secure_read('../data/sample.txt'))      # ✅ See updated content
    secure_delete('../data/sample.txt')           # ❌ Should raise an error
except Exception as e:
    print(e)