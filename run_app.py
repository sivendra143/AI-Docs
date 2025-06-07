import os
from src.app import setup_app

if __name__ == '__main__':
    # Set environment variables
    os.environ['FLASK_APP'] = 'wsgi:app'
    os.environ['FLASK_DEBUG'] = '1'
    
    # Create and run the app
    app = setup_app()
    
    # Run the app
    if hasattr(app, 'run'):
        app.run(host='0.0.0.0', port=5001, debug=True)
    else:
        print("Error: Could not start the application")
