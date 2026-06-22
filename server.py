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

# CORS Habilitado
CORS(app, resources={r"/*": {"origins": "*"}})

# --- Configuração do Firebase ---
FIREBASE_CREDENTIALS_PATH = "serviceAccountKey.json"
FIREBASE_DATABASE_URL = "https://project-revival-29e2b-default-rtdb.firebaseio.com" 

firebase_enabled = False
try:
    if os.path.exists(FIREBASE_CREDENTIALS_PATH):
        cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred, {'databaseURL': FIREBASE_DATABASE_URL})
        firebase_enabled = True
        logging.info("Firebase conectado com sucesso.")
    else:
        logging.error("ERRO: serviceAccountKey.json não encontrado.")
except Exception as e:
    logging.error(f"ERRO FIREBASE: {e}")

# --- Funções do Banco ---
def get_user(username):
    if not firebase_enabled: return None
    try:
        return db.reference(f'/users/{username}').get()
    except Exception as e:
        logging.error(f"Erro ao buscar: {e}")
        return None

def save_user(username, data):
    if not firebase_enabled: return False
    try:
        db.reference(f'/users/{username}').set(data)
        return True
    except Exception as e:
        logging.error(f"Erro ao salvar: {e}")
        return False

def get_all_users():
    if not firebase_enabled: return {}
    try:
        return db.reference('/users').get() or {}
    except Exception as e:
        logging.error(f"Erro ao listar: {e}")
        return {}

# --- ROTAS ---

@app.route("/", methods=["GET"])
def index():
    redirect_uri = request.args.get("redirect_uri", "fbconnect://success")
    state = request.args.get("state", "")
    return render_template_string(get_auth_html(redirect_uri, state))

@app.route("/<path:path>", methods=["GET", "POST"])
def catch_all(path):
    if path == "auth_login_submit": return process_login()
    if path == "auth_register_submit": return process_register()
    if path == "admin/users": return jsonify({"status": "success", "users": get_all_users()})
    
    if "dialog/oauth" in path or "login" in path:
        redirect_uri = request.args.get("redirect_uri", "fbconnect://success")
        state = request.args.get("state", "")
        return render_template_string(get_auth_html(redirect_uri, state))

    return jsonify({"status": "success", "message": "Server Online", "path": path})

def process_login():
    data = request.form if request.form else request.get_json()
    if not data: return jsonify({"status": "error", "message": "Sem dados"}), 400
    
    username = data.get("username")
    password = data.get("pass")
    redir = data.get("redirect_uri", "fbconnect://success")
    state = data.get("state", "")

    if not firebase_enabled:
        return jsonify({"status": "error", "message": "Banco de dados offline"}), 500

    user_data = get_user(username)
    if user_data and str(user_data.get("password")) == str(password):
        final_redirect = f"{redir}#access_token=REVIVAL_OK&state={state}"
        return jsonify({"status": "success", "redirect": final_redirect})
    
    return jsonify({"status": "error", "message": "Login inválido"}), 401

def process_register():
    data = request.form if request.form else request.get_json()
    if not data: return jsonify({"status": "error", "message": "Sem dados"}), 400

    username = data.get("username")
    password = data.get("pass")
    confirm = data.get("confirm_pass")

    if not username or not password:
        return jsonify({"status": "error", "message": "Campos vazios"}), 400

    if password != confirm:
        return jsonify({"status": "error", "message": "Senhas diferentes"}), 400

    if not firebase_enabled:
        return jsonify({"status": "error", "message": "Banco de dados offline"}), 500

    if get_user(username):
        return jsonify({"status": "error", "message": "Usuário já existe"}), 409

    new_user = {"username": username, "password": password, "diamonds": 5000, "gold": 10000}
    
    if save_user(username, new_user):
        return jsonify({"status": "success", "message": "Conta criada!"}), 201
    return jsonify({"status": "error", "message": "Erro ao salvar"}), 500

# --- HTML (CHAVES ESCAPADAS CORRETAMENTE) ---
def get_auth_html(redir, state):
    # Usando string normal para evitar conflito de f-string com JavaScript
    html = """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Revival Server</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap');
            body { background: #0a0a0a; color: #fff; font-family: 'Orbitron', sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
            .box { background: #111; border: 2px solid #f00; padding: 30px; border-radius: 15px; width: 320px; text-align: center; box-shadow: 0 0 20px #f00; }
            .tabs { display: flex; margin-bottom: 20px; border-bottom: 1px solid #333; }
            .tab { flex: 1; padding: 10px; cursor: pointer; color: #666; font-size: 12px; }
            .tab.active { color: #fff; border-bottom: 2px solid #f00; }
            input { width: 100%; box-sizing: border-box; padding: 12px; margin: 10px 0; background: #222; border: 1px solid #444; border-radius: 8px; color: #fff; text-align: center; font-family: 'Orbitron'; }
            button { width: 100%; padding: 15px; background: #f00; border: none; border-radius: 8px; color: #fff; font-weight: bold; cursor: pointer; margin-top: 10px; font-family: 'Orbitron'; }
            #msg { margin-top: 15px; font-size: 12px; color: #f00; min-height: 15px; }
            .section { display: none; }
            .section.active { display: block; }
        </style>
    </head>
    <body>
        <div class="box">
            <h2 style="color:#f00; margin-bottom:20px;">REVIVAL</h2>
            <div class="tabs">
                <div id="t1" class="tab active" onclick="sw('login')">LOGIN</div>
                <div id="t2" class="tab" onclick="sw('reg')">REGISTRO</div>
                <div id="t3" class="tab" onclick="sw('adm')">LISTA</div>
            </div>

            <div id="s-login" class="section active">
                <input type="text" id="lu" placeholder="USUÁRIO">
                <input type="password" id="lp" placeholder="SENHA">
                <button onclick="send('login')">ENTRAR</button>
            </div>

            <div id="s-reg" class="section">
                <input type="text" id="ru" placeholder="USUÁRIO">
                <input type="password" id="rp" placeholder="SENHA">
                <input type="password" id="rc" placeholder="CONFIRMAR">
                <button onclick="send('reg')">CRIAR CONTA</button>
            </div>

            <div id="s-adm" class="section">
                <div id="list" style="max-height:150px; overflow-y:auto; font-size:11px; text-align:left;"></div>
                <button onclick="load()" style="background:#333; font-size:10px;">ATUALIZAR</button>
            </div>

            <div id="msg"></div>
        </div>

        <script>
            const REDIR = \"""" + redir + """\";
            const STATE = \"""" + state + """\";

            function sw(n) {
                document.querySelectorAll('.tab, .section').forEach(e => e.classList.remove('active'));
                document.getElementById('t'+(n==='login'?'1':n==='reg'?'2':'3')).classList.add('active');
                document.getElementById('s-'+n).classList.add('active');
                if(n==='adm') load();
            }

            async function load() {
                const l = document.getElementById('list');
                try {
                    const r = await fetch('/admin/users');
                    const d = await r.json();
                    let h = "";
                    for(let k in d.users) h += `<div style="padding:5px; border-bottom:1px solid #222;">${k}</div>`;
                    l.innerHTML = h || "Vazio";
                } catch(e) { l.innerText = "Erro ao carregar"; }
            }

            async function send(t) {
                const m = document.getElementById('msg');
                m.innerText = "Processando...";
                let u = t === 'login' ? '/auth_login_submit' : '/auth_register_submit';
                let b = new URLSearchParams();
                if(t==='login') {
                    b.append('username', document.getElementById('lu').value);
                    b.append('pass', document.getElementById('lp').value);
                    b.append('redirect_uri', REDIR);
                    b.append('state', STATE);
                } else {
                    b.append('username', document.getElementById('ru').value);
                    b.append('pass', document.getElementById('rp').value);
                    b.append('confirm_pass', document.getElementById('rc').value);
                }

                try {
                    const r = await fetch(u, { method: 'POST', body: b });
                    const d = await r.json();
                    if(d.status === "success") {
                        if(t==='login') window.location.href = d.redirect;
                        else { m.style.color="#0f0"; m.innerText="Conta criada!"; sw('login'); }
                    } else { m.innerText = d.message; }
                } catch(e) { m.innerText = "Erro de conexão"; }
            }
        </script>
    </body>
    </html>
    """
    return html

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
    
