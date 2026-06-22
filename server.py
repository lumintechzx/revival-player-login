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
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "revival_secret_777)

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

def set_user_data_in_firebase(username, data):
    try:
        user_ref = db.reference(f'/users/{username}')
        user_ref.set(data)
        return True
    except Exception as e:
        logging.error(f"Erro ao definir dados do usuário {username} no Firebase: {e}")
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
@app.route("/<path:url>", methods=["POST", "GET"])
def universal_handler(url):
    logging.info(f"Rota: {url} | Método: {request.method}")

    # 1. Rota de Login/Registro (Interface HTML)
    if "dialog/oauth" in url or "login" in url or "register" in url:
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
            
            # Ordenar e limitar os 10 primeiros
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

    if not user_data:
        return jsonify({"status": "error", "message": "Usuário não encontrado."}), 401

    # Verificar a senha (agora armazenada como texto puro no Realtime DB para simplicidade com o HTML)
    # Em um cenário real, você usaria Firebase Auth ou hashing de senha no Realtime DB.
    if user_data.get("password") == password:
        access_token = "REVIVAL_TOKEN_OK"
        final_redirect = f"{redir}#access_token={access_token}&state={state}"
        return jsonify({"status": "success", "redirect": final_redirect})
    
    return jsonify({"status": "error", "message": "Senha incorreta"}), 401

# Lógica de Registro com Firebase
def process_register():
    data = get_request_data()
    username = data.get("username")
    password = data.get("pass")
    confirm_password = data.get("confirm_pass")

    logging.info(f"Tentativa de registro para: {username}")

    if not username or not password or not confirm_password:
        return jsonify({"status": "error", "message": "Todos os campos são obrigatórios."}), 400

    if password != confirm_password:
        return jsonify({"status": "error", "message": "As senhas não coincidem."}), 400

    # Validação de username (regex)
    if not re.match(r"^[a-zA-Z0-9_]{3,16}$", username):
        return jsonify({"status": "error", "message": "Username inválido. Use 3-16 caracteres alfanuméricos ou underscore."}), 400

    # Verificar se o usuário já existe no Realtime DB
    existing_user = get_user_data_from_firebase(username)
    if existing_user:
        return jsonify({"status": "error", "message": "Usuário já existe."}), 409

    try:
        # Criar usuário no Firebase Realtime Database
        new_user_data = {
            "username": username,
            "password": password, # Em produção, considere hashing ou Firebase Auth para senhas
            "diamonds": 5000,
            "gold": 10000,
            "items": "1001,1002"
        }
        if set_user_data_in_firebase(username, new_user_data):
            logging.info(f"Usuário {username} registrado com sucesso no Firebase Realtime DB.")
            return jsonify({"status": "success", "message": "Conta criada com sucesso! Faça login."}), 201
        else:
            return jsonify({"status": "error", "message": "Erro ao salvar dados do usuário."}), 500

    except Exception as e:
        logging.error(f"Erro durante o registro de {username}: {e}")
        return jsonify({"status": "error", "message": "Erro interno do servidor durante o registro.", "details": str(e)}), 500

# HTML Premium com Login e Registro (Vermelho e Cinza)
def get_auth_html(redir, state):
    return f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Revival Login/Registro</title>
        <style>
            @import url(\'https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Roboto:wght@400;700&display=swap\');

            :root {{
                --primary-red: #E53935; /* Vermelho vibrante */
                --dark-gray: #212121; /* Cinza escuro */
                --medium-gray: #424242;
                --light-gray: #BDBDBD;
                --text-color: #FAFAFA;
                --shadow-color: rgba(229, 57, 53, 0.5);
            }}

            body {{
                background: linear-gradient(135deg, var(--dark-gray) 0%, #000000 100%);
                color: var(--text-color);
                font-family: 'Roboto', sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                margin: 0;
                overflow: hidden;
            }}
            .container {{
                background: var(--dark-gray);
                border: 2px solid var(--primary-red);
                padding: 20px;
                border-radius: 15px;
                width: 380px;
                text-align: center;
                box-shadow: 0 0 30px var(--shadow-color);
                position: relative;
                overflow: hidden;
            }}
            .tabs {{
                display: flex;
                margin-bottom: 20px;
            }}
            .tab-button {{
                flex: 1;
                padding: 15px 0;
                background: var(--medium-gray);
                border: none;
                color: var(--light-gray);
                font-family: 'Orbitron', sans-serif;
                font-size: 16px;
                cursor: pointer;
                transition: background-color 0.3s ease, color 0.3s ease;
                border-radius: 8px 8px 0 0;
                margin: 0 2px;
            }}
            .tab-button.active {{
                background: var(--primary-red);
                color: var(--text-color);
                box-shadow: 0 2px 10px var(--shadow-color);
            }}
            .tab-button:hover:not(.active) {{
                background-color: #555;
            }}
            .form-section {{
                display: none;
                padding: 20px 0;
            }}
            .form-section.active {{
                display: block;
            }}
            .title {{
                color: var(--primary-red);
                font-family: 'Orbitron', sans-serif;
                font-size: 28px;
                font-weight: 700;
                margin-bottom: 25px;
                text-transform: uppercase;
                letter-spacing: 2px;
                text-shadow: 0 0 10px var(--shadow-color);
            }}
            input {{
                width: calc(100% - 28px);
                padding: 14px;
                margin: 10px 0;
                background: #333;
                border: 1px solid var(--medium-gray);
                border-radius: 8px;
                color: var(--text-color);
                font-size: 16px;
                transition: border-color 0.3s ease, box-shadow 0.3s ease;
            }}
            input:focus {{
                border-color: var(--primary-red);
                box-shadow: 0 0 8px var(--shadow-red);
                outline: none;
            }}
            input::placeholder {{
                color: var(--light-gray);
            }}
            button {{
                width: 100%;
                padding: 16px;
                background: var(--primary-red);
                border: none;
                border-radius: 8px;
                color: white;
                font-weight: bold;
                cursor: pointer;
                font-size: 18px;
                transition: background-color 0.3s ease, transform 0.2s ease;
                margin-top: 20px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            button:hover {{
                background-color: #C62828; /* Vermelho mais escuro */
                transform: translateY(-2px);
            }}
            button:active {{
                transform: translateY(0);
            }}
            #msg {{
                margin-top: 20px;
                font-size: 14px;
                color: var(--primary-red);
                min-height: 20px;
                font-weight: bold;
            }}
            .loading-spinner {{
                border: 4px solid rgba(255,255,255,0.3);
                border-top: 4px solid var(--primary-red);
                border-radius: 50%;
                width: 20px;
                height: 20px;
                animation: spin 1s linear infinite;
                display: inline-block;
                vertical-align: middle;
                margin-left: 10px;
            }}
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="title">Revival Server</div>
            <div class="tabs">
                <button class="tab-button active" onclick="showTab('login')">Login</button>
                <button class="tab-button" onclick="showTab('register')">Registrar</button>
            </div>

            <div id="loginForm" class="form-section active">
                <input type="text" id="loginUser" placeholder="Usuário">
                <input type="password" id="loginPass" placeholder="Senha">
                <button id="loginButton" onclick="handleLogin()">Entrar</button>
            </div>

            <div id="registerForm" class="form-section">
                <input type="text" id="registerUser" placeholder="Novo Usuário">
                <input type="password" id="registerPass" placeholder="Nova Senha">
                <input type="password" id="confirmPass" placeholder="Confirmar Senha">
                <button id="registerButton" onclick="handleRegister()">Registrar</button>
            </div>
            <div id="msg"></div>
        </div>

        <script>
            const redirectUri = "{redir}";
            const state = "{state}";

            function showTab(tabName) {{
                document.querySelectorAll('.tab-button').forEach(button => {{
                    button.classList.remove('active');
                }});
                document.querySelectorAll('.form-section').forEach(section => {{
                    section.classList.remove('active');
                }});

                document.querySelector(`.tab-button[onclick="showTab('${{tabName}}')"]`).classList.add('active');
                document.getElementById(`${{tabName}}Form`).classList.add('active');
                document.getElementById('msg').innerText = ''; // Limpa mensagens ao trocar de aba
            }}

            async function handleLogin() {{
                const u = document.getElementById("loginUser").value;
                const p = document.getElementById("loginPass").value;
                const msgDiv = document.getElementById("msg");
                const loginButton = document.getElementById("loginButton");

                msgDiv.innerText = "";
                loginButton.disabled = true;
                loginButton.innerHTML = 'Entrando... <span class="loading-spinner"></span>';

                if (!u || !p) {{
                    msgDiv.innerText = "Por favor, preencha usuário e senha.";
                    loginButton.disabled = false;
                    loginButton.innerHTML = 'Entrar';
                    return;
                }}

                try {{
                    const response = await fetch("/auth_login_submit", {{
                        method: "POST",
                        headers: {{"Content-Type": "application/x-www-form-urlencoded"}},
                        body: `username=${{u}}&pass=${{p}}&redirect_uri=${{redirectUri}}&state=${{state}}`
                    }});

                    const data = await response.json();

                    if(data.status === "success") {{
                        msgDiv.innerText = "Login bem-sucedido! Redirecionando...";
                        window.location.href = data.redirect;
                    }} else {{
                        msgDiv.innerText = data.message || "Login não teve sucesso. Verifique suas credenciais.";
                    }}
                }} catch (error) {{
                    console.error("Erro na requisição de login:", error);
                    msgDiv.innerText = "Erro de conexão com o servidor. Tente novamente.";
                }} finally {{
                    loginButton.disabled = false;
                    loginButton.innerHTML = 'Entrar';
                }}
            }}

            async function handleRegister() {{
                const u = document.getElementById("registerUser").value;
                const p = document.getElementById("registerPass").value;
                const cp = document.getElementById("confirmPass").value;
                const msgDiv = document.getElementById("msg");
                const registerButton = document.getElementById("registerButton");

                msgDiv.innerText = "";
                registerButton.disabled = true;
                registerButton.innerHTML = 'Registrando... <span class="loading-spinner"></span>';

                if (!u || !p || !cp) {{
                    msgDiv.innerText = "Por favor, preencha todos os campos.";
                    registerButton.disabled = false;
                    registerButton.innerHTML = 'Registrar';
                    return;
                }}

                if (p !== cp) {{
                    msgDiv.innerText = "As senhas não coincidem.";
                    registerButton.disabled = false;
                    registerButton.innerHTML = 'Registrar';
                    return;
                }}

                try {{
                    const response = await fetch("/auth_register_submit", {{
                        method: "POST",
                     
