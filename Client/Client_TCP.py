import socket
import rsa
import sys
import threading
import time

# Client Asymmetric Keys






# colocar pra receber pelo terminal
#address = input("Insert the Address -> ")



def handle_disconnection(server_connection, stop_event, host_public_key):

    server_connection.sendall(rsa.encrypt("/quit".encode("utf-8"), host_public_key))
    print("\n-> Disconnecting...")
    
    try:
        server_connection.close()
    except:
        pass
    stop_event.set()
    print("-> Disconnected")

# falta usar o stop event, 


def host_listener(server_connection, stop_event, client_private_key):
    # The decoded_message Needs to be on 

    # - Client's Name Request - #
    host_name_request = server_connection.recv(1024)
    if not stop_event.is_set():
            decoded_host_name_request = rsa.decrypt(host_name_request, client_private_key).decode("utf-8")
            print(decoded_host_name_request, end="") # Remove '\n' for Aesthetic Pourposes
    else:
        return

    while not stop_event.is_set():
        
        
        encoded_host_message = server_connection.recv(1024)

        if encoded_host_message:
            decoded_host_message = rsa.decrypt(encoded_host_message, client_private_key).decode("utf-8") # The decoded_message Needs to be on Bytes Format to Turn into String

        
            if decoded_host_message != "quit":
                print(decoded_host_message)
            else:
                stop_event.set() ##########
                break
        else:
            print("-> Connection with Host Expired due to Inactivity")
            stop_event.set() ######33
            break






def client_sender(server_connection, stop_event, host_public_key):

    while not stop_event.is_set():
        
        message = input()

        # The encoded_message Needs to be on String Format to Turn Into Bytes
        encoded_message = rsa.encrypt(message.encode("utf-8"), host_public_key)

        try:
            server_connection.sendall(encoded_message)
        except:
            print("-> Connection with Host Expired due to Inactivity")
            stop_event.set() #################3
            break






def main():

    try: # - TCP Connection - #
        try:
            server_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_connection.connect(("8.tcp.ngrok.io", 15368))
        except Exception:
            # print(f"Couldn't Connect to {address}:{port}.")
            print(f"-> Couldn't Connect to Specified Address : {Exception}")
            sys.exit(1)

        # - Initial Handshake - #
        ## - Client Asymmetric Keys - ##
        client_public_key, client_private_key = rsa.newkeys(2048)
        print("-> Client Asymmetric Keys Generated...")

        ## - Receive Host Public Key - ##
        try:
            host_public_key = server_connection.recv(1024)
            host_public_key =  rsa.PublicKey.load_pkcs1(host_public_key, "PEM")
            print("-> Host Public Key Received Successfully...")
        except Exception:
            print(f"-> Failed to Resolve Host's Public Key: {str(Exception)}")
            server_connection.close()
            sys.exit(1)
        ## - Send Client Public Key - ##
        try:
            server_connection.sendall(client_public_key.save_pkcs1("PEM"))
            print("-> Client Public Key Sent Succefully...")
        except Exception:
            print(f"-> Failed to Send Client's Public Key: {str(Exception)}")
            server_connection.close()
            sys.exit(1)

        # - Threading - #
        ## - End All Threads when Set - ##
        stop_event = threading.Event()

        ## - Start Client Sending Thread - ##
        start_client = threading.Thread(target=client_sender, args=(server_connection, stop_event, host_public_key))
        start_client.daemon = True   # Avoiding Zombie Proccesses
        start_client.start()

        ## - Start Host Listening Thread - ##
        host_join = threading.Thread(target=host_listener, args=(server_connection, stop_event, client_private_key))
        host_join.start()

        ## - Make main() Run until stop_event is set - ##
        while not stop_event.is_set():  # By doing this, it's possible to solve a KeyboardInterrupt
            time.sleep(1)

        handle_disconnection(server_connection, stop_event, host_public_key)
        sys.exit(1) # The code comes here after any disconnection
        # VERIFICAR SE EU FECHEI TODAS AS THREADS
    except KeyboardInterrupt:

        handle_disconnection(server_connection, stop_event, host_public_key)
        sys.exit(1)




if __name__=="__main__":
    main()
# Recebendo dados
    #   pacotes_recebidos = client.recv(4068)
     #   print(f"Received: {pacotes_recebidos.decode()}")






#try to ip spoof 