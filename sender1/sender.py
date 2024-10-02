import socket
import argparse
import struct
import time
import os

parser = argparse.ArgumentParser(description='UDP Sender')
parser.add_argument('-p', '--port', type=int, required=True, help='Port to bind to')
parser.add_argument('-g', '--group', type=int, required=True, help='Group number')
parser.add_argument('-r', '--rate', type=int, required=True, help='Rate')
parser.add_argument('-q', '--queue', type=int, required=True, help='Queue size')
parser.add_argument('-l', '--length', type=int, required=True, help='Length')

args = parser.parse_args()

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('0.0.0.0', args.port))  # Bind to all interfaces on specified port

sequence_number = 0

# Read the file to be sent
file_path = os.path.join(os.getcwd(), 'split.txt')
with open(file_path, 'rb') as f:
    file_data = f.read()

while True:
    data, addr = sock.recvfrom(1024)  # Buffer size is 1024 bytes
    print(f"Received request from {addr}")

    # Send file data in chunks
    for i in range(0, len(file_data), args.length):
        payload = file_data[i:i + args.length]
        length = len(payload)
        packet_type = b'D'
        sequence_number_net = socket.htonl(sequence_number)

        # Create the packet
        packet = struct.pack('!cII', packet_type, sequence_number_net, length) + payload
        sock.sendto(packet, addr)
        
        # Log packet information
        send_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        print(f"DATA Packet\nsend time: {send_time}\nrequester addr: {addr}\nSequence num: {sequence_number}\nlength: {length}\npayload: {payload[:4].decode(errors='ignore')}\n")
        
        sequence_number += length
        time.sleep(1 / args.rate)  # Control the sending rate

    # Send END packet
    end_packet = struct.pack('!cII', b'E', socket.htonl(sequence_number), 0)
    sock.sendto(end_packet, addr)
    
    # Log END packet information
    send_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    print(f"END Packet\nsend time: {send_time}\nrequester addr: {addr}\nSequence num: {sequence_number}\nlength: 0\npayload: \n")
    
    break  # Exit after sending one response for simplicity