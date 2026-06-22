import os
import logging
import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# Configuração de Logs para o Render
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'revival_master_secret_key_999')

# Configuração do Banco de Dados SQLite Local
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'users.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ==================== MODELO DA DATABASE ====================
class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    nick = db.Column(db.String(80), default='Recruta')
    nivel = db.Column(db.Integer, default=1)
    ouro = db.Column(db.Integer, default=0)
    diamantes = db.Column(db.Integer, default=0)
    cargo = db.Column(db.String(30), default='Jogador') # Jogador ou Admin
    banido = db.Column(db.Boolean, default=False)

# Criar as tabelas e o administrador inicial caso não existam
with app.app_context():
    db.create_all()
    # Verifica se o admin mestre já existe para não duplicar
    if not Player.query.filter_by(username='admin').first():
        senha_cripto = generate_password_hash('123456')
        admin_mestre = Player(
            username='admin',
            password=senha_cripto,
            nick='Cientista Dev',
            nivel=99,
            ouro=999999,
            diamantes=999999,
            cargo='Admin'
        )
        db.session.add(admin_mestre)
        db.session.commit()
        logging.info("Database SQLite inicializada e Administrador padrão criado com sucesso!")

# ==================== ROTAS DO SERVIDOR ====================

@app.route('/')
def index():
    try:
        return send_from_directory(BASE_DIR, 'index.html')
    except Exception as e:
        logging.error(f"Erro ao carregar index.html: {e}")
        return "Erro interno ao carregar a interface de login.", 500

@app.route('/api/v1/auth/login', methods=['POST'])
def player_login():
    data = request.get_json() or {}
    username_input = data.get('email', '').strip()
    password_input = data.get('password', '')

    if not username_input or not password_input:
        return jsonify({"success": False, "msg": "Preencha todos os campos."}), 400

    try:
        # Busca o usuário na database SQLite local
        player = Player.query.filter_by(username=username_input).first()

        if not player:
            return jsonify({"success": False, "msg": "Conta não encontrada no servidor."}), 404

        # Valida a senha usando hash seguro
        if not check_password_hash(player.password, password_input):
            return jsonify({"success": False, "msg": "Senha incorreta."}), 401

        if player.banido:
            return jsonify({"success": False, "msg": "Esta conta está suspensa permanentemente."}), 403

        # Retorna o resultado com base no cargo da conta
        return jsonify({
            "success": True,
            "cargo": player.cargo,
            "profile": {
                "nick": player.nick,
                "nivel": player.nivel,
                "ouro": player.ouro,
                "diamantes": player.diamantes
            }
        }), 200

    except Exception as e:
        logging.error(f"Erro no processamento do login: {e}")
        return jsonify({"success": False, "msg": "Erro interno no gerenciador de login."}), 500

@app.errorhandler(404)
def page_not_found(e):
    return send_from_directory(BASE_DIR, 'index.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
                            
