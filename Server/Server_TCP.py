import socket
from pyngrok import ngrok   # Turning a listener on
import yaml                 # Reading authentication token

import rsa
import sys

import threading
import time
"""
Server
1 - Initializes Main
  1.1 - Ngrok Setup and Connection
  1.2 - Generates host's Public and Private SSL keys
  1.3 - Threading to make communication in real time
      1.3.1 - "handle_client_connection" thread searches for new connections every time
            1.3.1.2 - If a new connection is found, they exchange keys, the client receives the host's public key, and the host receives the client's public key
            1.3.1.3 - Registers client if everything go as expected, avoiding names that could break the connection, and avoinding that any timeout breaks the code
            1.3.1.4 - If everything is right, a new thread called "clients_listeners" starts
                    1.3.1.4.1 - the "clients_listeners" thread make the connection with the client, searching for new messages everytime
                    1.3.1.4.2 - if the client asks to leave, the "handle_client_disconnections" is called
      1.3.2 - "host_sender" thread searchs for new host messages everytime
  1.4 - There is a loop in the end of "main", that handles KeyboardInterruptions if they happen

"""

# Create Clients List

# Mata todas as threads

# Waits Every Time for a Connection Request
def handle_client_connections(server, stop_event, clients_dictionary, host_public_key, host_private_key):
    
    """
    Handles new client connections including:
    - RSA key exchange
    - Client registration 
    - Thread creation for message listening
    """

    client_counter = 0

    while not stop_event.is_set():

        server.listen(5)
        client_socket, _ = server.accept() # client_address is Irrelevant Due to Ngrok Tunneling (switched for '_')

        if client_socket:


            client_counter += 1  # New Client
            print("-> Stablishing New Connection...")


            # - New Client Handling - #
            ## - Initial Handshake - ##
            ### - Send Host Public Key - ###
            try:
                client_socket.sendall(host_public_key.save_pkcs1("PEM"))
            except Exception:
                print(f"-> Failed to Send Host's Public Key: {str(Exception)}")
                client_socket.close()
                continue    # Go to While Loop Start
            ### - Receive Client Public Key - ###
            try: 
                client_public_key = client_socket.recv(1024)
                client_public_key =  rsa.PublicKey.load_pkcs1(client_public_key, "PEM")
                print("-> Client Public Key Received Successfully...")
            except Exception:
                print(f"-> Failed to Resolve Client's Public Key: {str(Exception)}")
                client_socket.close()
                continue


            ## - Registering Client - ##
            client_socket.sendall(rsa.encrypt("Your Name -> ".encode("utf-8"), client_public_key))
            encoded_client_name = client_socket.recv(1024)

            if encoded_client_name:
                
                decoded_client_name = rsa.decrypt(encoded_client_name, host_private_key).decode("utf-8")

                ### - Avoiding KeyboardInterruption - ### -> This keeps clients_dictionary clean from possible trash data TALVEZ FAZER COM ELSE AO INVES DE CONTINUE
                client_id = "client" + str(client_counter)
                clients_dictionary[client_id] = {"name": decoded_client_name, "socket": client_socket, "public_key" : client_public_key}

                if decoded_client_name == "/quit":
                    handle_client_disconnections(client_id, clients_dictionary, True)
                    continue

                ## - Starting Client's Listener - ##
                print(f"-> Connection Stabilished with \"{decoded_client_name}\"...") # tentar enviar para todos os clientes no futuro
                client_listener = threading.Thread(target=clients_listeners, args=(client_id, stop_event, clients_dictionary, host_public_key, host_private_key))
                client_listener.daemon = True
                client_listener.start()

            # timeout #
            else:
                handle_client_disconnections(client_id, clients_dictionary, False) ## NEM SEMPRE VAI TER UM PERFIL CRIADO
                continue









def handle_client_disconnections(client_id, clients_dictionary, has_client_profile):

   
    clients_dictionary[client_id]["socket"].sendall(rsa.encrypt("quit".encode("utf-8"), clients_dictionary[client_id]["public_key"])) # If client alters the "SIGINT" reception, it doesn't matter, he is already off, the error will only happen on his side
    client_disconnect_message = f"-> Connection with \"{clients_dictionary[client_id]["name"]}\" Closed." # tentar padronizar bglh de string


    ## - Broadcast Any Client Message to Everyone- ###
    print(client_disconnect_message)
    for client in clients_dictionary:
        if clients_dictionary[client]["name"] != clients_dictionary[client_id]["name"]:
                clients_dictionary[client]["socket"].sendall(rsa.encrypt(client_disconnect_message.encode("utf-8"), clients_dictionary[client]["public_key"]))  

    clients_dictionary[client_id]["socket"].close()
    clients_dictionary.pop(client_id, None)








def clients_listeners(client_id, stop_event, clients_dictionary, host_public_key, host_private_key):
        
        # - Retrieving Respective Client Thread Data - #  -> This is useful to avoid a client message getting sent to itself
        client_name = clients_dictionary[client_id]["name"]
        client_socket = clients_dictionary[client_id]["socket"]
        client_public_key = clients_dictionary[client_id]["public_key"]


        # features : clientes verem quem entra e sai
        
        # - Simple Warning - # melhorar o nome disso
        warning_message = "(If you want to leave the chat, write nothing but \"/quit\")\n"
        encoded_warning_message = rsa.encrypt(warning_message.encode("utf-8"), client_public_key)
        client_socket.sendall(encoded_warning_message)

        quit = False
        while not stop_event.is_set() and quit == False:

            # - Message Receiving - #
            encoded_client_message = client_socket.recv(1024) # Infinite loop that waits for a message from client

            ## - Verify if Message was Received - ##
            if encoded_client_message:
                
                decoded_client_message = rsa.decrypt(encoded_client_message, host_private_key).decode("utf-8") # The decoded_message Needs to be on Bytes Format to Turn into String
  
                
                ## - Handles Exit Requests - ##
                if decoded_client_message != "/quit":
                    decoded_broadcast = client_name + ":" + decoded_client_message
                # Verify Exit Request
                else:
                    handle_client_disconnections(client_id, clients_dictionary)
                    break

                ## - Broadcast Any Client Message to Everyone- ##
                print(decoded_broadcast)
                for client in clients_dictionary:
                    if clients_dictionary[client]["name"] != client_name:
                        encoded_broadcast = rsa.encrypt(decoded_broadcast.encode("utf-8"), clients_dictionary[client]["public_key"])
                        clients_dictionary[client]["socket"].sendall(encoded_broadcast)          

            ## - Timeout - ##
            else:
                handle_client_disconnections(client_id, clients_dictionary, True)
                break
                



def host_sender(server, tunnel, stop_event, clients_dictionary, host_public_key, host_private_key):

    print("(If you want to close the chat, write nothing but \"/close\")\n")

    while not stop_event.is_set():

        host_message = input()

        if host_message != "/close":
                
            # - Broadcast Host Message to All Clients - #
            host_message = "Host: " + host_message
            for client in clients_dictionary:
                encoded_message = rsa.encrypt(host_message.encode("utf-8"), clients_dictionary[client]["public_key"])
                clients_dictionary[client]["socket"].sendall(encoded_message)
                
        else: 
                
            # - Close Server - #
            ## - Client Disconnect - ##
            print("-> Closing Server...")
            for client in clients_dictionary:
                encoded_message = rsa.encrypt("Server Closed by Host.".encode("utf-8"), clients_dictionary[client]["public_key"])
                encoded_message = rsa.encrypt("/close".encode("utf-8"), clients_dictionary[client]["public_key"]) # ADAPTAR ISSO NO CLIENT
                clients_dictionary[client]["socket"].sendall(encoded_message)
                clients_dictionary[client]["socket"].close()
            print("-> Client Connections Closed")

            ## - Server Disconnect - ##
            server.close()
            time.sleep(2)
            try:
                ngrok.disconnect(tunnel.public_url)
            except:
                print("-> Ngrok tunnel closed.")

            print("-> Server Closed.")

            ## - End Program - ##
            stop_event.set()    
            sys.exit(0)    
               




def main():

    # - Server Setup - #
    ## - Ngrok Setup - ##
    ### - Token Path - ###
    try:
        with open('/home/host/.config/ngrok/ngrok.yml', 'r') as file:   
            config = yaml.safe_load(file)
    except:
        print("-> Error: Couldn't Find ngrok.yml File (authtoken)")
        sys.exit(1)
    ### - Ngrok Connection - ###
    try:
        ngrok.set_auth_token(config["agent"]["authtoken"])
        tunnel = ngrok.connect("7000", "tcp")   # Port > 1023
        print("\n" + str(tunnel))
    except:
        print("-> Couldn't Tunnel Connection with Ngrok")
        sys.exit(1)

    ## - Localhost TCP Port Opening - ##
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server.bind(("localhost", 7000))
    except Exception as error:
        print(error)
        ngrok.disconnect(tunnel.public_url)
        sys.exit(1)


    # - Host Asymmetric Keys - #
    host_public_key, host_private_key = rsa.newkeys(2048)
    print("-> Host Asymmetric Keys Generated..." + "\n")


    clients_dictionary = {} # Name, Socket and Public Key from every client

    # - Thread Managing - #
    stop_event = threading.Event() # Thread Killer

    ## - Handle Client Connection - # -> Verify Connection Requests and Starts Client Listener if Approved
    client_connection = threading.Thread(target=handle_client_connections, args=(server, stop_event, clients_dictionary, host_public_key, host_private_key))
    client_connection.daemon = True   # Avoiding Zombie Proccesses
    client_connection.start()

    ## - Handle Host Connection - # 
    host_start = threading.Thread(target=host_sender, args=(server, tunnel, stop_event, clients_dictionary, host_public_key, host_private_key))
    host_start.start()

        


if __name__=="__main__":
    main()