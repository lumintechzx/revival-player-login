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

# --- CONFIGURAÇÃO MANUAL DO FIREBASE ---
firebase_config = {
  "type": "service_account",
  "project_id": "project-revival-29e2b",
  "private_key_id": "1d6a87ec5530db69b417215151090bd34b21bb90",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC/3/FOmBq9AQnE\nLzgLyjMlDIgP+Ntj0JpiaPvfp7kYa8lJsbd3Gf23VH+kJzoJviFE/NAF2QGUssi3\nPr3EdzWxZ0KNtj4abxXhXyK91Fv091dAhDm36iWDdUGK/aXWYmTqHbSKorCNAEEt\ns5EXoiDiY6ekuQzxD8d2jJZA86X+xWc5G+wSYljFWfGUZupmFGEDvya7BTPN6g7l\nIgDKRNlE702kMIExckZSlRV1YgBno2YNQJuMzBAXS+bwnD3CFop88X8bEa7yvHEK\n1dKp9+zzL5M/Zdiy3bE9jTQfYAuybIqk6BUnONd+IAuzigMXBzoHKrkgS+37t4ex\n6l0ARdx9AgMBAAECggEAXj4C2n0YKPxBDUS6DQRoIYrpq5qqO3kC01JIYF6TqdyL\nNfCdsdioxyqwNPL1bUKfObDJBg5D2gMEVgjxkXWSAEw9IrjAASDNyO/+8ulCr2vr\nRauMY/qUKWDm6/tQwJ98fIdRnYRyHhdhbC6WFdsSts+G0H/5zM9Yw7Aivs1Nm3gE\n30KT1gzlhEjjuMkLYQz8D++lZi0CNZ8XQqI2WqdcnovPlR0cRV3ywf8i15rHMIU8\nnwugvVPXekj16AHc5gptz/lS7I+yTxkBOy0KJ3uVF9n7Gp27jwvBA/A/0EqnnjME\nW5ePaE5Fw/ogwOOqONMlRNfjLmYqw2ENiRJvTBpl6wKBgQDspiRgSXv7E586914O\nG3M9ruk2RmXTfEP/AYD7f8xIvuXTywuSCTz9BD0B4tlA6AkGVI0qpGd1jxJ6v0Wr\nEClP8mTrbx7E+EJ9a1SuvOgmyN/Zv8e64WL4i4Fcbbb261I5tbOZqSR+fz8re8Ct\nhg6alFgTSSxpY6VHuqYvt7uSEwKBgQDPkIadMVHUPiaJ67HVpWesZHISbokMpDSU\nPFLvZ9PPXTsxSVmqtuzcu8HIpGdEmIs+DPXBCqZDrW2xCpDNC9bwF0NDiP+3F+lb\nd3emX5Pb+gVTVrWOZ8NOoEcBlOQeyaJ9QlBCBqAchQ6DAn6kxv0FImrxFqLe7Djx\nASXlsespLwKBgFb3J18LIji+mUF+Ll5Y0BzW7nU3oav6erJ3xwKlkFkbbjJK59Ge\n+36v1AuhZd1oaAifgdEt4adeEJhzOhMHOWdb2KJ8j34rDaQxkUk1usql/z1yMOAI\ne+qCueNRnm9XQzxZ/cp2Uib6dChyrfgWz78WzNcpiNyh9ddKTFA04QVpAoGBAMCK\n9vS2nYvfI2zpgQwI5cUbYF4Mv4FEianA08ZVcDx55cDwpAcirVKNsVNofos5XmFv\nMEGkmVtKc+i5Pl2XUAlj6vepDF1SBxzcE9f37Xcv1OTcGItDYf972qJy9bJBpUPA\n0iaNctVB8JZDKCu+k1PB+6YtM2TLiH64a+lJRDXtAoGAYH+l0fYiFEmzeIL8pyMQ\nL+Pb7nOiUjjiJELf9vXDfE8XJvepRrY5ciLJOye14cykwqPnOPR52V3mrPvkWHqK\nWCZVAeVBbAvIc9V7zEvevgfReN/u2Z+uba3eaiRZlHU8tlarvhC6UA/QCUMOs3XS\nTGN4jgLS/Oj4yLJYIwnERSU=\n-----END PRIVATE KEY-----\n",
  "client_email": "firebase-adminsdk-fbsvc@project-revival-29e2b.iam.gserviceaccount.com",
  "client_id": "117277650859934457522",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40project-revival-29e2b.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}

firebase_status = "Iniciando..."

try:
    if not firebase_admin._apps:
        cred = credentials.Certificate(firebase_config)
        firebase_admin.initialize_app(cred, {'databaseURL': DB_URL})
        firebase_status = "Celestial Link Active"
except Exception as e:
    firebase_status = f"Connection Lost: {str(e)}"

# --- FUNÇÕES ---
def get_user(u):
    try:
        safe_u = u.replace(".", "_").replace("@", "_")
        return db.reference(f'/users/{safe_u}').get()
    except: return "ERR"

def save_user(u, d):
    try:
        safe_u = u.replace(".", "_").replace("@", "_")
        db.reference(f'/users/{safe_u}').set(d)
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
        if res == "ERR": return jsonify({"status":"error", "message":"Celestial Error"}), 500
        if res and str(res.get("password")) == str(p):
            return jsonify({"status":"success", "redirect": f"{redir}#access_token=OK&state={state}"})
        return jsonify({"status":"error", "message":"Invalid Credentials"}), 401

    if path == "auth_register_submit":
        data = request.form
        u, p, cp = data.get("username"), data.get("pass"), data.get("confirm_pass")
        if p != cp: return jsonify({"status":"error", "message":"Passwords mismatch"}), 400
        if get_user(u) not in [None, "ERR"]: return jsonify({"status":"error", "message":"Entity exists"}), 409
        if save_user(u, {"username":u, "password":p, "diamonds":5000, "gold":10000}):
            return jsonify({"status":"success", "message":"Ascended!"})
        return jsonify({"status":"error", "message":"Ascension failed"}), 500

    if path == "admin/users":
        try: return jsonify({"status":"success", "users": db.reference('/users').get() or {}})
        except: return jsonify({"status":"error"}), 500

    return jsonify({"status":"success", "msg":"Celestial Online"}), 200

def get_html():
    return """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Celestial Revival</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&family=Montserrat:wght@200;400&display=swap');
            
            * { margin: 0; padding: 0; box-sizing: border-box; }
            
            body { 
                background: radial-gradient(circle at center, #1a1a1a 0%, #000 100%); 
                color: #fff; 
                font-family: 'Montserrat', sans-serif; 
                display: flex; 
                justify-content: center; 
                align-items: center; 
                height: 100vh; 
                overflow: hidden;
            }

            /* Estrelas de fundo */
            .stars { position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; background: transparent url('https://www.transparenttextures.com/patterns/stardust.png') repeat; opacity: 0.3; }

            .container { 
                position: relative;
                background: rgba(10, 10, 10, 0.8); 
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.1); 
                padding: 40px; 
                border-radius: 2px; 
                width: 360px; 
                text-align: center; 
                box-shadow: 0 0 50px rgba(0, 0, 0, 1), 0 0 20px rgba(255, 255, 255, 0.05);
                z-index: 10;
            }

            /* O "C" Celestial */
            .logo-c {
                font-family: 'Cinzel', serif;
                font-size: 80px;
                font-weight: 700;
                color: #fff;
                line-height: 1;
                margin-bottom: 10px;
                position: relative;
                display: inline-block;
                text-shadow: 0 0 15px rgba(255, 255, 255, 0.5);
            }
            .logo-c::before {
                content: '';
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                width: 120px;
                height: 120px;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 50%;
                z-index: -1;
                animation: rotate 10s linear infinite;
            }
            .logo-c::after {
                content: '';
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                width: 140px;
                height: 140px;
                border: 1px dashed rgba(255, 255, 255, 0.1);
                border-radius: 50%;
                z-index: -1;
                animation: rotate-rev 15s linear infinite;
            }

            @keyframes rotate { from { transform: translate(-50%, -50%) rotate(0deg); } to { transform: translate(-50%, -50%) rotate(360deg); } }
            @keyframes rotate-rev { from { transform: translate(-50%, -50%) rotate(360deg); } to { transform: translate(-50%, -50%) rotate(0deg); } }

            h2 { font-family: 'Cinzel', serif; font-size: 14px; letter-spacing: 8px; margin-bottom: 30px; color: rgba(255, 255, 255, 0.7); font-weight: 400; }

            .tabs { display: flex; margin-bottom: 25px; border-bottom: 1px solid rgba(255, 255, 255, 0.05); }
            .tab { flex: 1; padding: 12px; cursor: pointer; color: #444; font-size: 10px; letter-spacing: 2px; transition: 0.4s; font-weight: 700; }
            .tab.active { color: #fff; border-bottom: 1px solid #fff; }

            .sec { display: none; animation: fadeIn 0.5s ease; }
            .sec.active { display: block; }
            @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

            .input-group { margin-bottom: 15px; position: relative; }
            input { 
                width: 100%; 
                background: transparent; 
                border: none; 
                border-bottom: 1px solid rgba(255, 255, 255, 0.1); 
                padding: 12px 5px; 
                color: #fff; 
                font-family: 'Montserrat', sans-serif; 
                font-size: 12px; 
                outline: none; 
                transition: 0.3s;
                letter-spacing: 1px;
            }
            input:focus { border-bottom: 1px solid #fff; }
            input::placeholder { color: #333; font-size: 10px; letter-spacing: 2px; text-transform: uppercase; }

            button { 
                width: 100%; 
                padding: 15px; 
                background: #fff; 
                border: none; 
                color: #000; 
                font-family: 'Cinzel', serif; 
                font-weight: 700; 
                font-size: 12px; 
                letter-spacing: 3px; 
                cursor: pointer; 
                margin-top: 20px; 
                transition: 0.4s;
                position: relative;
                overflow: hidden;
            }
            button:hover { background: #000; color: #fff; box-shadow: 0 0 20px rgba(255, 255, 255, 0.2); }

            #msg { margin-top: 20px; font-size: 10px; letter-spacing: 1px; color: #fff; min-height: 15px; text-transform: uppercase; }
            
            .footer { margin-top: 30px; font-size: 8px; color: #222; letter-spacing: 2px; text-transform: uppercase; }
            
            /* Admin List Style */
            #list { max-height: 120px; overflow-y: auto; text-align: left; font-size: 9px; padding: 10px; border: 1px solid rgba(255, 255, 255, 0.05); }
            #list div { padding: 5px 0; border-bottom: 1px solid rgba(255, 255, 255, 0.02); color: rgba(255, 255, 255, 0.5); }

            /* Custom Scrollbar */
            ::-webkit-scrollbar { width: 2px; }
            ::-webkit-scrollbar-track { background: transparent; }
            ::-webkit-scrollbar-thumb { background: #333; }
        </style>
    </head>
    <body>
        <div class="stars"></div>
        <div class="container">
            <div class="logo-c">C</div>
            <h2>CELESTIAL</h2>
            
            <div class="tabs">
                <div id="t1" class="tab active" onclick="sw('login')">ENTRY</div>
                <div id="t2" class="tab" onclick="sw('reg')">ASCEND</div>
                <div id="t3" class="tab" onclick="sw('adm')">SOULS</div>
            </div>

            <div id="s-login" class="sec active">
                <div class="input-group"><input id="lu" placeholder="Identifier"></div>
                <div class="input-group"><input id="lp" type="password" placeholder="Keyphrase"></div>
                <button onclick="go('login')">INVOKE</button>
            </div>

            <div id="s-reg" class="sec">
                <div class="input-group"><input id="ru" placeholder="New Identifier"></div>
                <div class="input-group"><input id="rp" type="password" placeholder="New Keyphrase"></div>
                <div class="input-group"><input id="rc" type="password" placeholder="Confirm Keyphrase"></div>
                <button onclick="go('reg')">ASCEND</button>
            </div>

            <div id="s-adm" class="sec">
                <div id="list">Loading souls...</div>
                <button onclick="load()" style="background: transparent; border: 1px solid rgba(255,255,255,0.1); color: #fff; margin-top: 10px;">REFRESH</button>
            </div>

            <div id="msg"></div>
            <div class="footer">Status: {{ status }}</div>
        </div>

        <script>
            const REDIR = "{{ redir }}"; const STATE = "{{ state }}";
            function sw(n){
                document.querySelectorAll('.tab, .sec').forEach(e=>e.classList.remove('active'));
                if(n==='login') document.getElementById('t1').classList.add('active');
                else if(n==='reg') document.getElementById('t2').classList.add('active');
                else { document.getElementById('t3').classList.add('active'); load(); }
                document.getElementById('s-'+n).classList.add('active');
                document.getElementById('msg').innerText = "";
            }
            async function load(){
                const l = document.getElementById('list');
                try {
                    const r = await fetch('/admin/users');
                    const d = await r.json();
                    let h = ""; 
                    for(let k in d.users) h += `<div>• ${d.users[k].username || k}</div>`;
                    l.innerHTML = h || "No souls found";
                } catch(e) { l.innerText = "Connection lost"; }
            }
            async function go(t){
                const m = document.getElementById('msg'); m.innerText = "Synchronizing...";
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
                        else { m.innerText="Ascension Complete"; setTimeout(()=>sw('login'), 1500); }
                    } else { m.innerText = d.message; }
                } catch(e) { m.innerText = "Network Error"; }
            }
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
      
