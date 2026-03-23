
from flask import Flask, request, jsonify
import random

app = Flask(__name__)

@app.route('/pay', methods=['POST'])
def pay():
    status = "approved" if random.random() > 0.2 else "declined"
    return jsonify({"status": status})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)

