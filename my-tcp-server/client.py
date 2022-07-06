    
import socket
import config as g
HOST = '192.168.1.225'  
PORT = 50050     
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('0.0.0.0',2305))

server_address = (HOST, PORT)
print('connecting to %s port ' + str(server_address))
s.connect(server_address)
try:
    while True:
        msg = input('Client: ')
        s.sendall(msg.encode('utf-8'))
      
        # s.sendall(b'OM1+2561')
finally:
    s.close()
