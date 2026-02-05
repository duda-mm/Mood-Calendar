from app import app, db

with app.app_context():
    print("Apagando tabelas antigas...")
    db.drop_all()  
    
    print("Criando tabelas novas com a estrutura atualizada...")
    db.create_all() 
    
    print("Banco de dados resetado com sucesso!")