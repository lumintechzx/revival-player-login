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

# É CRÍTICO que esta chave seja forte, única e mantida em segredo. Use variáveis de ambiente em produção.
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "7b9e8f1c4a2d5e3f8b0c9a1d4f6e8a2b5c7d9e0f1a3b5c7d9e0f1a3b5c7d9e0")

# --- Configuração do Firebase ---
# O arquivo `serviceAccountKey.json` deve estar no mesmo diretório no Render.
FIREBASE_CREDENTIALS_PATH = "serviceAccountKey.json"
# URL do seu Realtime Database do projeto project-revival-29e2b
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
            logging.error(f"ERRO CRÍTICO: Arquivo {FIREBASE_CREDENTIALS_PATH} não encontrado! O Firebase não funcionará.")
except Exception as e:
    logging.error(f"Erro fatal na inicialização do Firebase: {e}")

# Habilitar CORS para todas as rotas e origens.
CORS(app, supports_credentials=True)

# --- Funções de Utilitário para o Banco de Dados Firebase ---
def get_user_data_from_firebase(username):
    try:
        user_ref = db.reference(f'/users/{username}')
        return user_ref.get()
    except Exception as e:
        logging.error(f"Erro ao buscar dados do usuário {username} no Firebase: {e}")
        return None

def set_user_data_in_firebase(username, data):
    try:
        user_ref = db.reference(f'/users/{username}')
        user_ref.set(data)
        return True
    except Exception as e:
        logging.error(f"Erro ao definir dados do usuário {username} no Firebase: {e}")
        return False

def update_user_data_in_firebase(username, data):
    try:
        user_ref = db.reference(f'/users/{username}')
        user_ref.update(data)
        return True
    except Exception as e:
        logging.error(f"Erro ao atualizar dados do usuário {username} no Firebase: {e}")
        return False

# --- Função para obter dados da requisição ---
def get_request_data():
    if request.is_json:
        return request.get_json()
    else:
        return request.form

# --- Tratamento de Erros Global ---
@app.errorhandler(400)
def bad_request(error):
    return jsonify({"status": "error", "message": "Requisição inválida"}), 400

@app.errorhandler(401)
def unauthorized(error):
    return jsonify({"status": "error", "message": "Não autorizado", "details": "Credenciais inválidas ou acesso não permitido."}), 401

@app.errorhandler(403)
def forbidden(error):
    return jsonify({"status": "error", "message": "Acesso proibido", "details": str(error)}), 403

@app.errorhandler(404)
def not_found(error):
    return jsonify({"status": "error", "message": "Recurso não encontrado"}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({"status": "error", "message": "Método não permitido"}), 405

@app.errorhandler(500)
def internal_server_error(error):
    logging.exception("Erro interno:")
    return jsonify({"status": "error", "message": "Erro interno do servidor"}), 500

# --- ROTAS DE INTERCEPTAÇÃO E LOGIN/REGISTRO ---
@app.route("/", methods=["GET"])
def index():
    # Redireciona para a tela de login se acessar a raiz do site
    return render_template_string(get_auth_html("fbconnect://success", ""))

@app.route("/<path:url>", methods=["POST", "GET"])
def universal_handler(url):
    logging.info(f"Rota: {url} | Método: {request.method}")

    # 1. Rota de Login/Registro (Interface HTML)
    if "dialog/oauth" in url or "login" in url:
        if request.method == "POST":
            if "auth_login_submit" in url:
                return process_login()
            elif "auth_register_submit" in url:
                return process_register()
        
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
            
            rank_list = []
            for username_key, u_data in users.items():
                rank_list.append({"user": username_key, "score": u_data.get("diamonds", 0)})
            
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

# Lógica de Login
def process_login():
    data = get_request_data()
    username = data.get("username")
    password = data.get("pass")
    redir = data.get("redirect_uri", "fbconnect://success")
    state = data.get("state", "")

    if not username or not password:
        return jsonify({"status": "error", "message": "Campos obrigatórios ausentes"}), 400

    user_data = get_user_data_from_firebase(username)

    if user_data and user_data.get("password") == password:
        access_token = "REVIVAL_TOKEN_OK"
        final_redirect = f"{redir}#access_token={access_token}&state={state}"
        return jsonify({"status": "success", "redirect": final_redirect})
    
    return jsonify({"status": "error", "message": "Usuário ou senha incorretos"}), 401

# Lógica de Registro
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
        "items": "1001,1002"
    }
    if set_user_data_in_firebase(username, new_user):
        return jsonify({"status": "success", "message": "Conta criada com sucesso!"}), 201
    return jsonify({"status": "error", "message": "Erro ao salvar conta"}), 500

# HTML Premium (Vermelho e Cinza)
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
            body {{ background: #0a0a0a; color: #fff; font-family: 'Orbitron', sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
            .container {{ background: #1a1a1a; border: 2px solid #ff0000; padding: 30px; border-radius: 15px; width: 320px; text-align: center; box-shadow: 0 0 20px #ff0000; }}
            .tabs {{ display: flex; margin-bottom: 20px; }}
            .tab {{ flex: 1; padding: 10px; cursor: pointer; border-bottom: 2px solid #333; color: #888; transition: 0.3s; }}
            .tab.active {{ border-bottom: 2px solid #ff0000; color: #fff; }}
            input {{ width: calc(100% - 24px); padding: 12px; margin: 10px 0; background: #222; border: 1px solid #444; border-radius: 8px; color: #fff; text-align: center; }}
            button {{ width: 100%; padding: 15px; background: #ff0000; border: none; border-radius: 8px; color: white; font-weight: bold; cursor: pointer; text-transform: uppercase; margin-top: 15px; }}
            #msg {{ margin-top: 15px; color: #ff0000; font-size: 12px; min-height: 15px; }}
            .form-section {{ display: none; }}
            .form-section.active {{ display: block; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2 style="color:#ff0000; margin-bottom:20px;">REVIVAL</h2>
            <div class="tabs">
                <div id="tab-login" class="tab active" onclick="switchTab('login')">LOGIN</div>
                <div id="tab-reg" class="tab" onclick="switchTab('reg')">REGISTRAR</div>
            </div>
            <div id="form-login" class="form-section active">
                <input type="text" id="lu" placeholder="USUÁRIO">
                <input type="password" id="lp" placeholder="SENHA">
                <button onclick="handleAuth('login')">ENTRAR</button>
            </div>
            <div id="form-reg" class="form-section">
                <input type="text" id="ru" placeholder="NOVO USUÁRIO">
                <input type="password" id="rp" placeholder="SENHA">
                <input type="password" id="rc" placeholder="CONFIRMAR SENHA">
                <button onclick="handleAuth('reg')">CRIAR CONTA</button>
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
            }}
            async function handleAuth(type) {{
                const msg = document.getElementById('msg');
                msg.innerText = "Processando...";
                let body = "";
                let url = "";
                
                if(type === 'login') {{
                    url = '/auth_login_submit';
                    body = `username=${{document.getElementById('lu').value}}&pass=${{document.getElementById('lp').value}}&redirect_uri={redir}&state={state}`;
                }} else {{
                    url = '/auth_register_submit';
                    body = `username=${{document.getElementById('ru').value}}&pass=${{document.getElementById('rp').value}}&confirm_pass=${{document.getElementById('rc').value}}`;
                }}

                try {{
                    const r = await fetch(url, {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/x-www-form-urlencoded'}},
                        body: body
                    }});
                    const d = await r.json();
                    if(d.status === "success") {{
                        if(type === 'login') window.location.href = d.redirect;
                        else {{ msg.innerText = "Conta criada! Faça login."; switchTab('login'); }}
                    }} else {{
                        msg.innerText = d.message || "Erro na operação";
                    }}
                }} catch(e) {{ msg.innerText = "Erro de conexão"; }}
            }}
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    # Criar usuário inicial 'Foxyz 1020' para garantir que ele exista no Firebase
    try:
        if firebase_admin._apps:
            username_test = "Foxyz 1020"
            if not get_user_data_from_firebase(username_test):
                logging.info(f"Criando usuário de teste: {username_test}")
                set_user_data_in_firebase(username_test, {
                    "username": username_test,
                    "password": "123", # Senha padrão para teste
                    "diamonds": 99999,
                    "gold": 99999,
                    "items": "1001,1002,2003"
                })
    except Exception as e:
        logging.error(f"Erro ao criar usuário inicial: {e}")

    app.run(debug=True, host="0.0.0.0", port=5000)
    
