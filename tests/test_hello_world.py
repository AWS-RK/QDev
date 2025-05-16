#!/usr/bin/env python3
"""
Unit tests for the Hello World application.
"""

import unittest
import sys
import os

# Add the parent directory to the path so we can import the hello_world module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from hello_world import get_hello_message

class TestHelloWorld(unittest.TestCase):
    """Test cases for the Hello World application."""
    
    def test_get_hello_message(self):
        """Test that the get_hello_message function returns the correct string."""
        self.assertEqual(get_hello_message(), "Hello, World!")
    
    def test_message_type(self):
        """Test that the message is a string."""
        self.assertIsInstance(get_hello_message(), str)

if __name__ == "__main__":
    unittest.main()