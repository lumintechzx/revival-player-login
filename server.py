import os
import logging
import re
from flask import Flask, request, jsonify, render_template_string, redirect, url_for
from flask_cors import CORS

import firebase_admin
from firebase_admin import credentials, db

# --- CONFIGURAÇÃO INICIAL ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
app = Flask(__name__)

# Chave secreta para sessões e segurança
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "7b9e8f1c4a2d5e3f8b0c9a1d4f6e8a2b5c7d9e0f1a3b5c7d9e0f1a3b5c7d9e0")

# --- Configuração do Firebase ---
FIREBASE_CREDENTIALS_PATH = "serviceAccountKey.json"
FIREBASE_DATABASE_URL = "https://project-revival-29e2b-default-rtdb.firebaseio.com" 

# --- Inicialização Robusta do Firebase ---
try:
    if not firebase_admin._apps:
        if os.path.exists(FIREBASE_CREDENTIALS_PATH):
            cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
            firebase_admin.initialize_app(cred, {
                'databaseURL': FIREBASE_DATABASE_URL
            })
            logging.info("Firebase inicializado com sucesso para o projeto project-revival-29e2b.")
        else:
            logging.warning(f"AVISO: Arquivo {FIREBASE_CREDENTIALS_PATH} não encontrado. Usando modo de simulação (Mock).")
except Exception as e:
    logging.error(f"Erro na inicialização do Firebase: {e}")

# Habilitar CORS
CORS(app, supports_credentials=True)

# --- Funções de Utilitário para o Banco de Dados Firebase ---
def get_user_data_from_firebase(username):
    try:
        if not firebase_admin._apps: return None
        user_ref = db.reference(f'/users/{username}')
        return user_ref.get()
    except Exception as e:
        logging.error(f"Erro ao buscar dados do usuário {username}: {e}")
        return None

def set_user_data_in_firebase(username, data):
    try:
        if not firebase_admin._apps: return False
        user_ref = db.reference(f'/users/{username}')
        user_ref.set(data)
        return True
    except Exception as e:
        logging.error(f"Erro ao definir dados do usuário {username}: {e}")
        return False

def get_all_users_from_firebase():
    try:
        if not firebase_admin._apps: return {}
        users_ref = db.reference('/users')
        return users_ref.get() or {}
    except Exception as e:
        logging.error(f"Erro ao buscar todos os usuários: {e}")
        return {}

# --- Função para obter dados da requisição ---
def get_request_data():
    if request.is_json:
        return request.get_json()
    else:
        return request.form

# --- ROTAS ---

@app.route("/", methods=["GET"])
def index():
    return render_template_string(get_auth_html("fbconnect://success", ""))

@app.route("/auth_login_submit", methods=["POST"])
def process_login():
    data = get_request_data()
    username = data.get("username")
    password = data.get("pass")
    redir = data.get("redirect_uri", "fbconnect://success")
    state = data.get("state", "")

    if not username or not password:
        return jsonify({"status": "error", "message": "Campos obrigatórios ausentes"}), 400

    user_data = get_user_data_from_firebase(username)

    if user_data and str(user_data.get("password")) == str(password):
        access_token = "REVIVAL_TOKEN_OK"
        final_redirect = f"{redir}#access_token={access_token}&state={state}"
        logging.info(f"Login bem-sucedido: {username}")
        return jsonify({"status": "success", "redirect": final_redirect})
    
    return jsonify({"status": "error", "message": "Usuário ou senha incorretos"}), 401

@app.route("/auth_register_submit", methods=["POST"])
def process_register():
    data = get_request_data()
    username = data.get("username")
    password = data.get("pass")
    confirm = data.get("confirm_pass")

    if not username or not password or not confirm:
        return jsonify({"status": "error", "message": "Preencha todos os campos"}), 400

    if password != confirm:
        return jsonify({"status": "error", "message": "Senhas não coincidem"}), 400

    if get_user_data_from_firebase(username):
        return jsonify({"status": "error", "message": "Usuário já existe"}), 409

    new_user = {
        "username": username,
        "password": password,
        "diamonds": 5000,
        "gold": 10000,
        "items": "1001,1002",
        "created_at": db.server_timestamp() if firebase_admin._apps else "now"
    }
    
    if set_user_data_in_firebase(username, new_user):
        logging.info(f"Novo usuário registrado: {username}")
        return jsonify({"status": "success", "message": "Conta criada com sucesso!"}), 201
    return jsonify({"status": "error", "message": "Erro ao salvar conta"}), 500

@app.route("/admin/users", methods=["GET"])
def list_users():
    users = get_all_users_from_firebase()
    return jsonify({"status": "success", "users": users})

# --- Interface HTML ---

def get_auth_html(redir, state):
    return f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Revival Server | Painel</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Roboto:wght@300;400;700&display=swap');
            
            :root {{
                --primary: #ff0000;
                --bg: #0a0a0a;
                --card: #1a1a1a;
                --text: #ffffff;
                --gray: #888;
                --border: #333;
            }}

            body {{ 
                background: var(--bg); 
                color: var(--text); 
                font-family: 'Roboto', sans-serif; 
                display: flex; 
                justify-content: center; 
                align-items: center; 
                min-height: 100vh; 
                margin: 0; 
            }}

            .container {{ 
                background: var(--card); 
                border: 2px solid var(--primary); 
                padding: 30px; 
                border-radius: 15px; 
                width: 400px; 
                text-align: center; 
                box-shadow: 0 0 25px rgba(255, 0, 0, 0.3); 
            }}

            h2 {{ font-family: 'Orbitron', sans-serif; color: var(--primary); margin-bottom: 25px; letter-spacing: 2px; }}

            .tabs {{ display: flex; margin-bottom: 25px; border-bottom: 1px solid var(--border); }}
            .tab {{ 
                flex: 1; 
                padding: 12px; 
                cursor: pointer; 
                color: var(--gray); 
                transition: 0.3s; 
                font-family: 'Orbitron', sans-serif;
                font-size: 13px;
            }}
            .tab.active {{ border-bottom: 3px solid var(--primary); color: var(--text); }}

            input {{ 
                width: calc(100% - 24px); 
                padding: 12px; 
                margin: 10px 0; 
                background: #222; 
                border: 1px solid var(--border); 
                border-radius: 8px; 
                color: #fff; 
                text-align: center; 
                outline: none;
            }}
            input:focus {{ border-color: var(--primary); }}

            button {{ 
                width: 100%; 
                padding: 15px; 
                background: var(--primary); 
                border: none; 
                border-radius: 8px; 
                color: white; 
                font-weight: bold; 
                cursor: pointer; 
                text-transform: uppercase; 
                margin-top: 15px; 
                font-family: 'Orbitron', sans-serif;
                transition: 0.2s;
            }}
            button:hover {{ background: #cc0000; transform: translateY(-2px); }}

            #msg {{ margin-top: 15px; color: var(--primary); font-size: 13px; min-height: 20px; }}

            .form-section {{ display: none; }}
            .form-section.active {{ display: block; }}

            /* Estilo para a Lista de Usuários */
            .user-list {{ 
                max-height: 300px; 
                overflow-y: auto; 
                text-align: left; 
                margin-top: 10px; 
                padding-right: 5px;
            }}
            .user-item {{ 
                background: #252525; 
                padding: 12px; 
                margin-bottom: 8px; 
                border-radius: 6px; 
                border-left: 3px solid var(--primary);
                cursor: pointer;
            }}
            .user-item:hover {{ background: #333; }}
            .user-name {{ font-weight: bold; display: block; }}
            .user-details {{ font-size: 11px; color: var(--gray); margin-top: 4px; }}
            
            ::-webkit-scrollbar {{ width: 5px; }}
            ::-webkit-scrollbar-track {{ background: #111; }}
            ::-webkit-scrollbar-thumb {{ background: var(--primary); }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>REVIVAL SERVER</h2>
            <div class="tabs">
                <div id="tab-login" class="tab active" onclick="switchTab('login')">LOGIN</div>
                <div id="tab-reg" class="tab" onclick="switchTab('reg')">REGISTRO</div>
                <div id="tab-users" class="tab" onclick="switchTab('users')">USUÁRIOS</div>
            </div>

            <div id="form-login" class="form-section active">
                <input type="text" id="lu" placeholder="NOME DE USUÁRIO">
                <input type="password" id="lp" placeholder="SENHA">
                <button onclick="handleAuth('login')">ENTRAR NO SISTEMA</button>
            </div>

            <div id="form-reg" class="form-section">
                <input type="text" id="ru" placeholder="ESCOLHA UM USUÁRIO">
                <input type="password" id="rp" placeholder="DEFINA UMA SENHA">
                <input type="password" id="rc" placeholder="CONFIRME A SENHA">
                <button onclick="handleAuth('reg')">CRIAR MINHA CONTA</button>
            </div>

            <div id="form-users" class="form-section">
                <div id="user-list-container" class="user-list">
                    <p style="text-align:center; color:var(--gray);">Carregando usuários...</p>
                </div>
                <button onclick="loadUsers()" style="padding: 10px; font-size: 11px; margin-top: 10px; background: #333;">ATUALIZAR LISTA</button>
            </div>

            <div id="msg"></div>
        </div>

        <script>
            function switchTab(t) {{
                document.querySelectorAll('.tab').forEach(e => e.classList.remove('active'));
                document.querySelectorAll('.form-section').forEach(e => e.classList.remove('active'));
                document.getElementById('tab-' + t).classList.add('active');
                document.getElementById('form-' + t).classList.add('active');
                document.getElementById('msg').innerText = "";
                
                if(t === 'users') loadUsers();
            }}

            async function loadUsers() {{
                const container = document.getElementById('user-list-container');
                try {{
                    const r = await fetch('/admin/users');
                    const d = await r.json();
                    if(d.status === "success") {{
                        const users = d.users;
                        if(!users || Object.keys(users).length === 0) {{
                            container.innerHTML = '<p style="text-align:center; color:var(--gray);">Nenhum usuário registrado.</p>';
                            return;
                        }}
                        
                        let html = "";
                        for(let key in users) {{
                            const u = users[key];
                            html += `
                                <div class="user-item" onclick="alert('Usuário: ${{u.username}}\\nDiamantes: ${{u.diamonds}}\\nOuro: ${{u.gold}}')">
                                    <span class="user-name">${{u.username}}</span>
                                    <div class="user-details">
                                        💎 ${{u.diamonds}} | 💰 ${{u.gold}} | 📦 ${{u.items}}
                                    </div>
                                </div>
                            `;
                        }}
                        container.innerHTML = html;
                    }}
                }} catch(e) {{
                    container.innerHTML = '<p style="color:red;">Erro ao carregar lista.</p>';
                }}
            }}

            async function handleAuth(type) {{
                const msg = document.getElementById('msg');
                msg.innerText = "Processando requisição...";
                let body = "";
                let url = "";
                
                if(type === 'login') {{
                    url = '/auth_login_submit';
                    const u = document.getElementById('lu').value;
                    const p = document.getElementById('lp').value;
                    body = `username=${{encodeURIComponent(u)}}&pass=${{encodeURIComponent(p)}}&redirect_uri={redir}&state={state}`;
                }} else {{
                    url = '/auth_register_submit';
                    const u = document.getElementById('ru').value;
                    const p = document.getElementById('rp').value;
                    const c = document.getElementById('rc').value;
                    body = `username=${{encodeURIComponent(u)}}&pass=${{encodeURIComponent(p)}}&confirm_pass=${{encodeURIComponent(c)}}`;
                }}

                try {{
                    const r = await fetch(url, {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/x-www-form-urlencoded'}},
                        body: body
                    }});
                    const d = await r.json();
                    
                    if(d.status === "success") {{
                        if(type === 'login') {{
                            msg.style.color = "#00ff00";
                            msg.innerText = "Login autorizado! Redirecionando...";
                            setTimeout(() => {{ window.location.href = d.redirect; }}, 1000);
                        }} else {{ 
                            msg.style.color = "#00ff00";
                            msg.innerText = "Conta criada com sucesso!"; 
                            setTimeout(() => switchTab('login'), 1500); 
                        }}
                    }} else {{
                        msg.style.color = "#ff0000";
                        msg.innerText = d.message || "Erro na operação";
                    }}
                }} catch(e) {{ 
                    msg.style.color = "#ff0000";
                    msg.innerText = "Erro de conexão com o servidor"; 
                }}
            }}
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
    
