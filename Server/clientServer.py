from flask import Flask, request, render_template
from methods import Client

app = Flask(__name__)
client = Client()


@app.route('/')
def index():
    return render_template("index.html")

@app.route('/search/', methods=['GET'])
def get():
    book = request.args["book"]
    print(book)
    libraries = ", ".join(client.search(book))
    return render_template("search.html", libraries = libraries)

if __name__ == '__main__':
    app.run()