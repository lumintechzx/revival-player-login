import os
import json
import logging
import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit, join_room, leave_room
import firebase_admin
from firebase_admin import credentials, db, auth

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'revival_secret_key_777!')

# Ativa o SocketIO usando a pool de threads nativas do Gunicorn
socketio = SocketIO(app, cors_allowed_origins="*")

# ==================== CONFIGURAÇÃO FIREBASE ====================
if os.environ.get('FIREBASE_CREDENTIALS'):
    cred_json = json.loads(os.environ.get('FIREBASE_CREDENTIALS'))
    cred = credentials.Certificate(cred_json)
else:
    try:
        cred = credentials.Certificate("credenciais.json")
    except Exception:
        cred = None

if cred:
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://project-revival-29e2b-default-rtdb.firebaseio.com'
    })

# ==================== ROTAS HTTP (INTERFACES E API) ====================

# Rota para renderizar o seu index.html que já está no repositório
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/status')
def status():
    return jsonify({
        "status": "online",
        "version": "1.0.0-LOGIN-CORE"
    }), 200

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
        return jsonify({"success": False, "msg": "Erro de Autenticação.", "error": str(e)}), 401

# ==================== EVENTOS WEBSOCKET ====================

@socketio.on('connect')
def handle_connect():
    logging.info(f"Jogador conectado via WebSocket: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    logging.info(f"Jogador desconectado: {request.sid}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port)
           
