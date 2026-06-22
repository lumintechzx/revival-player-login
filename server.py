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

# Rota Principal - Carrega o Painel Web HTML automaticamente
@app.route('/')
def index():
    return render_template_string(get_html_content())

# 🔥 ROTA UNIVERSAL COM INTERCEPTADOR DE FLUXO OAUTH/SDK
@app.route('/<path:url>', methods=['POST', 'GET'])
@app.route('/api/login', methods=['POST', 'GET'])
@app.route('/login.php', methods=['POST', 'GET'])
def login_universal(url=None):
    print(f"[REQUISIÇÃO DETECTADA]: Rota acessada -> /{url}")

    # 1. Se o APK estiver a chamar o diálogo de autenticação (OAuth)
    if url and 'dialog/oauth' in url:
        redirect_uri = request.args.get('redirect_uri', 'fbconnect://success')
        state = request.args.get('state', '')
        
        # Apresenta a interface de autenticação do servidor para o jogador dentro do APK
        return render_template_string(get_auth_page_html(redirect_uri, state))

    # 2. Processamento do formulário de autenticação customizado
    if url and 'auth_login_submit' in url:
        if request.is_json:
            data = request.get_json() or {}
        else:
            data = request.form if request.form else request.args

        username = data.get('username') or data.get('user')
        password = data.get('pass') or data.get('password')
        redirect_uri = data.get('redirect_uri', 'fbconnect://success')
        state = data.get('state', '')

        if not username or not password:
            return "Erro: Usuário e senha obrigatórios.", 400

        # Verifica ou cria o utilizador automaticamente no banco de dados
        user = User.query.filter_by(username=username).first()
        if not user:
            try:
                user = User(username=username, password=password)
                db.session.add(user)
                db.session.commit()
            except Exception as e:
                print(f"Erro ao criar conta: {e}")

        # Gera o formato de retorno com o token que o cliente do jogo necessita
        token_auth = "REVIVAL_TOKEN_VALID_2018_EMULATION"
        success_url = f"{redirect_uri}#access_token={token_auth}&expires_in=86400&state={state}"
        
        # Redireciona o navegador interno do APK para fechar a WebView e validar o login
        return render_template_string(f"""
            <script>
                window.location.href = "{success_url}";
            </script>
        """)

    # 3. Retorno padrão para checagens automáticas ou rotas genéricas
    if request.is_json:
        data = request.get_json() or {}
    else:
        data = request.form if request.form else request.args

    username = data.get('username') or data.get('user') or data.get('account')
    password = data.get('password') or data.get('pass')

    if not username or not password:
        return jsonify({
            "status": "success", 
            "message": "Servidor Revival Online", 
            "version": "1.39"
        }), 200
        
    user = User.query.filter_by(username=username).first()
    if user and user.password == password:
        return jsonify({"status": "success", "error": 0, "username": user.username}), 200

    return jsonify({"status": "fail", "error": 1, "message": "Dados incorretos."}), 401

# Manual Register Rota (Caso queiras usar pelo Painel)
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

# Interface de Login do Painel Web HTML
def get_html_content():
    return """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Revival FF - Painel de Acesso</title>
        <style>
            body { background-color: #0d1117; color: #c9d1d9; font-family: 'Segoe UI', Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
            .login-card { background: #161b22; padding: 30px; border-radius: 10px; border: 1px solid #30363d; box-shadow: 0 8px 24px rgba(0,0,0,0.5); width: 100%; max-width: 350px; text-align: center; }
            h2 { color: #58a6ff; margin-bottom: 20px; font-size: 24px; text-transform: uppercase; }
            input { width: 90%; padding: 10px; margin: 10px 0; background: #0d1117; border: 1px solid #30363d; border-radius: 6px; color: #fff; }
            input:focus { border-color: #58a6ff; outline: none; }
            button { width: 96%; padding: 12px; background: #238636; color: white; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; margin-top: 15px; }
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
                        respDiv.innerText = `Sucesso! Dimas: ${data.diamonds} | Ouro: ${data.gold}`;
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

# Interface de Autenticação Interna Emulada (Abre dentro da WebView do Jogo)
def get_auth_page_html(redirect_uri, state):
    return f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Revival Network - Autenticação</title>
        <style>
            body {{ background-color: #0d1117; color: #c9d1d9; font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
            .auth-box {{ background: #161b22; padding: 25px; border-radius: 8px; border: 1px solid #30363d; width: 100%; max-width: 300px; text-align: center; }}
            .title {{ color: #58a6ff; font-size: 22px; font-weight: bold; margin-bottom: 20px; text-transform: uppercase; }}
            input {{ width: 90%; padding: 10px; margin: 8px 0; background: #0d1117; border: 1px solid #30363d; border-radius: 6px; color: #fff; }}
            button {{ width: 97%; padding: 12px; background: #238636; color: white; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; margin-top: 15px; }}
            button:hover {{ background: #2ea44f; }}
            .info {{ margin-top: 15px; font-size: 11px; color: #8b949e; }}
        </style>
    </head>
    <body>
        <div class="auth-box">
            <div class="title">REVIVAL AUTH</div>
            <form action="/auth_login_submit" method="POST">
                <input type="hidden" name="redirect_uri" value="{redirect_uri}">
                <input type="hidden" name="state" value="{state}">
                <input type="text" name="username" placeholder="Nome de Utilizador ou Email" required>
                <input type="password" name="pass" placeholder="Palavra-passe" required>
                <button type="submit">AUTORIZAR E ENTRAR</button>
            </form>
            <div class="info">Conexão segura para servidor privado.</div>
        </div>
    </body>
    </html>
    """

if __name__ == '__main__':
    try:
        with app.app_context():
            db.create_all()
    except Exception as e:
        print(f"Aviso ao inicializar tabelas: {e}")
        
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
        
