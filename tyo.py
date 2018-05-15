#!/usr/bin/python
# -*- coding: utf-8 -*-

# The modules required
import sys
import socket
import random
import string
import struct


def send_and_receive_tcp(address, port):
    
    #Socket creation
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((address, port))

    #Creation of keys
    ownKeys = []
    message = ("HELLO ENC\r\n") # ENC
    for j in range(0,20):
        randomS = [random.choice(string.hexdigits) for i in range(64)]
        randomString = "".join(randomS)
        message = message + randomString + "\r\n"
        #ownKeys.insert(0, randomString)
        ownKeys.append(randomString)
    message = message + ".\r\n"

    #Data transfer
    s.send(message)    
    data = s.recv(1024)
    s.close()

    datalist = data.split("\r\n")
    tokenAndPortList = datalist[0].split(' ')
    token = tokenAndPortList[1]
    udpPort = tokenAndPortList[2]
    return datalist, token, udpPort, ownKeys


def send_and_receive_udp(address, port, datalist, token, ownKeys):
    
    #Socket creation and bind
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('', int(port)))
    
    #Variables
    ack = True
    eom = False
    dataRemaining = 0
    content = "Hello from " + token
    contentLen = len(content)

    #Encryption
    m = 0
    encryptionKey = ownKeys[m]
    encryptedContent = ""
    k = 0
    j = 0
    for i in content:
        encryptedContent = encryptedContent + (chr(ord(content[k]) ^ ord(encryptionKey[j])))
        j = j + 1
        k = k + 1
    m = m + 1

    #First UDP-packet send
    daatta = struct.pack('!8s??HH64s', token, ack, eom, dataRemaining, contentLen, encryptedContent)
    s.sendto(daatta, (address, int(port)))
    
    unencryptedContent = ""

    #First UDP-packet receive
    data, addr = s.recvfrom(2048)
    token, ack, eom, dataRemaining, contentLen, encryptedContent = struct.unpack('!8s??HH64s', data)

    #Decryption
    l = 1
    decryptionKey = datalist[l]
    k = 0
    j = 0
    for i in range(contentLen):
        unencryptedContent = unencryptedContent + (chr(ord(encryptedContent[k]) ^ ord(decryptionKey[j])))
        j = j + 1
        k = k + 1
    l = l + 1 

    #Reversed order              
    temp = unencryptedContent.split()
    temp.reverse()
    reversedContent = " ".join(temp)

    while True: 
        #Encryption
        encryptionKey = ownKeys[m]
        encryptedContent = ""
        k = 0
        j = 0
        for i in reversedContent:
            encryptedContent = encryptedContent + (chr(ord(reversedContent[k]) ^ ord(encryptionKey[j])))
            j = j + 1
            k = k + 1
        m = m + 1
        
        #Second and so on UDP-packet send
        daatta = struct.pack('!8s??HH64s', token, ack, eom, dataRemaining, len(encryptedContent), encryptedContent)
        s.sendto(daatta, (address, int(port)))

        #Second and so on UDP-packet receive
        data, addr = s.recvfrom(2048)
        token, ack, eom, dataRemaining, contentLen, encryptedContent = struct.unpack('!8s??HH64s', data)
        
        # Check if eom == True
        if eom == True:
            print(encryptedContent)
            break

        #print(encryptedContent) #remove from comments if you want to see received content

        #Decryption
        decryptionKey = datalist[l]
        k = 0
        j = 0
        unencryptedContent = ""
        for i in range(contentLen):
            unencryptedContent = unencryptedContent + (chr(ord(encryptedContent[k]) ^ ord(decryptionKey[j])))
            j = j + 1
            k = k + 1
        l = l + 1
        
        #print(unencryptedContent) #remove from comments if you want to see received content              
        temp = unencryptedContent.split()
        temp.reverse()
        reversedContent = " ".join(temp)

    s.close()
    return


def main():
    USAGE = 'usage: %s <server address> <server port>' % sys.argv[0]

    try:
        server_address = str(sys.argv[1])
        server_tcpport = int(sys.argv[2])
        data, token, udpPort, ownKeys = send_and_receive_tcp(server_address, server_tcpport)
        send_and_receive_udp(server_address, udpPort, data, token, ownKeys)
    except (IndexError, ValueError):
        sys.exit(USAGE)



if __name__ == '__main__':
    main()
