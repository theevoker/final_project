import socket
from threading import Thread
import time

class File:
    @staticmethod
    def read_file(file_name):
        with open(file_name, 'r') as file:
            return dict([(line.split("%")[0], tuple(line.split("%"))[1::]) for line in file.read().split("\n")])
    @staticmethod
    def write_file(file_name, change):
        with open(file_name, 'w') as file:
            file.write("\n".join([f"{item[0]}%{"%".join(item[-1])}" for item in change.items()]))

class Library(File):
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(("", 1111))
        self.socket.listen()
        print("ran")
        while True:
            soc, b = self.socket.accept()
            Thread(target=self.first_connection, args=(soc,)).start()
    def first_connection(self, soc):
        self.book_update(soc)
        while True:
            self.check_connection(soc)
            time.sleep(5)

    def book_update(self, soc):
        print("check")
        soc.send("0.0.1".encode())
        books = soc.recv(1024).decode()
        print(books)
        library_list = self.read_file("libraries")
        library_list[soc] = tuple(books.split("%"))
        print(library_list)
        self.write_file("libraries", library_list)
    def check_connection(self, soc):
        try:
            soc.send("0.0.0".encode())
            ans = soc.recv(1024).decode()
            library_locations = self.read_file("library_locations")
            library_locations[soc] = ans.split("%")[0]
            print("check + " + ans.split("%")[-1])
            self.write_file("library_locations", library_locations)
            if ans.split("%")[-1] == "0.1.1":
                self.book_update(soc)
        except:
            soc.close()

class Client(File):
    def search(self, book):
        results = []
        library_locations = self.read_file("library_locations")
        libraries = self.read_file("libraries")
        for library in library_locations.keys():
            if book in libraries[library]:
                results.append(library_locations[library][0])
        print(results)
        return tuple(results)