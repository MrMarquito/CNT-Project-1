# Alyssa Hooper 6430685
# Marcos Cruz 6342207
# Shelby Larrucea 6408951
# Jacob Mendelson 6473225

from socket import *   
import sys             
import os              

# Send QUIT command 
def quitFTP(clientSocket):
    command = "QUIT\r\n"                   
    clientSocket.sendall(command.encode("utf-8"))  
    dataIn = clientSocket.recv(1024)      
    print(dataIn.decode("utf-8"))           


# Send command over control connection
def sendCommand(sock, command):
    sock.sendall(command.encode("utf-8"))   
    dataIn = sock.recv(1024)                 
    return dataIn.decode("utf-8")            


# Receive data from control connection
def receiveData(sock):
    dataIn = sock.recv(1024)                 
    return dataIn.decode("utf-8")            


# Enter Passive Mode
# Server responds for data connection
def modePASV(clientSocket):

    command = "PASV\r\n"                  
    clientSocket.sendall(command.encode("utf-8")) 

    data = clientSocket.recv(1024).decode("utf-8") 
    print(data)                             

    status = 0
    dataSocket = None

    # Check if server responded with 227 
    if data.startswith("227"):

        status = 227


        start = data.find("(")
        end = data.find(")")
        parts = data[start+1:end].split(",")

        ip = parts[0] + "." + parts[1] + "." + parts[2] + "." + parts[3]

        port = int(parts[4]) * 256 + int(parts[5])

        dataSocket = socket(AF_INET, SOCK_STREAM)

        dataSocket.connect((ip, port))

    return status, dataSocket


# Main Program
def main():

    
    if len(sys.argv) < 2:
        print("Usage: python myftp.py server-name")
        sys.exit()

    HOST = sys.argv[1]     

    # login credentials
    username = input("Enter the username: ")
    password = input("Enter the password: ")

    # Create socket for control connection
    clientSocket = socket(AF_INET, SOCK_STREAM)

    # Connect to FTP server on port 21
    clientSocket.connect((HOST, 21))

    
    dataIn = receiveData(clientSocket)
    print(dataIn)

    status = 0

    # Login Process

    # Check if server sent 220 
    if dataIn.startswith("220"):

        
        reply = sendCommand(clientSocket, f"USER {username}\r\n")
        print(reply)

        # If server asks for password (331)
        if reply.startswith("331"):

            
            reply = sendCommand(clientSocket, f"PASS {password}\r\n")
            print(reply)

            # If login works
            if reply.startswith("230"):
                status = 230

    # If login failed
    if status != 230:
        print("Login failed.")
        clientSocket.close()
        sys.exit()

    # Command loop

    # Keep running until user types quit
    while True:

        command = input("myftp> ")   

        # ls
        if command == "ls":

            pasvStatus, dataSocket = modePASV(clientSocket)

            if pasvStatus == 227:

                # Send LIST command
                reply = sendCommand(clientSocket, "LIST\r\n")
                print(reply)

                data = dataSocket.recv(4096).decode("utf-8")
                print(data)

                dataSocket.close()   # Close data connection

                # Receive final confirmation 
                finalReply = receiveData(clientSocket)
                print(finalReply)

        # cd
        elif command.startswith("cd "):

            directory = command.split(" ", 1)[1]

            reply = sendCommand(clientSocket, f"CWD {directory}\r\n")
            print(reply)

        # get
        elif command.startswith("get "):

            filename = command.split(" ", 1)[1]

            pasvStatus, dataSocket = modePASV(clientSocket)

            if pasvStatus == 227:

                reply = sendCommand(clientSocket, f"RETR {filename}\r\n")
                print(reply)

                if reply.startswith("150"):

                    file = open(filename, "wb")  # Open local file 
                    totalBytes = 0

                    # Receive file 
                    while True:
                        data = dataSocket.recv(4096)
                        if not data:
                            break
                        file.write(data)
                        totalBytes += len(data)

                    file.close()
                    dataSocket.close()

                    finalReply = receiveData(clientSocket)
                    print(finalReply)

                    print("Downloaded", totalBytes, "bytes")

        # put
        elif command.startswith("put "):

            filename = command.split(" ", 1)[1]

            # Check if file exists locally
            if not os.path.exists(filename):
                print("File does not exist.")
                continue

            pasvStatus, dataSocket = modePASV(clientSocket)

            if pasvStatus == 227:

                reply = sendCommand(clientSocket, f"STOR {filename}\r\n")
                print(reply)

                if reply.startswith("150"):

                    file = open(filename, "rb")
                    totalBytes = 0

                    # Send file 
                    while True:
                        data = file.read(4096)
                        if not data:
                            break
                        dataSocket.sendall(data)
                        totalBytes += len(data)

                    file.close()
                    dataSocket.close()

                    finalReply = receiveData(clientSocket)
                    print(finalReply)

                    print("Uploaded", totalBytes, "bytes")

        # delete
        elif command.startswith("delete "):

            filename = command.split(" ", 1)[1]

            # Send command
            reply = sendCommand(clientSocket, f"DELE {filename}\r\n")
            print(reply)

        # quit
        elif command == "quit":

            quitFTP(clientSocket)
            break

        # invalid
        else:
            print("Invalid command")

    print("Disconnecting...")
    clientSocket.close()
    sys.exit()


# Start
main()
