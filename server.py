import os
import json
import logging
import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
import firebase_admin
from firebase_admin import credentials, db, auth

# Configuração de logs para você acompanhar tudo pelo painel do Render
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'revival_secret_key_777!')

# Ativa o SocketIO pronto para trabalhar com as threads nativas do Gunicorn
socketio = SocketIO(app, cors_allowed_origins="*")

# ==================== CONFIGURAÇÃO FIREBASE ====================
if os.environ.get('FIREBASE_CREDENTIALS'):
    try:
        cred_json = json.loads(os.environ.get('FIREBASE_CREDENTIALS'))
        cred = credentials.Certificate(cred_json)
    except Exception as e:
        logging.error(f"Erro ao carregar FIREBASE_CREDENTIALS das variáveis de ambiente: {e}")
        cred = None
else:
    try:
        cred = credentials.Certificate("credenciais.json")
    except Exception:
        logging.warning("Arquivo credenciais.json não encontrado localmente.")
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

# Rota principal - Serve o index.html usando o caminho absoluto para evitar erro 404/Tela Branca
@app.route('/')
def index():
    try:
        # Pega a pasta exata onde o server.py está rodando no Render
        diretorio_raiz = os.path.abspath(os.path.dirname(__file__))
        logging.info(f"Tentando servir index.html a partir de: {diretorio_raiz}")
        return send_from_directory(diretorio_raiz, 'index.html')
    except Exception as e:
        logging.error(f"Erro ao servir o index.html: {e}")
        return f"Erro interno ao carregar a interface: {str(e)}", 500

# Rota de teste para você verificar se o servidor está respondendo direto pelo navegador
@app.route('/status')
def status():
    return jsonify({
        "status": "online",
        "version": "1.0.0-LOGIN-CORE",
        "timestamp": datetime.datetime.utcnow().isoformat()
    }), 200

# Rota de autenticação da API de login
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
            return jsonify({"success": False, "msg": "Perfil não encontrado no servidor."}), 404

        if player.get('banido', False):
            return jsonify({"success": False, "msg": "Acesso Suspenso. Esta conta está banida."}), 403

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
        return jsonify({"success": False, "msg": "Erro de Autenticação.", "error": str(e)}), 401

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
               
