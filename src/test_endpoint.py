from flask import Flask, request, jsonify, make_response
from flask_cors import CORS, cross_origin

app = Flask(__name__)

# Configure CORS to allow all origins and handle preflight requests
cors = CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

@app.route('/test', methods=['GET'])
def test():
    return jsonify({"message": "Test endpoint is working!"})

@app.route('/api/ask', methods=['POST', 'OPTIONS'])
@cross_origin()
def ask():
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
        
    data = request.json
    question = data.get('question', '')
    print(f"Received question: {question}")
    
    response = jsonify({
        "answer": f"You asked: {question}\nThis is a test response from the server.",
        "suggestions": ["Tell me more", "How does this work?"]
    })
    
    # Add CORS headers to the response
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

if __name__ == '__main__':
    app.run(port=5000, debug=True)
