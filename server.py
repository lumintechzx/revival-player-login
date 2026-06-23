import os
import logging
import secrets
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, db

# --- CONFIGURAÇÃO ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
app = Flask(__name__)
app.config["SECRET_KEY"] = secrets.token_hex(16)
CORS(app)

# URL do seu Database
DB_URL = "https://project-revival-29e2b-default-rtdb.firebaseio.com"

# --- CONFIGURAÇÃO MANUAL DO FIREBASE ---
firebase_config = {
  "type": "service_account",
  "project_id": "project-revival-29e2b",
  "private_key_id": "eefd18bd03bb13f1303a4a7d99c1fd629bad7e02",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDEiWzSV7BWO1Qi\nLJig7E8ToFyLjf5GeBWjA3ySEkuavCo4sqxUj02GKn8AKgX796W1oR58TyEnJaAc\nQK3fAwIyjh4eU17SlgUwX+IFG5lwBwi6lUYjRGxP3KHFu10JRd9ClfSV7AYerJ7v\nTVZmrWj89FsvE5KA4Zq/5gTh5eRsBswMq6y/YUD3/592J1RfmZ9z+3gqyJk9K5Vi\nIp44/V41PqAg6S0B7yq3xxOpuM5BBy3DY4NGKuV9PXnscnzs1+NM4WAi1Cd2ZDDc\nDB137oJ3qP8egXLINo6kpangsd9EY6BKF4D7DqItysHpHTmH8+kr6zVeP6yoT5VC\nOzZANu9NAgMBAAECggEAAowrenCDiyKavRSp59AYWE9IU9DD3oL4+NN3Pmd5Tmio\n/XIndLMk1JvhaI2i5Ti5D6kmfYMDEYBV2nfmKRFfamtYLZl0DbO/Hnjns5w/eWnF\n7bE4pwVgiAp6mFcM5i1fLvxFntnf3G7tYnm0qIEP7tN2CR6uU/hYqqsfHhR+SP4p\nvZJHuAm7/aVz/QhC70KaaqOGOyyIi2no+2kl1iPwtWhGpnd8/HvhvbMb1E7XSBqu\nVLsTN5dc8xW5hHRy66S2HE8mi9HN6ZKuDRtgK13dv32+dBXRASccTpRnHoSjImBw\nEYlXXun9OaWLa2S7hqpp7j30HSdUTo/gPI5PXbNysQKBgQDrVk79nSMcKQUV3xzz\nhx1mZTckFc5XGmhQBbWaamKY8VRF+NiHLLZ0uiXB5pc0+K7NU+6gw/k9IhRiCNL1\n9wRaP/N1gGkv2XF4GJUrb3XAPBGd2IzjOfCDJLHhW0YbeIYFGnkenUHfS6lHxcCg\n+mxOxL2povqh35omz75rQ8GViQKBgQDVyv+hBmGx4MaDaqqOy6qT/lxmjjFXGIfI\n9LiUhUrOgKSSSSwVy1ENgmv4li2gOvI8wGX7xaxL2y7wW5J0s1aMNWH7N8ieTHV4\nykRiqpbcCp+vEvH4418RxVnh29UKws2mpSyAH5zN14CIxb7cie58haZIC5j7JXh3\nz0pW9i+epQKBgGDxk+aLdawjBbJFz5JOJYFJzpYx2WcuPKxCPdYXXvhr6XBNmzzL\n4XliOS2QBNfQXYm9un5FXIWfZVAhHG4wTH20/GB5/lq0szZqwgA7kQEYfZVNYHQ2\nKOqNEi2oQNAOLP8rMZu34ivO6jPjtX9ayYUFLLAVsDNAfirgxys+pR8pAoGAevbc\n/IKtIiAETYXGP4dIvwInpxzVqCCFyMFogJQBqLA496J6ZragEcMX0sydxXDh7qtC\nfQL+zEpuvvQMUm7rsozppBI7o0CauDSuDInNZxX9LjcZUWuFPLVjsxI7gIr2uYh7\Bd4o1APE++WwlywGLTy5nOp+vMSae16QhV/nl7kCgYEApsGhL5DzMtsG6G7TxA39\nfpt2+Vm/gYKyJQnrQ+OnXr2r8VQm7a+0UD9i9L7U0eOY/tfVIln00NKg82mBmm0c\nX+DRunpSZT9hCzuzvVBWVFpZk6mdIgVOLpnfJm5c6hBSmtgkwaVQewpounQjv/cJ\nrrquGdxdlW+TVSgSEgfJ3Zk=\n-----END PRIVATE KEY-----\n",
  "client_email": "firebase-adminsdk-fbsvc@project-revival-29e2b.iam.gserviceaccount.com",
  "client_id": "117277650859934457522",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40project-revival-29e2b.iam.gserviceaccount.com"
}

try:
    if not firebase_admin._apps:
        cred = credentials.Certificate(firebase_config)
        firebase_admin.initialize_app(cred, {'databaseURL': DB_URL})
        firebase_status = "Conectado ao Firebase"
except Exception as e:
    firebase_status = f"Erro: {str(e)}"

# --- FUNÇÕES DE BANCO DE DADOS ---
def get_all_users():
    try:
        ref = db.reference('/users')
        return ref.get() or {}
    except: return {}

def update_user_data(username, data):
    try:
        ref = db.reference(f'/users/{username}')
        ref.update(data)
        return True
    except: return False

# --- ROTAS API ---
@app.route("/", methods=["GET"])
def index():
    return render_template_string(get_html(), status=firebase_status)

@app.route("/api/users", methods=["GET"])
def api_list_users():
    return jsonify({"status": "success", "users": get_all_users()})

@app.route("/api/save_config", methods=["POST"])
def api_save_config():
    data = request.json
    username = data.get("username")
    if not username: return jsonify({"status": "error", "message": "Usuário inválido"}), 400
    
    update_fields = {
        "level": data.get("level"),
        "game_name": data.get("game_name"),
        "name_color": data.get("name_color"),
        "diamonds": data.get("diamonds"),
        "gold": data.get("gold"),
        "skin_id": data.get("skin_id")
    }
    
    if update_user_data(username, update_fields):
        return jsonify({"status": "success", "message": "Configurações salvas!"})
    return jsonify({"status": "error", "message": "Erro ao salvar no Firebase"}), 500

@app.route("/api/set_ban", methods=["POST"])
def api_set_ban():
    data = request.json
    username = data.get("username")
    is_banned = data.get("is_banned", False)
    if update_user_data(username, {"is_banned": is_banned}):
        return jsonify({"status": "success", "message": "Status de banimento atualizado!"})
    return jsonify({"status": "error", "message": "Erro ao atualizar banimento"}), 500

# --- HTML INTERFACE ---
def get_html():
    return """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>REVIVAL PANEL PRO</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@500;700&display=swap');
            :root { --primary: #ff0000; --bg: #050505; --card-bg: #111; --text: #eee; }
            body { background: var(--bg); color: var(--text); font-family: 'Rajdhani', sans-serif; overflow-x: hidden; }
            h1, h2, h3, .nav-link { font-family: 'Orbitron', sans-serif; }
            
            .sidebar { height: 100vh; background: #000; border-right: 1px solid #222; position: fixed; width: 240px; padding: 20px 0; z-index: 100; }
            .sidebar-brand { text-align: center; color: var(--primary); font-size: 24px; font-weight: bold; margin-bottom: 40px; text-shadow: 0 0 10px rgba(255,0,0,0.5); }
            .nav-link { color: #666; padding: 12px 25px; margin: 5px 15px; border-radius: 8px; transition: 0.3s; cursor: pointer; display: flex; align-items: center; font-size: 14px; }
            .nav-link i { margin-right: 12px; font-size: 18px; }
            .nav-link:hover, .nav-link.active { color: #fff; background: rgba(255,0,0,0.1); border-left: 4px solid var(--primary); }
            .nav-link.active { background: var(--primary); box-shadow: 0 0 20px rgba(255,0,0,0.3); border-left: none; }
            
            .main-content { margin-left: 240px; padding: 40px; }
            .card { background: var(--card-bg); border: 1px solid #222; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); margin-bottom: 25px; }
            .card-header { background: transparent; border-bottom: 1px solid #222; padding: 20px; font-weight: bold; color: var(--primary); }
            
            .btn-revival { background: var(--primary); color: #fff; border: none; padding: 10px 25px; border-radius: 8px; font-weight: bold; text-transform: uppercase; transition: 0.3s; }
            .btn-revival:hover { background: #cc0000; box-shadow: 0 0 15px var(--primary); transform: translateY(-2px); }
            
            input, select { background: #1a1a1a !important; border: 1px solid #333 !important; color: #fff !important; padding: 12px !important; border-radius: 8px !important; }
            input:focus { border-color: var(--primary) !important; box-shadow: 0 0 10px rgba(255,0,0,0.2) !important; }
            
            .table { color: #ccc; border-collapse: separate; border-spacing: 0 10px; }
            .table thead th { border: none; color: #555; text-transform: uppercase; font-size: 12px; }
            .table tbody tr { background: #161616; transition: 0.2s; }
            .table tbody tr:hover { transform: scale(1.01); background: #1a1a1a; }
            .table td { padding: 15px; border: none; vertical-align: middle; }
            .table td:first-child { border-radius: 10px 0 0 10px; }
            .table td:last-child { border-radius: 0 10px 10px 0; }
            
            .badge-status { padding: 5px 12px; border-radius: 20px; font-size: 11px; font-weight: bold; }
            .bg-active { background: rgba(0,255,0,0.1); color: #00ff00; border: 1px solid #00ff00; }
            .bg-banned { background: rgba(255,0,0,0.1); color: #ff0000; border: 1px solid #ff0000; }
            
            .token-text { font-family: monospace; color: #666; font-size: 12px; background: #000; padding: 4px 8px; border-radius: 4px; }
            
            #loader { position: fixed; top: 0; right: 20px; padding: 10px; color: var(--primary); display: none; }
        </style>
    </head>
    <body>
        <div id="loader"><i class="fas fa-sync fa-spin"></i> SINCRONIZANDO...</div>
        
        <div class="sidebar">
            <div class="sidebar-brand">REVIVAL PRO</div>
            <div class="nav flex-column">
                <div class="nav-link active" onclick="switchTab('contas', this)"><i class="fas fa-users"></i> CONTAS</div>
                <div class="nav-link" onclick="switchTab('config', this)"><i class="fas fa-cogs"></i> CONFIG</div>
                <div class="nav-link" onclick="switchTab('banidos', this)"><i class="fas fa-user-slash"></i> BANIDOS</div>
            </div>
            <div style="position: absolute; bottom: 20px; width: 100%; text-align: center; font-size: 10px; color: #333;">
                FIREBASE: {{ status }}
            </div>
        </div>

        <div class="main-content">
            <!-- TAB CONTAS -->
            <div id="tab-contas" class="tab-pane">
                <div class="d-flex justify-content-between align-items-center mb-4">
                    <h3>Gerenciamento de Contas</h3>
                    <button class="btn btn-revival btn-sm" onclick="loadData()"><i class="fas fa-sync"></i> Atualizar</button>
                </div>
                <div class="card">
                    <div class="table-responsive p-3">
                        <table class="table">
                            <thead>
                                <tr>
                                    <th>Usuário</th>
                                    <th>Senha</th>
                                    <th>Token de Acesso</th>
                                    <th>Status</th>
                                    <th>Ações</th>
                                </tr>
                            </thead>
                            <tbody id="list-contas"></tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- TAB CONFIG -->
            <div id="tab-config" class="tab-pane" style="display:none;">
                <h3>Configurações de Jogo</h3>
                <div class="row mt-4">
                    <div class="col-md-5">
                        <div class="card">
                            <div class="card-header">SELECIONAR CONTA</div>
                            <div class="card-body">
                                <select id="select-user-config" class="form-select mb-3" onchange="fillConfigForm()">
                                    <option value="">Escolha um usuário...</option>
                                </select>
                                <p class="text-muted small">Selecione uma conta para carregar os dados atuais do Firebase.</p>
                            </div>
                        </div>
                        <div class="card">
                            <div class="card-header">DICAS DE SKINS</div>
                            <div class="card-body small text-muted">
                                Utilize os IDs oficiais do Free Fire. <br>
                                Ex: <b>101001</b> (Skin Alok)<br>
                                Ex: <b>202005</b> (Calça Angelical)<br>
                                As alterações são aplicadas instantaneamente no banco de dados.
                            </div>
                        </div>
                    </div>
                    <div class="col-md-7">
                        <div id="config-form-container" class="card" style="opacity: 0.5; pointer-events: none;">
                            <div class="card-header">EDITOR DE ATRIBUTOS</div>
                            <div class="card-body">
                                <div class="row">
                                    <div class="col-md-6 mb-3">
                                        <label class="form-label">Nome no Jogo</label>
                                        <input type="text" id="inp-game-name" class="form-control" placeholder="Ex: Foxyz">
                                    </div>
                                    <div class="col-md-6 mb-3">
                                        <label class="form-label">Cor do Nome</label>
                                        <input type="text" id="inp-name-color" class="form-control" placeholder="Ex: Azul ou #0000FF">
                                    </div>
                                    <div class="col-md-4 mb-3">
                                        <label class="form-label">Nível</label>
                                        <input type="number" id="inp-level" class="form-control">
                                    </div>
                                    <div class="col-md-4 mb-3">
                                        <label class="form-label">Diamantes</label>
                                        <input type="number" id="inp-diamonds" class="form-control">
                                    </div>
                                    <div class="col-md-4 mb-3">
                                        <label class="form-label">Moedas (Gold)</label>
                                        <input type="number" id="inp-gold" class="form-control">
                                    </div>
                                    <div class="col-12 mb-4">
                                        <label class="form-label">ID da Skin (Free Fire)</label>
                                        <input type="text" id="inp-skin-id" class="form-control" placeholder="Insira o ID da Skin">
                                    </div>
                                </div>
                                <button class="btn btn-revival w-100" onclick="saveConfig()">SALVAR ALTERAÇÕES</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- TAB BANIDOS -->
            <div id="tab-banidos" class="tab-pane" style="display:none;">
                <h3>Central de Banimentos</h3>
                <div class="card mt-4">
                    <div class="table-responsive p-3">
                        <table class="table">
                            <thead>
                                <tr>
                                    <th>Usuário</th>
                                    <th>Nome no Jogo</th>
                                    <th>Status Atual</th>
                                    <th>Ação Rápida</th>
                                </tr>
                            </thead>
                            <tbody id="list-banidos"></tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>

        <script>
            let cachedUsers = {};

            function switchTab(tabId, el) {
                document.querySelectorAll('.tab-pane').forEach(t => t.style.display = 'none');
                document.querySelectorAll('.nav-link').forEach(n => n.classList.remove('active'));
                document.getElementById('tab-' + tabId).style.display = 'block';
                el.classList.add('active');
                loadData();
            }

            async function loadData() {
                document.getElementById('loader').style.display = 'block';
                try {
                    const res = await fetch('/api/users');
                    const data = await res.json();
                    if(data.status === 'success') {
                        cachedUsers = data.users;
                        renderContas();
                        renderBanidos();
                        updateSelects();
                    }
                } catch(e) { console.error(e); }
                document.getElementById('loader').style.display = 'none';
            }

            function renderContas() {
                const container = document.getElementById('list-contas');
                container.innerHTML = "";
                for(let u in cachedUsers) {
                    const user = cachedUsers[u];
                    container.innerHTML += `
                        <tr>
                            <td><b>${u}</b></td>
                            <td>${user.password}</td>
                            <td><span class="token-text">${user.token || 'sem-token'}</span></td>
                            <td><span class="badge-status ${user.is_banned ? 'bg-banned' : 'bg-active'}">${user.is_banned ? 'BANIDO' : 'ATIVO'}</span></td>
                            <td><button class="btn btn-sm btn-outline-danger" onclick="editInConfig('${u}')"><i class="fas fa-edit"></i></button></td>
                        </tr>
                    `;
                }
            }

            function renderBanidos() {
                const container = document.getElementById('list-banidos');
                container.innerHTML = "";
                for(let u in cachedUsers) {
                    const user = cachedUsers[u];
                    container.innerHTML += `
                        <tr>
                            <td>${u}</td>
                            <td>${user.game_name || u}</td>
                            <td><b class="text-${user.is_banned ? 'danger' : 'success'}">${user.is_banned ? 'BANIDO' : 'NORMAL'}</b></td>
                            <td>
                                <button class="btn btn-sm ${user.is_banned ? 'btn-success' : 'btn-danger'}" onclick="toggleBan('${u}', ${!user.is_banned})">
                                    ${user.is_banned ? 'RETIRAR BAN' : 'BANIR AGORA'}
                                </button>
                            </td>
                        </tr>
                    `;
                }
            }

            function updateSelects() {
                const select = document.getElementById('select-user-config');
                const current = select.value;
                select.innerHTML = '<option value="">Escolha um usuário...</option>';
                for(let u in cachedUsers) {
                    select.innerHTML += `<option value="${u}">${u}</option>`;
                }
                select.value = current;
            }

            function editInConfig(u) {
                switchTab('config', document.querySelector('[onclick*="config"]'));
                document.getElementById('select-user-config').value = u;
                fillConfigForm();
            }

            function fillConfigForm() {
                const u = document.getElementById('select-user-config').value;
                const form = document.getElementById('config-form-container');
                if(!u) { form.style.opacity = "0.5"; form.style.pointerEvents = "none"; return; }
                
                form.style.opacity = "1";
                form.style.pointerEvents = "all";
                const user = cachedUsers[u];
                document.getElementById('inp-game-name').value = user.game_name || "";
                document.getElementById('inp-name-color').value = user.name_color || "";
                document.getElementById('inp-level').value = user.level || 0;
                document.getElementById('inp-diamonds').value = user.diamonds || 0;
                document.getElementById('inp-gold').value = user.gold || 0;
                document.getElementById('inp-skin-id').value = user.skin_id || "";
            }

            async function saveConfig() {
                const u = document.getElementById('select-user-config').value;
                const payload = {
                    username: u,
                    game_name: document.getElementById('inp-game-name').value,
                    name_color: document.getElementById('inp-name-color').value,
                    level: parseInt(document.getElementById('inp-level').value),
                    diamonds: parseInt(document.getElementById('inp-diamonds').value),
                    gold: parseInt(document.getElementById('inp-gold').value),
                    skin_id: document.getElementById('inp-skin-id').value
                };

                const res = await fetch('/api/save_config', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                alert(data.message);
                loadData();
            }

            async function toggleBan(u, status) {
                if(!confirm(`Confirmar ação para o usuário ${u}?`)) return;
                const res = await fetch('/api/set_ban', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({username: u, is_banned: status})
                });
                loadData();
            }

            // Init
            loadData();
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
