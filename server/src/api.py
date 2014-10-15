from flask import Flask

app = Flask(__name__)

@app.route('/')
def root():
    return 'API is running!'

@app.route('/data1')
def data1():
    return app.send_static_file('data1.json')

if __name__ == '__main__':
    app.run()
