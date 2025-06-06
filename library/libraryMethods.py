import socket
from threading import Thread
import json
import os

from functools import wraps
from flask import Flask, render_template, request, redirect, make_response
from requests import get

from param import *
import ssl
import hashlib


class Library:
    def __init__(self):
        self.name = "defaultName"
        self.ID = ""
        self.file = "file.JSON"
        self.books = []
        self.book_changed = False
        Thread(target=self.serv_conn).start() # connection with server


    #general methods
    @staticmethod
    def get_location(): # gets current location
        resp = get(f"https://geolocation-db.com/json/{get('https://api.ipify.org').content.decode('utf8')}&position=true").json()
        return str(f"{resp['latitude']}, {resp['longitude']}")

    @staticmethod
    def read_file(file_name): # guess what
        with open(file_name, 'r', encoding='utf-8') as file:
            return json.load(file)

    @staticmethod # guess what
    def write_file(file_name, change):
        with open(file_name, 'w', encoding='utf-8') as file:
            file.write("{}")
        with open(file_name, 'w', encoding='utf-8') as file:
            json.dump(change, file, ensure_ascii=False, indent=4)
    #server methods
    def set_new_lib(self, con): # guess what
        location = self.get_location()
        print("new lib")
        con.send(f'{location}%new lib'.encode()) # asks for new ID
        self.ID = con.recv(1024).decode() # receives ID
        with open('file.JSON', 'x+') as file: # writes it down
            file.write('{\n    "' + str(self.ID) + '": [],\n' + '"name": "defaultName"\n}')
        print(self.ID)

    def lib_exist(self, con): # guess what
        libraries = json.load(open(self.file, 'r', encoding='utf-8'))
        con.send(f"{self.name}%{list(libraries.keys())[0]}".encode()) # sends ID
        ans = con.recv(1024).decode() # receives either the OK or a new ID
        print(ans)
        if ans == "True": # if got the ID
            self.ID = list(libraries.keys())[0] # sets ID
            self.name = self.read_file("file.JSON")["name"]
        else:
            self.ID = ans # sets given ID as ID
            self.file = self.ID + ".json"
            with open(self.file, 'x+') as file:
                file.write('{\n    "' + "books" + '": [],\n' + '"name": "defaultName"\n}')
        print(self.ID)


    def serv_conn(self): # arranges connection with server
        start = True
        try:
            temp_con = socket.socket()# connects to server
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            con = context.wrap_socket(temp_con, server_hostname=IP)
            con.connect((IP, PORT))

            print(con.recv(1024).decode()) # the login thing
            if not os.path.isfile(self.file):
                self.set_new_lib(con)
            else:
                self.lib_exist(con)

            con.send("worked".encode())

        except ConnectionRefusedError:
            print("no connection")
            self.name = self.read_file("file.JSON")["name"]
            self.ID = list(self.read_file("file.JSON").keys())[0]
            start = False




        self.books = list(json.load(open(self.file, 'r', encoding='utf-8')).values())[0]



        Thread(target=self.start_screen).start()
        while start: # yay loop wooooooo
            quarry = con.recv(1024).decode() # server asks for something
            print(quarry)
            if quarry == "REPORT": # if so, the response is the name + whether the books changed or not

                if not self.book_changed:
                    print(f"{self.name}%NO CHANGE")
                    con.send(f"{self.name}%NO CHANGE".encode())
                else:
                    print(f"{self.name}%CHANGED")
                    con.send(f"{self.name}%CHANGED".encode())
                    self.book_changed = False
            elif quarry == "BOOKS": # sends books
                print("%".join(self.books))
                con.send(("books:"+"%".join(self.books)).encode())
    #physical methods
    def add_book(self, book): # adds book to file
        self.books.append(book)
        self.write_file(self.file, {self.ID:self.books, "name":self.name})
        self.book_changed = True


    def remove_book(self, book): # you won't believe what this function does
        self.books.remove(book)
        self.write_file(self.file, {self.ID:self.books,"name":self.name})
        self.book_changed = True

    def change_name(self, name):
        self.name = name
        self.write_file(self.file, {self.ID: self.books, "name": self.name})

    @staticmethod
    def change_pass(password):
        with open('code', 'w') as file:
            file.write(hashlib.sha1(password.encode()).hexdigest())


    @staticmethod
    def auth_required(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            auth = request.authorization
            if auth and auth.username == "" and hashlib.sha1(auth.password.encode()).hexdigest() == open("code", 'r').read():
                return f(*args, **kwargs)
            return make_response(redirect("/"), 401, {'WWW-Authenticate': 'Basic realm="Login required"'})

        return decorated


    def create_app(self):


        app = Flask(__name__)

        @app.route('/')
        def index():
            return render_template("index.html", name= self.name, books= self.books)

        @app.route('/developer/')
        @self.auth_required
        def developer():
            return render_template("developer.html")

        @app.route('/name/', methods=['GET'])
        @self.auth_required
        def change_name():
            self.change_name(request.args["name"])
            return redirect("/")

        @app.route('/pass/', methods=['GET'])
        @self.auth_required
        def change_pass():
            self.change_pass(request.args["pass"])
            return redirect("/")


        @app.route('/add_book/', methods=['GET'])
        def add_book():
            book = request.args["book"]
            print(book)
            self.add_book(book)
            return render_template("result.html", result="Book added successfully")

        @app.route('/remove_book/', methods=['GET'])
        def remove_book():
            book = request.args["book"]
            print(book)
            try:
                self.remove_book(book)
            except ValueError:
                return render_template("result.html", result="Book not found")
            else:
                return render_template("result.html", result="Book removed")

        return app

    def start_screen(self):
        self.create_app().run(port=int(self.ID))