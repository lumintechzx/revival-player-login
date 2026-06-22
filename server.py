import os
import logging
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, db

# --- CONFIGURAÇÃO ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
app = Flask(__name__)
app.config["SECRET_KEY"] = "revival_secret_key_123"
CORS(app)

FIREBASE_DATABASE_URL = "https://project-revival-29e2b-default-rtdb.firebaseio.com"
FIREBASE_CRED_PATH = "serviceAccountKey.json"

firebase_status = "Iniciando..."

try:
    if not firebase_admin._apps:
        if os.path.exists(FIREBASE_CRED_PATH):
            cred = credentials.Certificate(FIREBASE_CRED_PATH)
            firebase_admin.initialize_app(cred, {'databaseURL': FIREBASE_DATABASE_URL})
            firebase_status = "Conectado"
        else:
            firebase_status = "Arquivo serviceAccountKey.json não encontrado"
except Exception as e:
    firebase_status = f"Erro na inicialização: {str(e)}"

# --- FUNÇÕES ---
def get_user_data(username):
    try:
        return db.reference(f'/users/{username}').get()
    except Exception as e:
        logging.error(f"Erro ao buscar {username}: {e}")
        return "ERROR"

def save_user_data(username, data):
    try:
        db.reference(f'/users/{username}').set(data)
        return True
    except Exception as e:
        logging.error(f"Erro ao salvar {username}: {e}")
        return False

# --- ROTAS ---
@app.route("/", methods=["GET"])
def index():
    redir = request.args.get("redirect_uri", "fbconnect://success")
    state = request.args.get("state", "")
    return render_template_string(get_html(), redir=redir, state=state, status=firebase_status)

@app.route("/<path:path>", methods=["GET", "POST"])
def universal(path):
    if path == "auth_login_submit":
        data = request.form
        user = data.get("username")
        pw = data.get("pass")
        redir = data.get("redirect_uri")
        state = data.get("state")
        
        res = get_user_data(user)
        if res == "ERROR":
            return jsonify({"status": "error", "message": "Erro de conexão com o Firebase. Verifique a chave JSON."}), 500
        
        if res and str(res.get("password")) == str(pw):
            return jsonify({"status": "success", "redirect": f"{redir}#access_token=OK&state={state}"})
        return jsonify({"status": "error", "message": "Usuário ou senha incorretos"}), 401

    if path == "auth_register_submit":
        data = request.form
        user = data.get("username")
        pw = data.get("pass")
        cpw = data.get("confirm_pass")
        
        if pw != cpw:
            return jsonify({"status": "error", "message": "Senhas não coincidem"}), 400
            
        if get_user_data(user) not in [None, "ERROR"]:
            return jsonify({"status": "error", "message": "Usuário já existe"}), 409
            
        new_user = {"username": user, "password": pw, "diamonds": 5000, "gold": 10000}
        if save_user_data(user, new_user):
            return jsonify({"status": "success", "message": "Conta criada!"})
        return jsonify({"status": "error", "message": "Erro ao salvar no Firebase. Verifique as Regras do Database."}), 500

    if path == "admin/users":
        try:
            users = db.reference('/users').get() or {}
            return jsonify({"status": "success", "users": users})
        except:
            return jsonify({"status": "error", "message": "Erro ao listar"}), 500

    return jsonify({"status": "success", "msg": "Server Online"}), 200

def get_html():
    return """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Revival</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap');
            body { background: #000; color: #fff; font-family: 'Orbitron', sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
            .card { background: #111; border: 2px solid #f00; padding: 25px; border-radius: 15px; width: 300px; text-align: center; box-shadow: 0 0 20px #f00; }
            input { width: 100%; box-sizing: border-box; padding: 12px; margin: 10px 0; background: #222; border: 1px solid #444; border-radius: 8px; color: #fff; text-align: center; font-family: 'Orbitron'; }
            button { width: 100%; padding: 12px; background: #f00; border: none; border-radius: 8px; color: #fff; font-weight: bold; cursor: pointer; margin-top: 10px; font-family: 'Orbitron'; }
            .tabs { display: flex; margin-bottom: 15px; }
            .tab { flex: 1; padding: 10px; cursor: pointer; color: #555; font-size: 12px; border-bottom: 1px solid #333; }
            .tab.active { color: #fff; border-bottom: 2px solid #f00; }
            .sec { display: none; }
            .sec.active { display: block; }
            #msg { margin-top: 15px; font-size: 11px; color: #f00; }
            .status { font-size: 9px; color: #444; margin-top: 10px; }
        </style>
    </head>
    <body>
        <div class="card">
            <h2 style="color:#f00; margin-bottom:20px;">REVIVAL</h2>
            <div class="tabs">
                <div id="t1" class="tab active" onclick="sw('login')">LOGIN</div>
                <div id="t2" class="tab" onclick="sw('reg')">REGISTRO</div>
                <div id="t3" class="tab" onclick="sw('adm')">LISTA</div>
            </div>
            <div id="s-login" class="sec active">
                <input id="lu" placeholder="USUÁRIO">
                <input id="lp" type="password" placeholder="SENHA">
                <button onclick="go('login')">ENTRAR</button>
            </div>
            <div id="s-reg" class="sec">
                <input id="ru" placeholder="USUÁRIO">
                <input id="rp" type="password" placeholder="SENHA">
                <input id="rc" type="password" placeholder="CONFIRMAR">
                <button onclick="go('reg')">CRIAR</button>
            </div>
            <div id="s-adm" class="sec">
                <div id="list" style="max-height:100px; overflow:auto; font-size:10px; text-align:left;"></div>
                <button onclick="load()" style="background:#222; font-size:10px;">RECARREGAR</button>
            </div>
            <div id="msg"></div>
            <div class="status">Firebase: {{ status }}</div>
        </div>
        <script>
            const REDIR = "{{ redir }}"; const STATE = "{{ state }}";
            function sw(n){
                document.querySelectorAll('.tab, .sec').forEach(e=>e.classList.remove('active'));
                document.getElementById('t'+(n==='login'?'1':n==='reg'?'2':'3')).classList.add('active');
                document.getElementById('s-'+n).classList.add('active');
            }
            async function load(){
                const l = document.getElementById('list');
                try {
                    const r = await fetch('/admin/users');
                    const d = await r.json();
                    let h = ""; for(let k in d.users) h += `<div>- ${k}</div>`;
                    l.innerHTML = h || "Vazio";
                } catch(e) { l.innerText = "Erro"; }
            }
            async function go(t){
                const m = document.getElementById('msg'); m.innerText = "Processando...";
                let b = new URLSearchParams();
                if(t==='login'){
                    b.append('username', document.getElementById('lu').value);
                    b.append('pass', document.getElementById('lp').value);
                    b.append('redirect_uri', REDIR); b.append('state', STATE);
                } else {
                    b.append('username', document.getElementById('ru').value);
                    b.append('pass', document.getElementById('rp').value);
                    b.append('confirm_pass', document.getElementById('rc').value);
                }
                try {
                    const r = await fetch(t==='login'?'/auth_login_submit':'/auth_register_submit', {method:'POST', body:b});
                    const d = await r.json();
                    if(d.status==='success'){
                        if(t==='login') window.location.href = d.redirect;
                        else { m.style.color="#0f0"; m.innerText="Criado!"; sw('login'); }
                    } else { m.innerText = d.message; }
                } catch(e) { m.innerText = "Erro de conexão"; }
            }
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
    
