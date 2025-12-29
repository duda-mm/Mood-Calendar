from app import app, db

with app.app_context():
    print("Apagando tabelas antigas...")
    db.drop_all()  # Apaga tudo
    
    print("Criando tabelas novas com a estrutura atualizada...")
    db.create_all() # Cria tudo de novo, agora com o campo link_musica
    
    print("Banco de dados resetado com sucesso!")