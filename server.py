import os
import logging
from flask import Flask, request, jsonify, render_template_string
from flask_sqlalchemy import SQLAlchemy
import pymysql

# --- CONFIGURAÇÃO INICIAL ---
logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

# Conexão com o Banco de Dados
DATABASE_URL = os.environ.get('DATABASE_URL', 'mysql+pymysql://revival_user:123456@localhost:3306/revival_db')
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Modelo de Conta
class User(db.Model):
    __tablename__ = 'accounts'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(db.String(64), nullable=False)
    diamonds = db.Column(db.Integer, default=5000)
    gold = db.Column(db.Integer, default=10000)

# --- ROTAS DE INTERCEPTAÇÃO E LOGIN ---
@app.route('/<path:url>', methods=['POST', 'GET'])
def main_handler(url):
    # Rota de Login (OAuth/SDK do Jogo)
    if 'dialog/oauth' in url:
        return render_template_string(get_auth_html(request.args.get('redirect_uri'), request.args.get('state')))
    
    # Processamento de Submissão
    if 'auth_login_submit' in url:
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user and user.password == request.form.get('pass'):
            redirect = f"{request.form.get('redirect_uri')}#access_token=REVIVAL_TOKEN_OK&state={request.form.get('state')}"
            return jsonify({"status": "success", "redirect": redirect})
        return jsonify({"status": "error"}), 401
    
    return jsonify({"status": "success", "version": "1.39"}), 200

# --- ROTAS DE API (JOGO) ---
@app.route('/api/profile', methods=['GET'])
def get_profile():
    user = User.query.filter_by(username=request.args.get('username')).first()
    return jsonify({"diamonds": user.diamonds, "gold": user.gold}) if user else jsonify({"error": "not found"}), 404

@app.route('/api/inventory', methods=['GET'])
def get_inventory():
    return jsonify({"items": [{"id": 1001, "name": "Skin_Padrao"}]})

@app.route('/api/ranking', methods=['GET'])
def get_ranking():
    top = User.query.order_by(User.diamonds.desc()).limit(10).all()
    return jsonify([{"user": u.username, "score": u.diamonds} for u in top])

# --- HTML PREMIUM (INTERFACE FINAL) ---
def get_auth_html(redir, state):
    return f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ background: #000; color: #fff; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
            .auth-card {{ background: #111; border: 1px solid #222; padding: 30px; border-radius: 12px; width: 320px; text-align: center; }}
            .title {{ color: #ff5500; font-size: 20px; font-weight: 900; margin-bottom: 20px; text-transform: uppercase; }}
            input {{ width: 100%; padding: 12px; margin: 8px 0; background: #161616; border: 1px solid #262626; border-radius: 8px; color: #fff; }}
            button {{ width: 100%; padding: 12px; background: #ff5500; border: none; border-radius: 8px; color: white; font-weight: bold; cursor: pointer; }}
            #msg {{ margin-top: 15px; font-size: 12px; color: #ff5500; }}
        </style>
    </head>
    <body>
        <div class="auth-card">
            <div class="title">Revival Private Server</div>
            <input type="text" id="user" placeholder="Usuário">
            <input type="password" id="pass" placeholder="Senha">
            <button onclick="login()">Entrar</button>
            <div id="msg"></div>
        </div>
        <script>
            function login() {{
                const u = document.getElementById('user').value;
                const p = document.getElementById('pass').value;
                fetch('/auth_login_submit', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/x-www-form-urlencoded'}},
                    body: 'username='+u+'&pass='+p+'&redirect_uri={redir}&state={state}'
                }})
                .then(r => r.json())
                .then(d => {{
                    if(d.status === "success") window.location.href = d.redirect;
                    else document.getElementById('msg').innerText = "Login não teve sucesso.";
                }});
            }}
        </script>
    </body>
    </html>
    """

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000)
    
