import os
import json
import logging
import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
import firebase_admin
from firebase_admin import credentials, db, auth

# Configuração de logs para acompanhar os acessos pelo painel do Render
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'revival_secret_key_777!')

# Ativa o SocketIO configurado para rodar com as threads nativas do Gunicorn
socketio = SocketIO(app, cors_allowed_origins="*")

# ==================== CONFIGURAÇÃO DO FIREBASE ====================
if os.environ.get('FIREBASE_CREDENTIALS'):
    try:
        cred_json = json.loads(os.environ.get('FIREBASE_CREDENTIALS'))
        cred = credentials.Certificate(cred_json)
    except Exception as e:
        logging.error(f"Erro ao carregar FIREBASE_CREDENTIALS das variáveis: {e}")
        cred = None
else:
    try:
        cred = credentials.Certificate("credenciais.json")
    except Exception:
        logging.warning("Arquivo credenciais.json nao encontrado localmente.")
        cred = None

if cred:
    try:
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://project-revival-29e2b-default-rtdb.firebaseio.com'
        })
        logging.info("Firebase Admin inicializado com sucesso!")
    except Exception as e:
        logging.error(f"Erro ao inicializar o Firebase: {e}")
else:
    logging.error("Nenhuma credencial do Firebase foi detectada!")

# ==================== ROTAS HTTP (INTERFACES E API) ====================

# Rota Principal - Entrega o index.html usando o caminho absoluto correto do Render
@app.route('/')
def index():
    try:
        diretorio_raiz = os.path.abspath(os.path.dirname(__file__))
        logging.info(f"Servindo index.html a partir de: {diretorio_raiz}")
        return send_from_directory(diretorio_raiz, 'index.html')
    except Exception as e:
        logging.error(f"Erro ao servir o index.html: {e}")
        return f"Erro interno ao carregar a interface: {str(e)}", 500

# Rota de Status - Para você testar direto no navegador se o servidor está vivo
@app.route('/status')
def status():
    return jsonify({
        "status": "online",
        "version": "1.0.0-LOGIN-CORE",
        "timestamp": datetime.datetime.utcnow().isoformat()
    }), 200

# Rota de Login da API do Jogo
@app.route('/api/v1/auth/login', methods=['POST'])
def player_login():
    data = request.get_json() or {}
    email = data.get('email')

    if not email:
        return jsonify({"success": False, "msg": "E-mail ausente."}), 400

    try:
        user = auth.get_user_by_email(email)
        uid = user.uid
        user_ref = db.reference(f'users/{uid}')
        player = user_ref.get()

        if not player:
            return jsonify({"success": False, "msg": "Perfil nao encontrado no servidor."}), 404

        if player.get('banido', False):
            return jsonify({"success": False, "msg": "Acesso Suspenso. Esta conta esta banida."}), 403

        user_ref.update({
            'status': 'online',
            'ultima_conexao': datetime.datetime.utcnow().isoformat()
        })

        return jsonify({
            "success": True,
            "profile": {
                "uid": uid,
                "nick": player.get('nick', 'Recruta'),
                "nivel": player.get('nivel', 1),
                "ouro": player.get('moedas', 0),
                "diamantes": player.get('diamantes', 0)
            }
        }), 200
    except Exception as e:
        logging.error(f"Erro de login para o e-mail {email}: {e}")
        return jsonify({"success": False, "msg": "Erro de Autenticacao.", "error": str(e)}), 401


# ==================== CONTROLE DE ERRO 404 (BLINDAGEM DO APK) ====================

# Se o APK do jogo antigo tentar chamar qualquer link bizarro (ex: index.php, /login, /news)
# o Flask intercepta o erro 404 e abre o seu index.html na tela do jogo de qualquer jeito!
@app.errorhandler(404)
def page_not_found(e):
    try:
        diretorio_raiz = os.path.abspath(os.path.dirname(__file__))
        logging.info(f"APK tentou acessar rota invalida. Redirecionando para index.html")
        return send_from_directory(diretorio_raiz, 'index.html')
    except Exception as err:
        logging.error(f"Erro no redirecionamento do erro 404: {err}")
        return "Erro interno do servidor", 500


# ==================== EVENTOS WEBSOCKET ====================

@socketio.on('connect')
def handle_connect():
    logging.info(f"Jogador conectado via WebSocket: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    logging.info(f"Jogador desconectado do WebSocket: {request.sid}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port)
    
