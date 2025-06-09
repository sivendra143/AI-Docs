from flask import Flask
from src.main.routes import main_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Development')

    # Initialize extensions
    from src.extensions import db, login_manager
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'main.index'

    # Register blueprints
    app.register_blueprint(main_bp)
    from src.api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
