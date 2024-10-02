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
start_times = {}
end_times = {}
packet_counts = {}
byte_counts = {}

for part in file_parts:
    filename, id, sender_host, sender_port, size = part
    sender_port = int(sender_port)
    size = int(size[:-1])  # Remove 'B' and convert to int

    # Debug information
    print(f"Sending request to {sender_host}:{sender_port}")

    # Send request packet
    request_packet = struct.pack('!cII', b'R', 0, 0) + args.file_option.encode()
    sock.sendto(request_packet, ('', sender_port))

    while True:
        data, addr = sock.recvfrom(1024)
        packet_type, sequence_number_net, length = struct.unpack('!cII', data[:9])
        sequence_number = socket.ntohl(sequence_number_net)
        payload = data[9:]

        recv_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        
        if packet_type == b'D':
            received_data.extend(payload)
            percentage = (len(received_data) / size) * 100
            print(f"DATA Packet\nrecv time: {recv_time}\nsender addr: {addr[0]}:{addr[1]}\nsequence: {sequence_number}\nlength: {length}\npercentage: {percentage:.2f}%\npayload: {payload[:4].decode(errors='ignore')}\n")
            
            if addr not in start_times:
                start_times[addr] = time.time()
                packet_counts[addr] = 0
                byte_counts[addr] = 0
            
            packet_counts[addr] += 1
            byte_counts[addr] += length
            
        elif packet_type == b'E':
            print(f"END Packet\nrecv time: {recv_time}\nsender addr: {addr[0]}:{addr[1]}\nsequence: {sequence_number}\nlength: 0\npayload: \n")
            end_times[addr] = time.time()
            break

# Write received data to file
output_file_path = os.path.join(os.getcwd(), args.file_option)
with open(output_file_path, 'wb') as output_file:
    output_file.write(received_data)

# Print tracker information
for part in file_parts:
    print(" ".join(part))

# Print summary information
for addr in start_times:
    duration = (end_times[addr] - start_times[addr]) * 1000  # in milliseconds
    avg_packets_per_sec = packet_counts[addr] / ((end_times[addr] - start_times[addr]) or 1)
    print(f"\nSummary\nsender addr: {addr[0]}:{addr[1]}\nTotal Data packets: {packet_counts[addr]}\nTotal Data bytes: {byte_counts[addr]}\nAverage packets/second: {avg_packets_per_sec:.2f}\nDuration of the test: {duration:.0f} ms\n")

# Close the socket
sock.close()