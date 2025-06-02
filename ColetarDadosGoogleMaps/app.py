from flask import Flask
from coletardadosgooglemaps.routes import main_bp # Importa o Blueprint das rotas

def create_app():
    """Cria e configura a instância da aplicação Flask."""
    app = Flask(__name__)

    # Registra o Blueprint na aplicação
    app.register_blueprint(main_bp)

    return app

if __name__ == '__main__':
    # Cria a aplicação
    app = create_app()
    # Para rodar em ambiente de desenvolvimento
    app.run(debug=True)
    # Para rodar em produção, use: app.run(host='0.0.0.0', port=5000)