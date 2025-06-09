import os
from src.app import setup_app

if __name__ == '__main__':
    # Set environment variables
    os.environ['FLASK_APP'] = 'wsgi:app'
    os.environ['FLASK_DEBUG'] = '1'
    
    # Create and run the app
    socketio, app = setup_app()
    
    # Run the app
    if socketio:
        socketio.run(app, host='0.0.0.0', port=5000, debug=True)
    else:
        app.run(host='0.0.0.0', port=5000, debug=True)
