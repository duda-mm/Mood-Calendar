from app import app, db
from sqlalchemy import text

with app.app_context():
    with db.engine.connect() as conn:
        print("🔄 Iniciando atualização do banco...")
        
        # 1. Coluna Streak
        try:
            # Note as aspas duplas em "user"
            conn.execute(text('ALTER TABLE "user" ADD COLUMN streak INTEGER DEFAULT 0'))
            print("✅ Coluna 'streak' criada com sucesso.")
        except Exception as e:
            # Se der erro, verificamos se é porque a coluna já existe
            if 'already exists' in str(e):
                print("ℹ️ A coluna 'streak' já existia.")
            else:
                print(f"⚠️ Erro ao criar streak: {e}")

        # 2. Coluna Data do último post
        try:
            conn.execute(text('ALTER TABLE "user" ADD COLUMN last_post_date DATE'))
            print("✅ Coluna 'last_post_date' criada com sucesso.")
        except Exception as e:
            if 'already exists' in str(e):
                print("ℹ️ A coluna 'last_post_date' já existia.")
            else:
                print(f"⚠️ Erro ao criar data: {e}")

        # 3. Coluna XP
        try:
            conn.execute(text('ALTER TABLE "user" ADD COLUMN xp_total INTEGER DEFAULT 0'))
            print("✅ Coluna 'xp_total' criada com sucesso.")
        except Exception as e:
            if 'already exists' in str(e):
                print("ℹ️ A coluna 'xp_total' já existia.")
            else:
                print(f"⚠️ Erro ao criar XP: {e}")

        conn.commit()
        print("🎉 Processo finalizado! Agora seu sistema de gamificação vai funcionar.")