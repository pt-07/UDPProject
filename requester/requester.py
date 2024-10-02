import socket
import struct
import os
import argparse
import time

parser = argparse.ArgumentParser(description='UDP Requester')
parser.add_argument('-p', '--port', type=int, required=True, help='Port to bind to')
parser.add_argument('-o', '--file_option', type=str, required=True, help='Name of the file to request')

args = parser.parse_args()

# Initialize socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('0.0.0.0', args.port))  # Bind to all interfaces on specified port

# Read tracker file
tracker_path = os.path.join(os.getcwd(), 'tracker.txt')
with open(tracker_path, 'r') as tracker_file:
    tracker_lines = tracker_file.readlines()

# Parse tracker file for the requested file
file_parts = [line.strip().split() for line in tracker_lines if line.startswith(args.file_option)]
file_parts.sort(key=lambda x: int(x[1]))  # Sort by ID

received_data = bytearray()

for part in file_parts:
    filename, id, sender_host, sender_port, size = part
    sender_port = int(sender_port)

    # Debug information
    print(f"Sending request to {sender_host}:{sender_port}")

    # Send request packet
    request_packet = struct.pack('!cII', b'R', 0, 0) + args.file_option.encode()
    sock.sendto(request_packet, ('', sender_port))

    while True:
        data, addr = sock.recvfrom(1024)
        packet_type, sequence_number, length = struct.unpack('!cII', data[:9])
        payload = data[9:]

        if packet_type == b'D':
            received_data.extend(payload)
            print(f"Received DATA packet: {sequence_number}, {len(payload)} bytes from {addr}")
        elif packet_type == b'E':
            print(f"Received END packet from {addr}")
            break

# Write received data to file
output_file_path = os.path.join(os.getcwd(), args.file_option)
with open(output_file_path, 'wb') as output_file:
    output_file.write(received_data)

# Print tracker information
for part in file_parts:
    print(" ".join(part))

# Close the socket
sock.close()