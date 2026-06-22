import os
import sys
import logging
import getpass # Para input de senha seguro

import firebase_admin
from firebase_admin import credentials, db

# --- CONFIGURAÇÃO INICIAL ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# --- Configuração do Firebase ---
FIREBASE_CREDENTIALS_PATH = "serviceAccountKey.json"
FIREBASE_DATABASE_URL = "https://project-revival-29e2b-default-rtdb.firebaseio.com" # Substitua pelo URL do seu Realtime Database

try:
    if not firebase_admin._apps:
        if os.path.exists(FIREBASE_CREDENTIALS_PATH):
            cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
            firebase_admin.initialize_app(cred, {
                'databaseURL': FIREBASE_DATABASE_URL
            })
            logging.info("Firebase inicializado com sucesso no gerenciador.")
        else:
            logging.error(f"ERRO: Arquivo {FIREBASE_CREDENTIALS_PATH} não encontrado! O gerenciador não funcionará.")
            sys.exit(1)
except Exception as e:
    logging.error(f"Erro fatal na inicialização do Firebase no gerenciador: {e}")
    sys.exit(1)

# --- Funções de Gerenciamento de Usuários ---
def get_user_data(username):
    try:
        user_ref = db.reference(f'/users/{username}')
        return user_ref.get()
    except Exception as e:
        logging.error(f"Erro ao buscar dados do usuário {username}: {e}")
        return None

def set_user_data(username, data):
    try:
        user_ref = db.reference(f'/users/{username}')
        user_ref.set(data)
        return True
    except Exception as e:
        logging.error(f"Erro ao definir dados do usuário {username}: {e}")
        return False

def update_user_data(username, data):
    try:
        user_ref = db.reference(f'/users/{username}')
        user_ref.update(data)
        return True
    except Exception as e:
        logging.error(f"Erro ao atualizar dados do usuário {username}: {e}")
        return False

def delete_user(username):
    try:
        user_ref = db.reference(f'/users/{username}')
        user_ref.delete()
        return True
    except Exception as e:
        logging.error(f"Erro ao deletar usuário {username}: {e}")
        return False

def list_all_users():
    try:
        users_ref = db.reference('/users')
        return users_ref.get()
    except Exception as e:
        logging.error(f"Erro ao listar usuários: {e}")
        return None

# --- Funções de Validação e Ações ---
def validate_login(username, password):
    user_data = get_user_data(username)
    if user_data:
        if user_data.get('password') == password:
            print(f"\n✅ Login bem-sucedido para o usuário: {username}")
            print("--- Detalhes do Usuário ---")
            for key, value in user_data.items():
                print(f"  {key}: {value}")
            return True
        else:
            print(f"\n❌ Senha incorreta para o usuário: {username}")
    else:
        print(f"\n❌ Usuário não encontrado: {username}")
    return False

def create_new_user(username, password, diamonds=5000, gold=10000, items="1001,1002"):
    if get_user_data(username):
        print(f"\n❌ Erro: Usuário '{username}' já existe.")
        return False
    
    new_user_data = {
        "username": username,
        "password": password, # ATENÇÃO: Em produção, use hashing de senha!
        "diamonds": diamonds,
        "gold": gold,
        "items": items
    }
    if set_user_data(username, new_user_data):
        print(f"\n✅ Usuário '{username}' criado com sucesso!")
        return True
    else:
        print(f"\n❌ Erro ao criar usuário '{username}'.")
        return False

def update_user_resources(username, resource_type, amount):
    user_data = get_user_data(username)
    if not user_data:
        print(f"\n❌ Usuário '{username}' não encontrado.")
        return False
    
    try:
        amount = int(amount)
        current_amount = user_data.get(resource_type, 0)
        new_amount = current_amount + amount
        if new_amount < 0: # Evitar valores negativos para recursos
            print(f"\n❌ Não é possível deixar '{resource_type}' negativo. Valor atual: {current_amount}")
            return False

        if update_user_data(username, {resource_type: new_amount}):
            print(f"\n✅ '{resource_type}' de '{username}' atualizado para {new_amount} (anterior: {current_amount}).")
            return True
        else:
            print(f"\n❌ Erro ao atualizar '{resource_type}' para '{username}'.")
            return False
    except ValueError:
        print(f"\n❌ Quantidade inválida para '{resource_type}'. Deve ser um número inteiro.")
        return False

# --- Interface de Linha de Comando (CLI) ---
def main():
    print("\n--- Gerenciador de Servidor Revival (Firebase) ---")
    print("Certifique-se de que 'serviceAccountKey.json' está na mesma pasta.")

    while True:
        print("\nOpções:")
        print("  1. Validar Login")
        print("  2. Listar Todos os Usuários")
        print("  3. Ver Detalhes de um Usuário")
        print("  4. Criar Novo Usuário")
        print("  5. Atualizar Diamantes de um Usuário")
        print("  6. Atualizar Ouro de um Usuário")
        print("  7. Deletar Usuário")
        print("  0. Sair")

        choice = input("Escolha uma opção: ").strip()

        if choice == '1':
            username = input("Username: ").strip()
            password = getpass.getpass("Senha: ").strip()
            validate_login(username, password)
        elif choice == '2':
            users = list_all_users()
            if users:
                print("\n--- Todos os Usuários ---")
                for username_key, user_data in users.items():
                    print(f"  - {username_key} (Diamantes: {user_data.get('diamonds', 0)}, Ouro: {user_data.get('gold', 0)})")
            else:
                print("Nenhum usuário encontrado.")
        elif choice == '3':
            username = input("Username do usuário para ver detalhes: ").strip()
            user_data = get_user_data(username)
            if user_data:
                print(f"\n--- Detalhes de '{username}' ---")
                for key, value in user_data.items():
                    print(f"  {key}: {value}")
            else:
                print(f"Usuário '{username}' não encontrado.")
        elif choice == '4':
            username = input("Novo Username: ").strip()
            password = getpass.getpass("Nova Senha: ").strip()
            create_new_user(username, password)
        elif choice == '5':
            username = input("Username do usuário: ").strip()
            amount = input("Quantidade de diamantes para adicionar/remover (ex: 1000 ou -500): ").strip()
            update_user_resources(username, 'diamonds', amount)
        elif choice == '6':
            username = input("Username do usuário: ").strip()
            amount = input("Quantidade de ouro para adicionar/remover (ex: 1000 ou -500): ").strip()
            update_user_resources(username, 'gold', amount)
        elif choice == '7':
            username = input("Username do usuário para deletar: ").strip()
            confirm = input(f"Tem certeza que deseja deletar '{username}'? (s/N): ").strip().lower()
            if confirm == 's':
                if delete_user(username):
                    print(f"\n✅ Usuário '{username}' deletado com sucesso.")
                else:
                    print(f"\n❌ Erro ao deletar usuário '{username}'.")
            else:
                print("Operação cancelada.")
        elif choice == '0':
            print("Saindo do gerenciador.")
            break
        else:
            print("Opção inválida. Tente novamente.")

if __name__ == "__main__":
    main()
      
