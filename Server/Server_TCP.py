import socket
from pyngrok import ngrok   # Turning a listener on
import yaml                 # Reading authentication token

import threading



# Ngrok Setup
# insert token path
try:
    with open('/home/host/.config/ngrok/ngrok.yml', 'r') as file:   
        config = yaml.safe_load(file)
except:
    print("Error: Couldn't Find ngrok.yml File (authtoken)")
    exit()
ngrok.set_auth_token(config["agent"]["authtoken"])
tunnel = ngrok.connect("7000", "tcp")   # Port > 1023
print(tunnel)



# Create Clients List
clients = []
# Mata todas as threads
stop_event = threading.Event()

clientes = {}




def clients_listeners(client_socket, client_name):
        


        client_socket.send("If you want to leave the chat, write nothing but \"/quit\"\n".encode())


        while not stop_event.is_set():

            # Message Receiving
            client_message = client_socket.recv(1024).decode()
            

            if client_message:

                # Verify Exit Request
                if client_message == "/quit\n":
                    print(f"Connection with \"{client_name}\" Closed.")
                    clients.remove(client_socket)
                    client_socket.close()
                    break

                # Send the Message for All Other Clients
                for client in clients:
                    if client != client_socket:     
                        client.send(f"{client_name} : {client_message}".encode())
                
                # Print for Host
                print(f"{client_name} : {client_message}", end = "")



def host_listener(server):

    while not stop_event.is_set():


        host_message = input()


        if host_message:
        
            # ARRUMAR ISSO
            if host_message == "/close":

                host_message = "Server Closed by Host."
                print(host_message)
                for client in clients:
                    client.send(host_message.encode())

            
                for client in clients:
                    client.close()
                    
                ngrok.disconnect(tunnel.public_url)
                server.close()
                stop_event.set()    
                exit()    

            # Send the Message for All Clients
            host_message = "Host : " + host_message + "\n"
            for client in clients:
                client.send(host_message.encode())



# Waits every time to someone joning
def join(server):
    
    while not stop_event.is_set():

        server.listen(5)
        client_socket, _ = server.accept() # client_address is Irrelevant Due to Ngrok Tunneling (switched for '_')
        clients.append(client_socket)

        if client_socket:
            
            # Get the client's custom name
            client_socket.send("Your Name -> ".encode())
            client_name = client_socket.recv(1024).decode().strip()

            client_listener = threading.Thread(target=clients_listeners, args=(client_socket, client_name))
            client_listener.daemon = True
            client_listener.start()

            print(f"Connection Stabilished with \"{client_name}\"...")


# Opens TCP Connection on Specified Port
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    server.bind(("localhost", 7000))
except Exception as error:
    print(error)


print("If you want to close the chat, write nothing but \"/close\"\n")

# Verify Join Requests and Starts Client Listener if Approved
client_join = threading.Thread(target=join, args=(server, ))
client_join.daemon = True   # Avoiding Zombie Proccesses
client_join.start()

# Starts Host Listener
host_join = threading.Thread(target=host_listener, args=(server, ))
host_join.start()








