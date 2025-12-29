from app import app, db
from sqlalchemy import text

# Esse script força a criação da coluna titulo na tabela diario
with app.app_context():
    with db.engine.connect() as conn:
        print("🛠️ Tentando criar a coluna 'titulo'...")
        try:
            # Comando SQL direto para adicionar a coluna
            conn.execute(text("ALTER TABLE diario ADD COLUMN titulo VARCHAR(150)"))
            conn.commit()
            print("✅ Sucesso! Coluna 'titulo' criada.")
        except Exception as e:
            # Se der erro, mostramos qual foi
            if 'duplicate column' in str(e) or 'already exists' in str(e):
                print("ℹ️ A coluna já existia. Tudo certo.")
            else:
                print(f"❌ Erro: {e}")