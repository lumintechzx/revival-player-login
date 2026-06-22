import pymysql

def menu():
    print("\n=== GERENCIADOR DE CONTAS (REVIVAL FF) ===")
    print("1. Listar Jogadores Logados")
    print("2. Injetar Diamantes & Ouro")
    print("3. Sair")
    return input("Escolha uma opção: ")

def list_players():
    try:
        conn = pymysql.connect(host='localhost', user='revival_user', password='123456', database='revival_db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, diamonds, gold FROM accounts")
        players = cursor.fetchall()
        print("\nID | Usuário | Diamantes | Ouro")
        print("-" * 40)
        for p in players:
            print(f"{p[0]} | {p[1]} | {p[2]} | {p[3]}")
        conn.close()
    except Exception as e:
        print(f"Erro ao conectar no banco local: {e}")

def add_currency():
    username = input("Digite o nome do usuário: ")
    dimas = input("Quantidade de Diamantes a adicionar: ")
    gold = input("Quantidade de Ouro a adicionar: ")
    try:
        conn = pymysql.connect(host='localhost', user='revival_user', password='123456', database='revival_db')
        cursor = conn.cursor()
        cursor.execute("UPDATE accounts SET diamonds = diamonds + %s, gold = gold + %s WHERE username = %s", (dimas, gold, username))
        conn.commit()
        if cursor.rowcount > 0:
            print(f"💎 Sucesso! Itens injetados para {username}.")
        else:
            print("Usuário não encontrado.")
        conn.close()
    except Exception as e:
        print(f"Erro ao injetar dados: {e}")

if __name__ == '__main__':
    while True:
        op = menu()
        if op == '1': list_players()
        elif op == '2': add_currency()
        elif op == '3': break
          
