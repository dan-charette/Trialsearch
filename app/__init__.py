from flask import Flask


def create_app(config=None):
    app = Flask(__name__)
    app.config.from_object('app.config')
    if config:
        app.config.update(config)

    from app.routes.search import search_bp
    app.register_blueprint(search_bp)

    return app
