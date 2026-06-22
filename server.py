import os
import logging
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, db

# --- CONFIGURAÇÃO ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
app = Flask(__name__)
app.config["SECRET_KEY"] = "revival_final_key_999"
CORS(app)

# URL do seu Database
DB_URL = "https://project-revival-29e2b-default-rtdb.firebaseio.com"

# --- CONFIGURAÇÃO MANUAL DO FIREBASE (SUBSTITUA OS VALORES ABAIXO) ---
# Abra seu serviceAccountKey.json e preencha aqui para não depender de arquivo externo
firebase_config = {
  "type": "service_account",
  "project_id": "project-revival-29e2b",
  "private_key_id": "eefd18bd03bb13f1303a4a7d99c1fd629bad7e02",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDEiWzSV7BWO1Qi\nLJig7E8ToFyLjf5GeBWjA3ySEkuavCo4sqxUj02GKn8AKgX796W1oR58TyEnJaAc\nQK3fAwIyjh4eU17SlgUwX+IFG5lwBwi6lUYjRGxP3KHFu10JRd9ClfSV7AYerJ7v\nTVZmrWj89FsvE5KA4Zq/5gTh5eRsBswMq6y/YUD3/592J1RfmZ9z+3gqyJk9K5Vi\nIp44/V41PqAg6S0B7yq3xxOpuM5BBy3DY4NGKuV9PXnscnzs1+NM4WAi1Cd2ZDDc\nDB137oJ3qP8egXLINo6kpangsd9EY6BKF4D7DqItysHpHTmH8+kr6zVeP6yoT5VC\nOzZANu9NAgMBAAECggEAAowrenCDiyKavRSp59AYWE9IU9DD3oL4+NN3Pmd5Tmio\n/XIndLMk1JvhaI2i5Ti5D6kmfYMDEYBV2nfmKRFfamtYLZl0DbO/Hnjns5w/eWnF\n7bE4pwVgiAp6mFcM5i1fLvxFntnf3G7tYnm0qIEP7tN2CR6uU/hYqqsfHhR+SP4p\nvZJHuAm7/aVz/QhC70KaaqOGOyyIi2no+2kl1iPwtWhGpnd8/HvhvbMb1E7XSBqu\nVLsTN5dc8xW5hHRy66S2HE8mi9HN6ZKuDRtgK13dv32+dBXRASccTpRnHoSjImBw\nEYlXXun9OaWLa2S7hqpp7j30HSdUTo/gPI5PXbNysQKBgQDrVk79nSMcKQUV3xzz\nhx1mZTckFc5XGmhQBbWaamKY8VRF+NiHLLZ0uiXB5pc0+K7NU+6gw/k9IhRiCNL1\n9wRaP/N1gGkv2XF4GJUrb3XAPBGd2IzjOfCDJLHhW0YbeIYFGnkenUHfS6lHxcCg\n+mxOxL2povqh35omz75rQ8GViQKBgQDVyv+hBmGx4MaDaqqOy6qT/lxmjjFXGIfI\n9LiUhUrOgKSSSSwVy1ENgmv4li2gOvI8wGX7xaxL2y7wW5J0s1aMNWH7N8ieTHV4\nykRiqpbcCp+vEvH4418RxVnh29UKws2mpSyAH5zN14CIxb7cie58haZIC5j7JXh3\nz0pW9i+epQKBgGDxk+aLdawjBbJFz5JOJYFJzpYx2WcuPKxCPdYXXvhr6XBNmzzL\n4XliOS2QBNfQXYm9un5FXIWfZVAhHG4wTH20/GB5/lq0szZqwgA7kQEYfZVNYHQ2\nKOqNEi2oQNAOLP8rMZu34ivO6jPjtX9ayYUFLLAVsDNAfirgxys+pR8pAoGAevbc\n/IKtIiAETYXGP4dIvwInpxzVqCCFyMFogJQBqLA496J6ZragEcMX0sydxXDh7qtC\nfQL+zEpuvvQMUm7rsozppBI7o0CauDSuDInNZxX9LjcZUWuFPLVjsxI7gIr2uYh7\nBd4o1APE++WwlywGLTy5nOp+vMSae16QhV/nl7kCgYEApsGhL5DzMtsG6G7TxA39\nfpt2+Vm/gYKyJQnrQ+OnXr2r8VQm7a+0UD9i9L7U0eOY/tfVIln00NKg82mBmm0c\nX+DRunpSZT9hCzuzvVBWVFpZk6mdIgVOLpnfJm5c6hBSmtgkwaVQewpounQjv/cJ\nrrquGdxdlW+TVSgSEgfJ3Zk=\n-----END PRIVATE KEY-----\n",
  "client_email": "firebase-adminsdk-fbsvc@project-revival-29e2b.iam.gserviceaccount.com",
  "client_id": "117277650859934457522",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40project-revival-29e2b.iam.gserviceaccount.com"
}

firebase_status = "Aguardando configuração..."

try:
    if not firebase_admin._apps:
        # Tenta carregar do dicionário acima se preenchido, senão tenta do arquivo
        if firebase_config["private_key"] != "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDEiWzSV7BWO1Qi\nLJig7E8ToFyLjf5GeBWjA3ySEkuavCo4sqxUj02GKn8AKgX796W1oR58TyEnJaAc\nQK3fAwIyjh4eU17SlgUwX+IFG5lwBwi6lUYjRGxP3KHFu10JRd9ClfSV7AYerJ7v\nTVZmrWj89FsvE5KA4Zq/5gTh5eRsBswMq6y/YUD3/592J1RfmZ9z+3gqyJk9K5Vi\nIp44/V41PqAg6S0B7yq3xxOpuM5BBy3DY4NGKuV9PXnscnzs1+NM4WAi1Cd2ZDDc\nDB137oJ3qP8egXLINo6kpangsd9EY6BKF4D7DqItysHpHTmH8+kr6zVeP6yoT5VC\nOzZANu9NAgMBAAECggEAAowrenCDiyKavRSp59AYWE9IU9DD3oL4+NN3Pmd5Tmio\n/XIndLMk1JvhaI2i5Ti5D6kmfYMDEYBV2nfmKRFfamtYLZl0DbO/Hnjns5w/eWnF\n7bE4pwVgiAp6mFcM5i1fLvxFntnf3G7tYnm0qIEP7tN2CR6uU/hYqqsfHhR+SP4p\nvZJHuAm7/aVz/QhC70KaaqOGOyyIi2no+2kl1iPwtWhGpnd8/HvhvbMb1E7XSBqu\nVLsTN5dc8xW5hHRy66S2HE8mi9HN6ZKuDRtgK13dv32+dBXRASccTpRnHoSjImBw\nEYlXXun9OaWLa2S7hqpp7j30HSdUTo/gPI5PXbNysQKBgQDrVk79nSMcKQUV3xzz\nhx1mZTckFc5XGmhQBbWaamKY8VRF+NiHLLZ0uiXB5pc0+K7NU+6gw/k9IhRiCNL1\n9wRaP/N1gGkv2XF4GJUrb3XAPBGd2IzjOfCDJLHhW0YbeIYFGnkenUHfS6lHxcCg\n+mxOxL2povqh35omz75rQ8GViQKBgQDVyv+hBmGx4MaDaqqOy6qT/lxmjjFXGIfI\n9LiUhUrOgKSSSSwVy1ENgmv4li2gOvI8wGX7xaxL2y7wW5J0s1aMNWH7N8ieTHV4\nykRiqpbcCp+vEvH4418RxVnh29UKws2mpSyAH5zN14CIxb7cie58haZIC5j7JXh3\nz0pW9i+epQKBgGDxk+aLdawjBbJFz5JOJYFJzpYx2WcuPKxCPdYXXvhr6XBNmzzL\n4XliOS2QBNfQXYm9un5FXIWfZVAhHG4wTH20/GB5/lq0szZqwgA7kQEYfZVNYHQ2\nKOqNEi2oQNAOLP8rMZu34ivO6jPjtX9ayYUFLLAVsDNAfirgxys+pR8pAoGAevbc\n/IKtIiAETYXGP4dIvwInpxzVqCCFyMFogJQBqLA496J6ZragEcMX0sydxXDh7qtC\nfQL+zEpuvvQMUm7rsozppBI7o0CauDSuDInNZxX9LjcZUWuFPLVjsxI7gIr2uYh7\nBd4o1APE++WwlywGLTy5nOp+vMSae16QhV/nl7kCgYEApsGhL5DzMtsG6G7TxA39\nfpt2+Vm/gYKyJQnrQ+OnXr2r8VQm7a+0UD9i9L7U0eOY/tfVIln00NKg82mBmm0c\nX+DRunpSZT9hCzuzvVBWVFpZk6mdIgVOLpnfJm5c6hBSmtgkwaVQewpounQjv/cJ\nrrquGdxdlW+TVSgSEgfJ3Zk=\n-----END PRIVATE KEY-----\n":
            cred = credentials.Certificate(firebase_config)
            firebase_admin.initialize_app(cred, {'databaseURL': DB_URL})
            firebase_status = "Conectado via Código"
        elif os.path.exists("serviceAccountKey.json"):
            cred = credentials.Certificate("serviceAccountKey.json")
            firebase_admin.initialize_app(cred, {'databaseURL': DB_URL})
            firebase_status = "Conectado via Arquivo"
        else:
            firebase_status = "Erro: Configure o dicionário firebase_config no server.py"
except Exception as e:
    firebase_status = f"Erro: {str(e)}"

# --- FUNÇÕES ---
def get_user(u):
    try: return db.reference(f'/users/{u}').get()
    except: return "ERR"

def save_user(u, d):
    try:
        db.reference(f'/users/{u}').set(d)
        return True
    except: return False

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
        u, p = data.get("username"), data.get("pass")
        redir, state = data.get("redirect_uri"), data.get("state")
        res = get_user(u)
        if res == "ERR": return jsonify({"status":"error", "message":"Erro Firebase"}), 500
        if res and str(res.get("password")) == str(p):
            return jsonify({"status":"success", "redirect": f"{redir}#access_token=OK&state={state}"})
        return jsonify({"status":"error", "message":"Usuário/Senha incorretos"}), 401

    if path == "auth_register_submit":
        data = request.form
        u, p, cp = data.get("username"), data.get("pass"), data.get("confirm_pass")
        if p != cp: return jsonify({"status":"error", "message":"Senhas diferentes"}), 400
        if get_user(u) not in [None, "ERR"]: return jsonify({"status":"error", "message":"Já existe"}), 409
        if save_user(u, {"username":u, "password":p, "diamonds":5000, "gold":10000}):
            return jsonify({"status":"success", "message":"Criado!"})
        return jsonify({"status":"error", "message":"Erro ao salvar"}), 500

    if path == "admin/users":
        try: return jsonify({"status":"success", "users": db.reference('/users').get() or {}})
        except: return jsonify({"status":"error"}), 500

    return jsonify({"status":"success", "msg":"Online"}), 200

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
            .box { background: #111; border: 2px solid #f00; padding: 25px; border-radius: 15px; width: 300px; text-align: center; box-shadow: 0 0 20px #f00; }
            input { width: 100%; box-sizing: border-box; padding: 12px; margin: 10px 0; background: #222; border: 1px solid #444; border-radius: 8px; color: #fff; text-align: center; font-family: 'Orbitron'; }
            button { width: 100%; padding: 12px; background: #f00; border: none; border-radius: 8px; color: #fff; font-weight: bold; cursor: pointer; margin-top: 10px; font-family: 'Orbitron'; }
            .tabs { display: flex; margin-bottom: 15px; }
            .tab { flex: 1; padding: 10px; cursor: pointer; color: #555; font-size: 12px; border-bottom: 1px solid #333; }
            .tab.active { color: #fff; border-bottom: 2px solid #f00; }
            .sec { display: none; }
            .sec.active { display: block; }
            #msg { margin-top: 15px; font-size: 11px; color: #f00; min-height: 15px; }
            .st { font-size: 9px; color: #444; margin-top: 10px; }
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
            <div class="st">Status: {{ status }}</div>
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
    
