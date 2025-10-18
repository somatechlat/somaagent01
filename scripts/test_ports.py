#!/usr/bin/env python3
import socket

def test_port(port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('0.0.0.0', port))
            s.listen(1)
            print(f"Port {port} is available")
            return True
    except Exception as e:
        print(f"Port {port} error: {str(e)}")
        return False

# Test a few ports in our range
for port in [68100, 68200, 68300, 68400, 68500]:
    test_port(port)