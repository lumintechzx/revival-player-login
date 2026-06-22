import os
import logging
import re
from flask import Flask, request, jsonify, render_template_string, redirect, url_for
from flask_cors import CORS

import firebase_admin
from firebase_admin import credentials, auth, db

# --- CONFIGURAÇÃO INICIAL ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
app = Flask(__name__)

# É CRÍTICO que esta chave seja forte, única e mantida em segredo. Use variáveis de ambiente em produção.
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "Revival_777")

# --- Configuração do Firebase ---
# O arquivo `serviceAccountKey.json` foi fornecido e salvo no diretório atual.
FIREBASE_CREDENTIALS_PATH = "serviceAccountKey.json"
# Substitua pelo URL real do seu Realtime Database (encontrado no console do Firebase)
FIREBASE_DATABASE_URL = "https://project-revival-29e2b-default-rtdb.firebaseio.com" 

try:
    if not firebase_admin._apps:
        cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred, {
            'databaseURL': FIREBASE_DATABASE_URL
        })
    logging.info("Firebase inicializado com sucesso para o projeto project-revival-29e2b.")
except Exception as e:
    logging.error(f"Erro ao inicializar Firebase: {e}")

# Habilitar CORS para todas as rotas e origens.
CORS(app, supports_credentials=True)

# --- Funções de Utilitário para o Banco de Dados Firebase ---
def get_user_data_from_firebase(username):
    try:
        # No Realtime DB, vamos organizar por /users/username
        user_ref = db.reference(f'/users/{username}')
        return user_ref.get()
    except Exception as e:
        logging.error(f"Erro ao buscar dados do usuário {username} no Firebase: {e}")
        return None

def update_user_data_in_firebase(username, data):
    try:
        user_ref = db.reference(f'/users/{username}')
        user_ref.update(data)
        return True
    except Exception as e:
        logging.error(f"Erro ao atualizar dados do usuário {username} no Firebase: {e}")
        return False

# --- Função para obter dados da requisição (JSON ou Form-data) ---
def get_request_data():
    if request.is_json:
        return request.get_json()
    else:
        return request.form

# --- Tratamento de Erros Global ---
@app.errorhandler(400)
def bad_request(error):
    return jsonify({"status": "error", "message": "Requisição inválida"}), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({"status": "error", "message": "Recurso não encontrado"}), 404

@app.errorhandler(500)
def internal_server_error(error):
    logging.exception("Erro interno:")
    return jsonify({"status": "error", "message": "Erro interno do servidor"}), 500

# --- ROTAS DE INTERCEPTAÇÃO E LOGIN ---
@app.route("/<path:url>", methods=["POST", "GET"])
def universal_handler(url):
    logging.info(f"Rota: {url} | Método: {request.method}")

    # 1. Rota de Login (Interface HTML)
    if "dialog/oauth" in url or "login" in url:
        if request.method == "POST":
            return process_login()
        redirect_uri = request.args.get("redirect_uri", "")
        state = request.args.get("state", "")
        return render_template_string(get_auth_html(redirect_uri, state))

    # 2. Rota de Perfil do Jogador
    if "profile" in url:
        username = request.args.get("username")
        if not username:
            return jsonify({"status": "error", "message": "Username ausente"}), 400
        
        user_data = get_user_data_from_firebase(username)
        if user_data:
            return jsonify({
                "status": "success", 
                "diamonds": user_data.get("diamonds", 5000), 
                "gold": user_data.get("gold", 10000), 
                "items": user_data.get("items", "1001,1002")
            })
        return jsonify({"status": "error", "message": "Usuário não encontrado"}), 404

    # 3. Rota de Ranking
    if "ranking" in url:
        try:
            users_ref = db.reference('/users')
            users = users_ref.get()
            if not users: return jsonify({"status": "success", "rank": []})
            
            rank_list = [{"user": u_data.get("username"), "score": u_data.get("diamonds", 0)} for u_data in users.values()]
            rank_list = sorted(rank_list, key=lambda x: x['score'], reverse=True)[:10]
            return jsonify({"status": "success", "rank": rank_list})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

    # 4. Rota Admin para Adicionar Diamantes
    if "admin/add_diamonds" in url and request.method == "POST":
        data = get_request_data()
        username, amount, secret = data.get("username"), data.get("amount"), data.get("secret_key")
        
        if secret != app.config["SECRET_KEY"]:
            return jsonify({"status": "error", "message": "Chave inválida"}), 403
        
        user_data = get_user_data_from_firebase(username)
        if user_data:
            new_diamonds = user_data.get("diamonds", 0) + int(amount)
            update_user_data_in_firebase(username, {"diamonds": new_diamonds})
            return jsonify({"status": "success", "message": f"Diamantes adicionados! Novo total: {new_diamonds}"})
        return jsonify({"status": "error", "message": "Usuário não encontrado"}), 404

    return jsonify({"status": "success", "version": "1.39", "message": "Revival Server Ativo"}), 200

# Lógica de Login com Firebase
def process_login():
    data = get_request_data()
    username = data.get("username")
    password = data.get("pass")
    redir = data.get("redirect_uri", "fbconnect://success")
    state = data.get("state", "")

    logging.info(f"Tentativa de login: {username}")

    if not username or not password:
        return jsonify({"status": "error", "message": "Campos obrigatórios ausentes"}), 400

    user_data = get_user_data_from_firebase(username)

    # Se o usuário não existir, vamos criar um novo (Auto-registro para facilitar)
    if not user_data:
        logging.info(f"Criando novo usuário no Firebase: {username}")
        new_user = {
            "username": username,
            "password": password, # Em produção, use hashing!
            "diamonds": 5000,
            "gold": 10000,
            "items": "1001,1002"
        }
        update_user_data_in_firebase(username, new_user)
        user_data = new_user

    if user_data.get("password") == password:
        access_token = "REVIVAL_TOKEN_OK"
        final_redirect = f"{redir}#access_token={access_token}&state={state}"
        return jsonify({"status": "success", "redirect": final_redirect})
    
    return jsonify({"status": "error", "message": "Senha incorreta"}), 401

# HTML Premium
def get_auth_html(redir, state):
    return f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Revival Login</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap');
            body {{ background: #0a0a0a; color: #fff; font-family: 'Orbitron', sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
            .card {{ background: rgba(20,20,20,0.9); border: 2px solid #ff5500; padding: 40px; border-radius: 15px; width: 320px; text-align: center; box-shadow: 0 0 20px #ff5500; }}
            input {{ width: calc(100% - 24px); padding: 12px; margin: 10px 0; background: #222; border: 1px solid #444; border-radius: 8px; color: #fff; text-align: center; }}
            button {{ width: 100%; padding: 15px; background: #ff5500; border: none; border-radius: 8px; color: white; font-weight: bold; cursor: pointer; text-transform: uppercase; margin-top: 15px; }}
            #msg {{ margin-top: 15px; color: #ff5500; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h2 style="color:#ff5500; margin-bottom:20px;">REVIVAL</h2>
            <input type="text" id="u" placeholder="USUÁRIO">
            <input type="password" id="p" placeholder="SENHA">
            <button onclick="login()">ENTRAR</button>
            <div id="msg"></div>
        </div>
        <script>
            function login() {{
                const u = document.getElementById('u').value;
                const p = document.getElementById('p').value;
                const msg = document.getElementById('msg');
                msg.innerText = "Conectando...";

                fetch('/auth_login_submit', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/x-www-form-urlencoded'}},
                    body: `username=${{u}}&pass=${{p}}&redirect_uri={redir}&state={state}`
                }})
                .then(r => r.json())
                .then(d => {{
                    if(d.status === "success") window.location.href = d.redirect;
                    else msg.innerText = d.message || "Erro no login";
                }})
                .catch(() => msg.innerText = "Erro de conexão");
            }}
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
                
