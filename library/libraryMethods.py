import socket
from threading import Thread

class Library:
    def __init__(self):
        self.books = self.read_file("file")
        self.book_changed = False
        Thread(target=self.run).start()
        Thread(target=self.serv_conn).start()


    #general methods
    @staticmethod
    def get_location():
        print("whoa look i'm getting my location")
        return "12"

    @staticmethod
    def write_file(file_name, change):
        with open(file_name, 'w') as file:
            file.write("#".join(change))
    @staticmethod
    def read_file(file_name):
        with open(file_name, 'r') as file:
            return file.read().split("#")
    #server methods
    def serv_conn(self):
        books = self.books
        location = self.get_location()
        con = socket.socket()
        con.connect(("127.0.0.1", 1111))
        while True:
            quarry = con.recv(1024).decode()
            if quarry == "0.0.0":
                if not self.book_changed:
                    print(f"{location}%0.1.0")
                    con.send(f"{location}%0.1.0".encode())
                else:
                    print(f"{location}%0.1.1")
                    con.send(f"{location}%0.1.1".encode())
                    self.book_changed = False
            elif quarry == "0.0.1":
                print("%".join(books))
                con.send("%".join(books).encode())

    #physical methods
    def add_book(self, book):
        books = self.read_file("file")
        self.books.append(book)
        books.append(book)
        self.write_file("file", books)
        self.book_changed = True


    def remove_book(self, book):
        books = self.read_file("file")
        books.remove(book)
        self.books.remove(book)
        self.write_file("file", books)
        self.book_changed = True

    def run(self):
        while True:
            print("what do you want to do? (1 for adding book anything else for lending book)")
            if input() == "1":
                self.add_book(input())
            else:
                self.remove_book(input())