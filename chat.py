import socket
import threading
from time import time
import tkinter as tk
import tkinter.scrolledtext as st


hostname = socket.gethostname()
SERVER = socket.gethostbyname(hostname) 

DISCONNECT = '#EXIT#'
HEADER = 128
FORMAT = 'utf-8'
PORT = 5050

clients = []
client_names = {}

startt = 0

def broadcast(message, sender_conn=None):
    for client in clients:
        if client != sender_conn:
            try:
                msg_encoded = message.encode(FORMAT)
                msg_len = str(len(msg_encoded)).encode(FORMAT)
                msg_len += b' ' * (HEADER - len(msg_len))
                client.send(msg_len)
                client.send(msg_encoded)
            except:
                clients.remove(client)

def manage_client(con, addr):
    print(f'{addr} fellépett!\n')
    
    connected = True
    client_name = str(addr)
    msg = ''
    
    while connected:
        try:
            msg_len = con.recv(HEADER).decode(FORMAT)
        except:
            msg = '###########'
        
        if msg != '###########':
            msg_len = int(msg_len)
            msg = con.recv(msg_len).decode(FORMAT)
        
            if '#NAME# ' in msg:
                client_name = msg.replace('#NAME# ', '')
                client_names[con] = client_name
                broadcast(f'{client_name} csatlakozott a chathez', con)
            
            else:
                print(f'{client_name}: {msg}')
                broadcast(f'\n{client_name}: {msg}', con)
        
        else:
            connected = False
            print(f'{client_name} Kilépett!')
            broadcast(f'\n {client_name} kilépett a chatből', con)
    
    if con in clients:
        clients.remove(con)
    if con in client_names:
        del client_names[con]
    con.close()

def start(live_server):
    live_server.listen()
    while True:
        con, addr = live_server.accept()
        clients.append(con)
        thread = threading.Thread(target=manage_client, args=(con, addr))
        thread.start()
        print(f'szerver méret: {threading.active_count() - 1}\n')

def send(msg, live_server):
    global endt
    global startt
    global output_msg

    if not '#NAME#' in msg:
        output_msg.insert(tk.INSERT, msg + '\n')
        output_msg.see('end')

    endt = int(time() * 1000)
    if endt - startt >= 500 or startt == None:
        msg += '\n'
        msg_to_send = msg.encode(FORMAT)
        msg_len = len(msg_to_send)
        send_len = str(msg_len).encode(FORMAT)
        send_len += b' ' * (HEADER - len(send_len))
        live_server.send(send_len)
        live_server.send(msg_to_send)
        startt = int(time() * 1000)

def receive(live_server):
    while True:
        try:
            msg_len = live_server.recv(HEADER).decode(FORMAT)
            if msg_len:
                msg_len = int(msg_len.strip())
                msg = live_server.recv(msg_len).decode(FORMAT)
                print(msg)
                global output_msg
                if not '#NAME#' in msg:
                    output_msg.insert(tk.INSERT, msg + '\n')
                    output_msg.see('end')
        except:
            break

def server():
    ADDR = (SERVER, PORT)
    live_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    live_server.bind(ADDR)
    print('Indul a szerver...')
    start(live_server)

def client():
    ADDR = (input('address: '), PORT)
    live_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    live_server.connect(ADDR)

    receive_thread = threading.Thread(target=receive, args=(live_server,))
    receive_thread.start()

    name = '#NAME# ' + input('Név: ')
    send(name, live_server)

    window = tk.Tk()
    window.title('Chat')

    output_label = tk.Label(window, text = 'Output') 
    global output_msg
    output_msg = st.ScrolledText(window, height = 15, width = 50, wrap = 'word', bg = 'light blue')

    input_label = tk.Label(window, text = 'Input') 
    input_msg = tk.Text(window, height = 15, width = 50, wrap = 'word', bg = 'light green')

    send_button = tk.Button(window, height = 2, width = 20, text = 'Üzenet küldése', command = lambda:send(input_msg.get("1.0", "end-1c"),live_server))

    output_label.pack()
    output_msg.pack()
    input_label.pack()
    input_msg.pack()
    send_button.pack()
    window.mainloop()

choice = input('host/csatlakozás? (h/c) ')
if choice == 'c':
    client()
elif choice == 'h':
    print(hostname, SERVER)
    server()