import socket
from threading import Thread
import json
import os
from requests import get
from param import *


class Library:
    def __init__(self):
        self.ID = ""
        self.books = []
        self.book_changed = False
        Thread(target=self.run).start() # connection with server
        Thread(target=self.serv_conn).start() # add and removes books


    #general methods
    @staticmethod
    def get_location(): # gets current location
        resp = get(f"https://geolocation-db.com/json/{get('https://api.ipify.org').content.decode('utf8')}&position=true").json()
        return str(f"{resp['latitude']}, {resp['longitude']}")

    @staticmethod
    def read_file(file_name): # guess what
        with open(file_name, 'r') as file:
            return json.load(file)

    @staticmethod # guess what
    def write_file(file_name, change):
        with open(file_name, 'w') as file:
            file.write("{}")
        with open(file_name, 'w', encoding='utf-8') as file:
            json.dump(change, file, ensure_ascii=False, indent=4)
    #server methods
    def set_new_lib(self, con): # guess what
        print("new lib")
        con.send('new lib'.encode()) # asks for new ID
        self.ID = con.recv(1024).decode() # receives ID
        with open('file.JSON', 'x+') as file: # writes it down
            file.write('{\n    "' + str(self.ID) + '": []\n}')
        print(self.ID)

    def lib_exist(self, con): # guess what
        libraries = json.load(open("file.JSON", 'r'))
        con.send(list(libraries.keys())[0].encode()) # sends ID
        ans = con.recv(1024).decode() # receives either the OK or a new ID
        print(ans)
        if ans == "True": # if got the ID
            self.ID = list(libraries.keys())[0] # sets ID
        else:
            self.ID = ans # sets given ID as ID
        print(self.ID)


    def serv_conn(self): # arranges connection with server
        self.books = list(json.load(open("file.JSON", 'r')).values())[0] # lists books in library
        location = self.get_location() # gets location
        con = socket.socket()# connects to server
        con.connect((IP, PORT))

        print(con.recv(1024).decode()) # the login thing
        if not os.path.isfile('file.JSON'):
            self.set_new_lib(con)
        else:
            self.lib_exist(con)

        con.send("worked".encode())
        while True: # yay loop wooooooo
            quarry = con.recv(1024).decode() # server asks for something
            print(quarry)
            if quarry == "REPORT": # if so, the response is the location + whether the books changed or not

                if not self.book_changed:
                    print(f"{location}%NO CHANGE")
                    con.send(f"{location}%NO CHANGE".encode())
                else:
                    print(f"{location}%CHANGED")
                    con.send(f"{location}%CHANGED".encode())
                    self.book_changed = False
            elif quarry == "BOOKS": # sends books
                print("%".join(self.books))
                con.send("%".join(self.books).encode())
    #physical methods
    def add_book(self, book): # adds book to file
        self.books.append(book)
        self.write_file("file.JSON", self.books)
        self.book_changed = True


    def remove_book(self, book): # you won't believe what this function does
        self.books.remove(book)
        self.write_file("file.JSON", self.books)
        self.book_changed = True

    def run(self): # this is the physical function, which doesn't matter
        while True:
            print("what do you want to do? (1 for adding book anything else for lending book)")
            if input() == "1":
                self.add_book(input())
            else:
                try:
                    self.remove_book(input())
                except ValueError:
                    print("book does not exist")