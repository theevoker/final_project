import socket
import json
from threading import Thread
import time
import random


from param import *
import ssl
#from geopy.geocoders import Nominatim

class File: # this class is for writing / reading JSON file, later will be replaced by a DB class
    @staticmethod
    def read_file(file_name):
        with open(file_name, 'r') as file:
            return json.load(file)
    @staticmethod
    def write_file(file_name, change):
        with open(file_name, 'w') as file:
            file.write("{}")
        with open(file_name, 'w', encoding='utf-8') as file:
            json.dump(change, file, ensure_ascii=False, indent=4)

class Server(File): # arranges the library connections
    def __init__(self):
        Thread(target=self.ClientWebsite, args=()).start()
        self.active_libs = [] # which IDs are currently in use

        self.books = self.read_file("books.JSON") # which books are in which libraries, is a DICT

        temp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # sets up server
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(certfile='cert.pem', keyfile='key.pem')
        self.socket = context.wrap_socket(temp_socket, server_side=True)
        self.socket.bind((IP, PORT)) # "
        self.socket.listen() # "
        print("ran")
        while True: # library connections
            soc, b = self.socket.accept()
            Thread(target=self.first_connection, args=(soc,)).start() # starts new thread for each library

    def get_new_ID(self, soc): # gets a new ID that's not used for the new library
        while True:
            rand = str(random.randint(1111, 9999))
            if not rand in self.read_file("libraries.JSON").keys():
                soc.send(rand.encode())
                break
        return rand

    def first_connection(self, soc): # sets up a new library that just connected
        print(soc, "    | this is the socket in question")
        soc.send("login".encode()) # asks for ID
        ans = soc.recv(1024).decode() # response is either ID or "new lib", which means that it need a new ID
        analyze = ans.split("%")
        ans = analyze[1]
        location = analyze[0]
        print(ans, "    | this is the answer for the login question")
        if ans == "new lib":
            num = self.get_new_ID(soc) # gets a new ID for the library
            self.active_libs.append(num) # adds number to both self.numbers and self.active_numbers
            print(self.active_libs, "     | active numbers")
        else: # if it's a number
            if ans in self.active_libs: # if so, the library can't use this ID
                num = self.get_new_ID(soc) #" "
                print(num, "     | active numbers")
            else: # meaning ID is open
                num = ans # sets up this libraries number
                soc.send("True".encode()) # this ensures the library that it's fine
                self.active_libs.append(num) # "
                print(self.active_libs, "     | active numbers")
        print(soc.recv(1024).decode(), "    | checks if everything is correct")
        self.book_update((soc, num)) # loads the new library's books
        library_locations = self.read_file("locations.JSON")  # loads the locations
        library_locations[num] = (location,)
        self.write_file("locations.JSON", library_locations)
        while True:
            if self.library_connection((soc, num)): # runs main function
                break
            time.sleep(5) # waits, because my computer is slow af and I don't want it to die

    def book_update(self, lib): # load a library's books into JSON file
        print("book update activated")

        lib[0].send(f"BOOKS".encode()) # requests for books
        books = lib[0].recv(1024).decode()[6:] # receives books
        print(books, "    | list of books")

        library_list = self.read_file("libraries.JSON") # a bunch of nonsense

        library_list[lib[1]] = tuple(books.split("%"))

        self.write_file("libraries.JSON", library_list) # loads books into file

        for book in library_list[lib[1]]: # this function writes which books are in which library after the update
            if self.books.get(book) is not None:
                if not lib[1] in self.books[book]:
                    self.books[book].append(lib[1])
            else:
                self.books[book] = [lib[1], ]

        for book in self.books.keys(): # this check whether everything is correct
            if lib in self.books[book] and book not in library_list[lib[1]]:
                self.books[book].remove(lib)

        self.write_file("books.JSON", self.books)


    def library_connection(self, lib): # this function holds everything together
        # lib is made out of a tuple, (soc, num)
        try:
            print(lib[0])
            lib[0].send(f"REPORT".encode()) # asks for a state report, whether the books changed or not
            ans = lib[0].recv(1024).decode() # ans is either CHANGED or NO CHANGED, plus the library's location
            print(ans,"    | what to do")

            library_names = self.read_file("libraryNames.JSON") # loads the names
            library_names[lib[1]] = (ans.split("%")[0],)
            self.write_file("libraryNames.JSON", library_names)

            if ans.split("%")[-1] == "CHANGED":
                self.book_update(lib)
        except OSError: # exception for when the library crashes/ disconnects
            print("closed")
            lib[0].close()
            self.active_libs.remove(lib[1])

            #removing it
            libraries_list = self.read_file("libraries.json")
            libraries_list.pop(lib[1], None)
            self.write_file("libraries.JSON", libraries_list)
            return True

            '''from here on out it's a flask server'''

    def ClientWebsite(self):
        from flask import Flask, request, render_template

        app = Flask(__name__)

        @app.route('/')
        def index():
            return render_template("index.html", libraries = list(self.read_file("libraries.JSON").keys()))

        @app.route('/library/', methods=['GET'])
        def get_library():
            library = request.args["library"]
            try:
                books = self.read_file("libraries.JSON")[''.join(char for char in library if char.isdigit())]
            except KeyError:
                books = ["library not found"]
            print(library)
            print(books)
            return render_template("library.html", books = books, library = library)
        @app.route('/search/', methods=['GET'])
        def get_book():
            book = request.args["book"]
            print(book)
            try:
                libraries = self.search(book)
            except KeyError:
                libraries = ["book not found"]
            return render_template("search.html", libraries=libraries, book=book)

        app.run(ssl_context=('cert.pem', 'key.pem'), host=IP, port=WEBSITE_PORT)

    def search(self, book):
        #locations = self.read_file("locations.JSON")
        #geolocator = Nominatim(user_agent="library_useragent")
        result = []
        for lib in self.read_file("books.JSON")[book]:
            if lib in self.active_libs:
                #result.insert(0, geolocator.reverse(locations[lib]))
                result.insert(0, lib)
            else:
                #result.append("not online " + str(geolocator.reverse(locations[lib])))
                result.append("not online " +  lib)
        #print([geolocator.reverse(locations[lib]) for lib in self.read_file("books.JSON")[book]])
        return result


