import os
import logging
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS

import firebase_admin
from firebase_admin import credentials, db

# --- CONFIGURAÇÃO INICIAL ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
app = Flask(__name__)

# Chave secreta
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "7b9e8f1c4a2d5e3f8b0c9a1d4f6e8a2b5c7d9e0f1a3b5c7d9e0f1a3b5c7d9e0")

# Habilitar CORS GLOBALMENTE para evitar erro de conexão no registro
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# --- Configuração do Firebase ---
FIREBASE_CREDENTIALS_PATH = "serviceAccountKey.json"
FIREBASE_DATABASE_URL = "https://project-revival-29e2b-default-rtdb.firebaseio.com" 

# --- Inicialização do Firebase ---
try:
    if not firebase_admin._apps:
        if os.path.exists(FIREBASE_CREDENTIALS_PATH):
            cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
            firebase_admin.initialize_app(cred, {'databaseURL': FIREBASE_DATABASE_URL})
            logging.info("Firebase inicializado com sucesso.")
        else:
            logging.warning("Firebase em modo simulação (serviceAccountKey.json não encontrado).")
except Exception as e:
    logging.error(f"Erro Firebase: {e}")

# --- Funções do Banco ---
def get_user(username):
    if not firebase_admin._apps: return None
    return db.reference(f'/users/{username}').get()

def save_user(username, data):
    if not firebase_admin._apps: return False
    db.reference(f'/users/{username}').set(data)
    return True

def get_all_users():
    if not firebase_admin._apps: return {}
    return db.reference('/users').get() or {}

# --- TRATAMENTO DE ROTAS ---

# Rota Raiz - Serve o HTML
@app.route("/", methods=["GET"])
def index():
    # Pega os parâmetros que o jogo envia (como redirect_uri e state)
    redirect_uri = request.args.get("redirect_uri", "fbconnect://success")
    state = request.args.get("state", "")
    return render_template_string(get_auth_html(redirect_uri, state))

# Rota Universal para capturar qualquer URL que o jogo tente acessar (EVITA O 404)
@app.route("/<path:path>", methods=["GET", "POST"])
def catch_all(path):
    logging.info(f"Jogo acessou rota: {path} [{request.method}]")
    
    # Se for a rota de login/registro vinda do formulário
    if path == "auth_login_submit": return process_login()
    if path == "auth_register_submit": return process_register()
    if path == "admin/users": return jsonify({"status": "success", "users": get_all_users()})
    
    # Se o jogo estiver procurando por rotas de OAuth (Facebook/Google)
    if "dialog/oauth" in path or "login" in path:
        redirect_uri = request.args.get("redirect_uri", "fbconnect://success")
        state = request.args.get("state", "")
        return render_template_string(get_auth_html(redirect_uri, state))

    # Resposta padrão para qualquer outra rota desconhecida (evita erro 404)
    return jsonify({"status": "success", "message": "Revival Server Ativo", "path": path}), 200

# Lógica de Login Corrigida
def process_login():
    data = request.form if request.form else request.get_json()
    username = data.get("username")
    password = data.get("pass")
    redir = data.get("redirect_uri", "fbconnect://success")
    state = data.get("state", "")

    if not username or not password:
        return jsonify({"status": "error", "message": "Usuário e senha obrigatórios"}), 400

    user_data = get_user(username)

    if user_data and str(user_data.get("password")) == str(password):
        # Gera o link de sucesso que o jogo espera para fechar a WebView
        final_redirect = f"{redir}#access_token=REVIVAL_OK&state={state}"
        return jsonify({"status": "success", "redirect": final_redirect})
    
    return jsonify({"status": "error", "message": "Credenciais incorretas"}), 401

# Lógica de Registro Corrigida
def process_register():
    data = request.form if request.form else request.get_json()
    username = data.get("username")
    password = data.get("pass")
    confirm = data.get("confirm_pass")

    if not username or not password or not confirm:
        return jsonify({"status": "error", "message": "Preencha todos os campos"}), 400

    if password != confirm:
        return jsonify({"status": "error", "message": "Senhas não conferem"}), 400

    if get_user(username):
        return jsonify({"status": "error", "message": "Usuário já existe"}), 409

    new_user = {
        "username": username,
        "password": password,
        "diamonds": 5000,
        "gold": 10000,
        "items": "1001,1002"
    }
    
    if save_user(username, new_user):
        return jsonify({"status": "success", "message": "Conta criada!"}), 201
    return jsonify({"status": "error", "message": "Erro no Firebase"}), 500

# --- INTERFACE HTML ---
def get_auth_html(redir, state):
    return f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Revival Server</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap');
            body {{ background: #0a0a0a; color: #fff; font-family: 'Orbitron', sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; overflow: hidden; }}
            .container {{ background: #151515; border: 2px solid #ff0000; padding: 25px; border-radius: 12px; width: 300px; text-align: center; box-shadow: 0 0 20px rgba(255,0,0,0.4); }}
            h2 {{ color: #ff0000; margin-bottom: 20px; font-size: 20px; text-shadow: 0 0 10px #ff0000; }}
            .tabs {{ display: flex; margin-bottom: 15px; border-bottom: 1px solid #333; }}
            .tab {{ flex: 1; padding: 10px; cursor: pointer; color: #666; font-size: 12px; transition: 0.3s; }}
            .tab.active {{ color: #fff; border-bottom: 2px solid #ff0000; }}
            input {{ width: 100%; box-sizing: border-box; padding: 12px; margin: 8px 0; background: #222; border: 1px solid #444; border-radius: 6px; color: #fff; text-align: center; font-family: 'Orbitron'; font-size: 12px; }}
            button {{ width: 100%; padding: 12px; background: #ff0000; border: none; border-radius: 6px; color: #fff; font-weight: bold; cursor: pointer; margin-top: 10px; font-family: 'Orbitron'; }}
            #msg {{ margin-top: 15px; font-size: 11px; color: #ff0000; min-height: 15px; }}
            .form-section {{ display: none; }}
            .form-section.active {{ display: block; }}
            .user-list {{ max-height: 200px; overflow-y: auto; text-align: left; font-size: 10px; }}
            .u-item {{ background: #222; padding: 8px; margin-bottom: 5px; border-left: 2px solid #ff0000; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>REVIVAL</h2>
            <div class="tabs">
                <div id="t-login" class="tab active" onclick="tab('login')">LOGIN</div>
                <div id="t-reg" class="tab" onclick="tab('reg')">REGISTRO</div>
                <div id="t-list" class="tab" onclick="tab('list')">USERS</div>
            </div>

            <div id="f-login" class="form-section active">
                <input type="text" id="lu" placeholder="USUÁRIO">
                <input type="password" id="lp" placeholder="SENHA">
                <button onclick="send('login')">ENTRAR</button>
            </div>

            <div id="f-reg" class="form-section">
                <input type="text" id="ru" placeholder="USUÁRIO">
                <input type="password" id="rp" placeholder="SENHA">
                <input type="password" id="rc" placeholder="CONFIRMAR">
                <button onclick="send('reg')">REGISTRAR</button>
            </div>

            <div id="f-list" class="form-section">
                <div id="list-cont" class="user-list">Carregando...</div>
                <button onclick="load()" style="font-size:10px; background:#333;">ATUALIZAR</button>
            </div>

            <div id="msg"></div>
        </div>

        <script>
            const REDIR = "{redir}";
            const STATE = "{state}";

            function tab(n) {{
                document.querySelectorAll('.tab, .form-section').forEach(e => e.classList.remove('active'));
                document.getElementById('t-'+n).classList.add('active');
                document.getElementById('f-'+n).classList.add('active');
                if(n === 'list') load();
            }}

            async function load() {{
                const c = document.getElementById('list-cont');
                try {{
                    const r = await fetch('/admin/users');
                    const d = await r.json();
                    let h = "";
                    for(let k in d.users) h += `<div class="u-item"><b>${{k}}</b><br>💎 ${{d.users[k].diamonds}}</div>`;
                    c.innerHTML = h || "Vazio";
                }} catch(e) {{ c.innerText = "Erro ao carregar"; }}
            }}

            async function send(type) {{
                const m = document.getElementById('msg');
                m.innerText = "Aguarde...";
                let url = type === 'login' ? '/auth_login_submit' : '/auth_register_submit';
                let body = new URLSearchParams();
                
                if(type === 'login') {{
                    body.append('username', document.getElementById('lu').value);
                    body.append('pass', document.getElementById('lp').value);
                    body.append('redirect_uri', REDIR);
                    body.append('state', STATE);
                }} else {{
                    body.append('username', document.getElementById('ru').value);
                    body.append('pass', document.getElementById('rp').value);
                    body.append('confirm_pass', document.getElementById('rc').value);
                }}

                try {{
                    const r = await fetch(url, {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/x-www-form-urlencoded' }},
                        body: body
                    }});
                    const d = await r.json();
                    if(d.status === "success") {{
                        if(type === 'login') {{
                            m.style.color = "#00ff00";
                            m.innerText = "Sucesso! Entrando...";
                            window.location.href = d.redirect;
                        }} else {{
                            m.style.color = "#00ff00";
                            m.innerText = "Registrado! Faça login.";
                            tab('login');
                        }}
                    }} else {{
                        m.innerText = d.message;
                    }}
                }} catch(e) {{ m.innerText = "Erro de Conexão"; }}
            }}
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    # Roda na porta 5000 (ou a que o seu Render/Host usar)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
        
