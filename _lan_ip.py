"""Print this PC's WiFi/LAN IPv4 address (used by START_APP.bat)."""
import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
try:
    sock.connect(("8.8.8.8", 80))  # UDP trick - no packet actually sent
    print(sock.getsockname()[0])
except OSError:
    print("127.0.0.1")
finally:
    sock.close()