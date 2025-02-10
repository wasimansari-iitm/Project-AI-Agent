import unittest
import sys
import os

# Import functions from app.py
sys.path.append('../app')
from app import secure_read, secure_write, secure_delete

class TestDataAccess(unittest.TestCase):

    def setUp(self):
        # Create a sample file in /data for testing
        self.data_file = '../data/test_data.txt'
        secure_write(self.data_file, 'Test content')

    def test_read_inside_data(self):
        # ✅ Test reading a file inside /data
        content = secure_read(self.data_file)
        self.assertEqual(content, 'Test content')

    def test_read_outside_data(self):
        # ❌ Test reading a file outside /data (should raise error)
        with self.assertRaises(PermissionError):
            secure_read('../app/secret.txt')

    def test_delete_prevention(self):
        # ❌ Test preventing deletion inside /data (should raise error)
        with self.assertRaises(PermissionError):
            secure_delete(self.data_file)

    def tearDown(self):
        # Clean up: Remove test file if it exists
        if os.path.exists(self.data_file):
            os.remove(self.data_file)

if __name__ == '__main__':
    unittest.main()