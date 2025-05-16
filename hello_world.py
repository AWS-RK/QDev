#!/usr/bin/env python3
"""
A simple Hello World application.
"""

def get_hello_message():
    """
    Returns a Hello World message.
    
    Returns:
        str: The Hello World message
    """
    return "Hello, World!"

def main():
    """
    Main function that prints the Hello World message.
    """
    message = get_hello_message()
    print(message)

if __name__ == "__main__":
    main()