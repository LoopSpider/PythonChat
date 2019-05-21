import threading
import socket
import json
from tkinter import *
import sys

from services.JsonParser import JsonParser


class ClientWrapper:
    room_list = {}

    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error as err:
        print("Socket failed with error:: " + err)

    def __init__(self, root):
        self.root = root
        self.chat_frame = ChatFrame
        self.server_address = ("localhost", 8080)
        self.client_socket.connect(self.server_address)
        threading.Thread(target=self.socket_data).start()

        root.title("Secret Chat")
        x = root.winfo_x()
        y = root.winfo_y()
        w = root.winfo_width()
        h = root.winfo_height()
        root.geometry("+%d+%d" % (x + 800, y + 300))

        root.configure(background="black")
        LoginFrame(root)
        # ChatFrame(root)

    def socket_data(self):
        size = 1024
        while True:
            data = self.client_socket.recv(size).decode("utf-8")
            json_data = JsonParser.parse(data)

            for json_element in json_data:
                final_json_data = json.loads(json_element)

                result = self.client_event_handler(final_json_data)

                if result is False:
                    self.client_socket.close()
                    print("Exit test")
                    self.root.destroy()
                    sys.exit()

    def client_event_handler(self, json_data):
        event = json_data["type"]
        del json_data["type"]
        switch = {
            "quit": {
                "class": self,
                "method": "close_connection",
                "params": json_data.values()
            },
            "server-message": {
                "class": self,
                "method": "server_message",
                "params": json_data.values()
            },
            "room-list": {
                "class": self,
                "method": "room_list",
                "params": json_data.values()
            },
            "receive-message": {
                "class": self.chat_frame,
                "method": "receive_message",
                "params": json_data.values()
            },
            "login-success": {
                "class": self,
                "method": "login_success",
                "params": json_data.values()
            }
        }

        current_event = switch[event]
        result = getattr(current_event["class"], current_event["method"])(*current_event["params"])

        return result

    def server_message(self, message):
        # TODO Implement Server message display in GUI view (Tkinter)
        print(message)

    def login_success(self, status):
        if status == "True":
            self.chat_frame = self.chat_frame(self.root)

    def room_list(self, data):

        room_list = json.loads(data)

        final_room_list = {}

        for k, v in room_list.items():
            try:
                final_room_list[int(k)] = v
            except (ValueError, TypeError):
                pass

        # print(final_room_list)
        self.room_list = final_room_list

    def close_connection(self):
        print("Connection closed by server")
        return False


class LoginFrame(ClientWrapper):
    def __init__(self, root):
        self.login_frame = Frame(root)
        self.login_frame.pack(side="top", fill="both", expand=True)  ## MAN SKAL ÅBENBART PACK, LORTE TKINTER
        self.login_frame.configure(background="black")

        ## Label Username
        Label(self.login_frame, text="USERNAME:", bg="black", fg="#20C20E").grid(row=1, column=0, sticky=W)

        ## Username
        self.username = Entry(self.login_frame, borderwidth=10, relief=FLAT, width=49, bg="black", fg="#20C20E",
                              insertbackground="#20C20E", insertwidth=5)
        self.username.grid(row=2, column=0, sticky=W)

        ## Label Password
        Label(self.login_frame, text="PASSWORD:", bg="black", fg="#20C20E").grid(row=3, column=0, sticky=W)

        ## Password
        self.password = Entry(self.login_frame, show="*", borderwidth=10, relief=FLAT, width=49, bg="black",
                              fg="#20C20E",
                              insertbackground="#20C20E", insertwidth=5)
        self.password.grid(row=4, column=0, sticky=W)

        ## Button
        Button(self.login_frame, text="Login", width=44, command=self.login, bg="#20C20E", fg="black").grid(row=5, column=0, sticky=W, pady=15)

    def login(self):
        username_text = self.username.get()
        password_text = self.password.get()
        json_credentials = '{ "type":"login", "username":"%s", "password":"%s" }' % (username_text, password_text)
        self.client_socket.send(bytes(json_credentials, "utf-8"))

        self.username.delete(0, END)
        self.password.delete(0, END)

        self.login_frame.destroy()


class ChatFrame(ClientWrapper):
    def __init__(self, root):
        self.chat_frame = Frame(root)
        self.message = StringVar()
        self.message.set("")
        scrollbar = Scrollbar(self.chat_frame)

        self.message_box = Listbox(self.chat_frame, bg="black", fg="#20C20E", font=20, height=25, width=55,
                                   highlightcolor="green", selectbackground="green",
                                   yscrollcommand=scrollbar.set)

        scrollbar.pack(side=RIGHT, fill=Y)
        self.message_box.pack(side=TOP)
        # self.message_box.pack()
        self.chat_frame.pack()

        message_field = Entry(self.chat_frame, borderwidth=10, relief=FLAT, width=79, bg="black", fg="#20C20E",
                              insertbackground="#20C20E", insertwidth=5,
                              textvariable=self.message)

        message_field.bind("<Return>", self.send_message)
        message_field.pack(ipady=10)
        # send_button = Button(self.chat_frame, height=5, width=5, text="Send", command=self.send_message)
        # send_button.pack(side=RIGHT)

    def send_message(self, event=None):
        message = self.message.get()
        self.message.set("")
        message_to_send = {
            "type": "send-message",
            "message": message
        }
        self.client_socket.send(JsonParser.prepare(message_to_send))

    def receive_message(self, message):
        self.message_box.insert(END, message)


def main():
    root = Tk()
    ClientWrapper(root)
    root.mainloop()


if __name__ == '__main__':
    main()
