from http import client
import socket
from threading import Thread
from time import sleep
import config as g
import paho.mqtt.client as mqttclient
import json

def getIdDeviceOMNI(data):
    result = data.split(",")
    finalresult = result[g.indexIdOmni[0]] + '/'
    for i in g.indexIdOmni:
        finalresult += result[i]
    return finalresult

def addToDictionary(address, addr):
    address = address.split('/')
    temp = g.deviceThingsboard
    for i in address[:-1]:
        if(i not in temp):
            temp[i] = {}
        temp = temp[i]
            
    temp[address[-1]] = addr

def getClientfromTopic(topic):
    filterTopic = topic.split('/')
    addr = g.deviceThingsboard
    for i in g.indexDeviceTopic:
        if filterTopic[i] in addr:
            addr = addr[filterTopic[i]]
        else: 
            return -1
    
    return addr
        

class clientMQTT():
    _client = mqttclient
    
    def __init__(self):
        self._client = mqttclient.Client()
        self._client.username_pw_set(g.USERNAME)
        # self._client.on_connect = self.connect
        self._client.connect(g.MQTT_BROKER_ADDRESS, g.MQTT_BROKER_PORT)
        self._client.on_message = self.onmessage
        self._client.loop_start()
        
    def connect(client, userdata, flags, rc):
        if rc == 0:
            print("Ket noi thanh cong..."+str(rc))
        else:
            print("ket noi khong thanh cong... loi=" + str(rc))
    def processUpData(self, data):
        data = data.replace('*', '')
        data = data.replace("#<LF>", "")
        result = data.split(",")
        result[4:] = [','.join(result[4:])]
        result[:4] = [','.join(result[:4])]
        print(result)
        return result
    
    def publishData(self, deviceName, msg):
        mess = self.processUpData(msg)
        message = {
        "telemetry": mess[0],
        "attributes": mess[1]
        }
        topic = "tcp/"+deviceName+"/data" 
        self._client.publish(topic, json.dumps(message))
        print("send data ", msg, " successfully")
        sleep(2)
    def subscribeTopic(self, topic):
        # topic = "tcp/"+topic+"/set" 
        topic= "hex/test/demo"
        self._client.subscribe(topic=topic)
        print('Subscribed to topic: ', topic)
        
    def onmessage(self, client, userdata, message):
        print("Receive message " + message.payload.decode('utf8') + " from topic: " + str(message.topic))
        addr = getClientfromTopic(message.topic)
        if addr == -1:
            pass
        g.clients[addr].send(message.payload)

class SocketServer():
    serv = socket

    def __init__(self, client):
        self.client_thingsboard = client
        self.serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # create a socket TCP
        __bind = False
        while not __bind:
            try:
                self.serv.bind(('0.0.0.0', g.my_port_server))
            except OSError:
                print('Address already in use. Reconnecting...')
                self.serv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sleep(3)
            else:
                __bind = True
        self.serv.listen(10) # listen up to 10 clients
        self.serv.getsockname()
    
    def run(self):
        print("Server started")
        try:
            self.accept_clients()
        except Exception as ex:
            print(ex)
        finally:
            print("Server closed")
            for client in g.clients:
                self.onclose(client)

    def accept_clients(self):
        while True:
            clientsocket, address = self.serv.accept()
            #Adding client to clients list
            g.clients[address] = clientsocket
            #Client Connected
            self.onopen(clientsocket, address)
            #Receiving data from client
            Thread(target=self.recieve, args=(clientsocket,address,)).start()
            
    def recieve(self, client, addr):
        while True:
            data = client.recv(1024)
            if not data:
                break
            #Message Received
            self.onmessage(addr, data)
        #Removing client from clients list
        self.clients.remove(client)
        #Client Disconnected
        self.onclose(client)
        #Closing thread
        print(self.clients)

    def broadcast(self, message):
        #Sending message to all clients
        for client in self.clients:
            client.send(message)

    def onopen(self, client, addr):
        print("Connectd from: addr=", addr)
        pass

    def onmessage(self, addr, message):
        print("Data from ", addr, ":", message.decode('utf8'))
        (ip, port) = addr
        try:
            deviceName = getIdDeviceOMNI(message.decode('utf8'))
            addToDictionary(deviceName, addr)
        except:
            print("Invalid message!")
            return
        if(deviceName not in g.subscribedTopic):
            self.client_thingsboard.subscribeTopic(deviceName)
            g.subscribedTopic[deviceName] = 1
        self.client_thingsboard.publishData(deviceName, message.decode('utf8'))
        pass

    def onclose(self, client):
        #Closing connection with client
        client.close()
        pass
# SocketServer().run()
if __name__ == '__main__':
    
    clientMQTT = clientMQTT()
    
    my_server = SocketServer(clientMQTT)
    my_server.run()
    