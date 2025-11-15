#importok
import socket
import threading
import tkinter as tk
import tkinter.scrolledtext as st
from time import time

#host adatok
hostname = socket.gethostname()
SERVER = socket.gethostbyname(hostname) 

#konstansok
HEADER = 128
FORMAT = 'utf-8'
PORT = 5050

#kliensek
clients = []
client_names = {}

#időmérő deklarálása
startt = 0

#üzenetek továbbküldése
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

#kliens management
def manage_client(con, addr):
    global output_msg
    
    connected = True
    client_name = str(addr)
    msg = ''
    
    while connected:
        #a host megpróbál hozzáférni a legutóbbi üzenethez (ha nem sikerül = kapcsolat megszakadt)
        try:
            msg_len = con.recv(HEADER).decode(FORMAT)
        except:
            msg = '###########'
        
        if msg != '###########':
            #üzenet dekódolása
            msg_len = int(msg_len)
            msg = con.recv(msg_len).decode(FORMAT)
        
            #névváltoztatás
            if '#NAME# ' in msg:
                client_name = msg.replace('#NAME# ', '')
                client_names[con] = client_name
                insert_to_output_msg(f'{client_name} csatlakozott a chathez')
                broadcast(f'{client_name} csatlakozott a chathez', con)
            
            #üzenet tovább küldése
            else:
                insert_to_output_msg(f'{client_name}: {msg}')
                broadcast(f'\n{client_name}: {msg}', con)
        
        #Kilépés
        else:
            connected = False
            insert_to_output_msg(f'{client_name} Kilépett!')
            broadcast(f'\n {client_name} kilépett a chatből', con)
    
    if con in clients:
        clients.remove(con)
    if con in client_names:
        del client_names[con]
    con.close()

#szerver indítása
def start(live_server):
    global output_msg
    live_server.listen()
    while True:
        con, addr = live_server.accept()
        clients.append(con)
        thread = threading.Thread(target = manage_client, args=(con, addr))
        thread.start()
        insert_to_output_msg(f'szerver méret: {threading.active_count() - 1}')

#üzenet küldés
def send(msg, live_server):
    global endt
    global startt
    global output_msg

    if not '#NAME#' in msg:
        insert_to_output_msg(msg)

    #üzenet küldés, ha nincs átlépve a limit (0.5 másodperc minden üzenet után)
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

    #túl gyakori üzenetküldés megakadályozása
    elif endt - startt < 500:
        insert_to_output_msg('Várj 0.5 másodpercet minden üzenet között!')

#üzenet fogadás
def receive(live_server):
    global output_msg

    while True:
        try:
            msg_len = live_server.recv(HEADER).decode(FORMAT)
            if msg_len:
                msg_len = int(msg_len.strip())
                msg = live_server.recv(msg_len).decode(FORMAT)
                if not '#NAME#' in msg:
                    insert_to_output_msg(msg)
        except:
            break

#szerver futtatása + vizuális felület
def server():
    global output_msg

    #vizuális felület létrehozása
    server_window = tk.Tk()
    server_window.title('Chat')

    #vizuális elemek hozzáadása
    output_label = tk.Label(server_window, text = 'Output') 
    output_msg = st.ScrolledText(server_window, height = 15, width = 50, wrap = 'word', bg = 'light blue')
    output_msg.config(state = 'disabled')

    insert_to_output_msg(hostname + ' ' + SERVER)

    #szerver futtatás
    ADDR = (SERVER, PORT)
    live_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    live_server.bind(ADDR)

    #vizális elemek elhelyezése
    output_label.pack()
    output_msg.pack()

    #start() függvény indítása külön thread-en
    server_thread = threading.Thread(target = start, args = ( live_server ), daemon = True)
    server_thread.start()
    output_msg.config(state = 'disabled')

    server_window.mainloop()

#kliens futtatása + vizuális felület
def client():
    global output_msg

    #csatlakozás szerverhez
    ADDR = (input('address: '), PORT)
    live_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    live_server.connect(ADDR)

    #receive() függvény indítása külön thread-en
    receive_thread = threading.Thread(target = receive, args = ( live_server ))
    receive_thread.start()

    #Név megadása
    name = '#NAME# ' + input('Név: ')
    send(name, live_server)

    #vizuális felület létrehozása
    client_window = tk.Tk()
    client_window.title('Chat')
    print('Chat megnyitva új ablakban')

    #vizuális elemek hozzáadása
    output_label = tk.Label(client_window, text = 'Output') 
    output_msg = st.ScrolledText(client_window, height = 15, width = 48, wrap = 'word', bg = 'light blue')

    input_label = tk.Label(client_window, text = 'Input') 
    input_msg = tk.Entry(client_window, width = 40, bg = 'light green')

    send_button = tk.Button(client_window, height = 2, width = 20, text = 'Üzenet küldése', command = lambda:send(input_msg.get(),live_server))
    client_window.bind('<Return>',lambda event: send(input_msg.get(),live_server))

    #vizális elemek elhelyezése
    output_label.pack()
    output_msg.pack(padx = 5)
    input_label.pack()
    input_msg.pack()
    send_button.pack(pady = 5)

    client_window.mainloop()

#szöveg elhelyezése az output mezőbe
def insert_to_output_msg(msg):
    global output_msg
    output_msg.config(state = 'normal')
    output_msg.insert(tk.INSERT, msg + '\n')
    output_msg.see('end')
    output_msg.config(state = 'disabled')   

choice = input('host/csatlakozás? (h/c) ')
if choice == 'c':
    client()
elif choice == 'h':
    server()