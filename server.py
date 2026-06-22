import os
from flask import Flask, request, jsonify, render_template_string
from flask_sqlalchemy import SQLAlchemy
import pymysql

app = Flask(__name__)

# Configuração automática do Banco de Dados via Variável de Ambiente (Render) ou Local
DATABASE_URL = os.environ.get('DATABASE_URL', 'mysql+pymysql://revival_user:123456@localhost:3306/revival_db')
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Tabela de Contas dos Jogadores (Padrão Free Fire 2018/2019)
class User(db.Model):
    __tablename__ = 'accounts'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    diamonds = db.Column(db.Integer, default=1000)
    gold = db.Column(db.Integer, default=5000)

# Rota Principal - Carrega o teu Painel Web HTML automaticamente
@app.route('/')
def index():
    return render_template_string(get_html_content())

# Rotas de Login Unificadas (Resolve o erro "Not Found" do APK e do HTML)
@app.route('/api/login', methods=['POST', 'GET'])
@app.route('/login.php', methods=['POST', 'GET'])
@app.route('/login', methods=['POST', 'GET'])
def login():
    # Verifica se os dados vieram por JSON (HTML moderno) ou Form/URL (APK Antigo)
    if request.is_json:
        data = request.get_json() or {}
    else:
        data = request.form if request.form else request.args

    # Tenta ler as variações de parâmetros comuns em APKs modificados
    username = data.get('username') or data.get('user') or data.get('account')
    password = data.get('password') or data.get('pass') or data.get('pwd')
    
    if not username or not password:
        return jsonify({"status": "fail", "message": "Campos obrigatórios em falta."}), 400
        
    user = User.query.filter_by(username=username).first()
    
    if user and user.password == password:
        # Retorno completo com a estrutura que o APK e o Painel precisam
        return jsonify({
            "status": "success",
            "message": "Login efetuado com sucesso!",
            "user": {
                "id": user.id,
                "username": user.username,
                "diamonds": user.diamonds,
                "gold": user.gold
            }
        }), 200
        
    return jsonify({"status": "fail", "message": "Usuário ou senha incorretos."}), 401

# Rota de Registo de Contas (Via Painel ou APK)
@app.route('/api/register', methods=['POST', 'GET'])
@app.route('/register.php', methods=['POST', 'GET'])
def register():
    if request.is_json:
        data = request.get_json() or {}
    else:
        data = request.form if request.form else request.args

    username = data.get('username') or data.get('user')
    password = data.get('password') or data.get('pass')
    
    if not username or not password:
        return jsonify({"status": "fail", "message": "Campos obrigatórios em falta."}), 400
        
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({"status": "fail", "message": "Este usuário já existe."}), 400
        
    new_user = User(username=username, password=password)
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({"status": "success", "message": "Conta criada com sucesso!"}), 201

# Interface HTML integrada diretamente no Backend
def get_html_content():
    return """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Revival FF - Painel de Acesso</title>
        <style>
            body {
                background-color: #0d1117;
                color: #c9d1d9;
                font-family: 'Segoe UI', Arial, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
            }
            .login-card {
                background: #161b22;
                padding: 30px;
                border-radius: 10px;
                border: 1px solid #30363d;
                box-shadow: 0 8px 24px rgba(0,0,0,0.5);
                width: 100%;
                max-width: 350px;
                text-align: center;
            }
            h2 { color: #58a6ff; margin-bottom: 20px; font-size: 24px; text-transform: uppercase; }
            input {
                width: 90%;
                padding: 10px;
                margin: 10px 0;
                background: #0d1117;
                border: 1px solid #30363d;
                border-radius: 6px;
                color: #fff;
            }
            input:focus { border-color: #58a6ff; outline: none; }
            button {
                width: 96%;
                padding: 12px;
                background: #238636;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                cursor: pointer;
                margin-top: 15px;
            }
            button:hover { background: #2ea44f; }
            #response { margin-top: 15px; font-size: 14px; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="login-card">
            <h2>REVIVAL FF LOGIN</h2>
            <input type="text" id="user" placeholder="Nome de Usuário">
            <input type="password" id="pass" placeholder="Sua Senha">
            <button onclick="enviarLogin()">ENTRAR NO SERVIDOR</button>
            <div id="response"></div>
        </div>

        <script>
            function enviarLogin() {
                const u = document.getElementById('user').value;
                const p = document.getElementById('pass').value;
                const respDiv = document.getElementById('response');
                
                respDiv.innerText = "A conectar...";
                respDiv.style.color = "#8b949e";

                fetch('/api/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username: u, password: p })
                })
                .then(res => res.json())
                .then(data => {
                    if(data.status === "success") {
                        respDiv.innerText = `Sucesso! Dimas: ${data.user.diamonds} | Ouro: ${data.user.gold}`;
                        respDiv.style.color = "#2ea44f";
                    } else {
                        respDiv.innerText = data.message;
                        respDiv.style.color = "#f85149";
                    }
                })
                .catch(err => {
                    respDiv.innerText = "Erro ao conectar com o Servidor/Zrok!";
                    respDiv.style.color = "#f85149";
                });
            }
        </script>
    </body>
    </html>
    """

if __name__ == '__main__':
    # Cria as tabelas estruturadas no banco do Termux via Zrok automaticamente
    try:
        with app.app_context():
            db.create_all()
    except Exception as e:
        print(f"Aviso ao inicializar tabelas: {e}")
        
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
    
