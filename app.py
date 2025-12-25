from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date

app = Flask(__name__)
app.secret_key = 'segredo_absoluto_life_tracker'

DB_URL = "postgresql://neondb_owner:npg_xfJM2RKW8wVz@ep-divine-block-a45en3kh-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# --- MODELOS (TABELAS) ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    diarios = db.relationship('Diario', backref='autor', lazy=True)
    tags = db.relationship('Tag', backref='dono', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    diarios = db.relationship('Diario', backref='tag', lazy=True)

class Diario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tag_id = db.Column(db.Integer, db.ForeignKey('tag.id'), nullable=True)
    
    data_registro = db.Column(db.Date, nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    nota_dia = db.Column(db.Integer, nullable=False)
    humor_cor = db.Column(db.String(20), nullable=False, default="mediano")
    musica_dia = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- CONTEXTO (BARRA LATERAL) ---
@app.context_processor
def inject_tags():
    if current_user.is_authenticated:
        minhas_tags = Tag.query.filter_by(user_id=current_user.id).all()
        return dict(sidebar_tags=minhas_tags)
    return dict(sidebar_tags=[])

# --- ROTAS ---

@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect('/dashboard')
    # Garante que as tabelas existem ao abrir o site
    with app.app_context():
        db.create_all()
    return render_template('home.html')

@app.route('/dashboard')
@login_required
def dashboard():
    # Filtro de Tags (Álbuns)
    tag_filter = request.args.get('tag_id')
    query = Diario.query.filter_by(user_id=current_user.id)
    
    filtro_nome = "Todas as Memórias"
    if tag_filter:
        query = query.filter_by(tag_id=tag_filter)
        tag_obj = Tag.query.get(tag_filter)
        if tag_obj: filtro_nome = f"Álbum: {tag_obj.nome}"

    entradas = query.order_by(Diario.data_registro.desc()).all()
    
    # Mapa de Cores para o Calendário
    mapa_humor = {e.data_registro.strftime('%Y-%m-%d'): e.humor_cor for e in entradas}
    
    return render_template('dashboard.html', entradas=entradas, mapa_humor=mapa_humor, 
                           filtro_nome=filtro_nome, ano_atual=date.today().year)

@app.route('/adicionar', methods=['GET', 'POST'])
@login_required
def adicionar():
    if request.method == 'POST':
        dt = datetime.strptime(request.form['data'], '%Y-%m-%d').date()
        
        # Lógica de Tag (Selecionar Existente ou Criar Nova)
        tag_id_final = None
        nova_tag_nome = request.form.get('nova_tag')
        tag_existente = request.form.get('tag_existente')

        if nova_tag_nome:
            nova_tag = Tag(nome=nova_tag_nome, user_id=current_user.id)
            db.session.add(nova_tag)
            db.session.commit()
            tag_id_final = nova_tag.id
        elif tag_existente:
            tag_id_final = int(tag_existente)

        novo = Diario(
            user_id=current_user.id,
            tag_id=tag_id_final,
            data_registro=dt,
            descricao=request.form['descricao'],
            nota_dia=int(request.form['nota']),
            humor_cor=request.form['humor_cor'],
            musica_dia=request.form['musica']
        )
        db.session.add(novo)
        db.session.commit()
        flash('Memória salva com sucesso!', 'success')
        return redirect('/dashboard')
    
    return render_template('add_entry.html', editando=False)

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    entrada = Diario.query.get_or_404(id)
    if entrada.user_id != current_user.id: return redirect('/')
    
    if request.method == 'POST':
        entrada.data_registro = datetime.strptime(request.form['data'], '%Y-%m-%d').date()
        entrada.descricao = request.form['descricao']
        entrada.nota_dia = int(request.form['nota'])
        entrada.humor_cor = request.form['humor_cor']
        entrada.musica_dia = request.form['musica']
        
        if request.form.get('nova_tag'):
            nt = Tag(nome=request.form.get('nova_tag'), user_id=current_user.id)
            db.session.add(nt); db.session.commit()
            entrada.tag_id = nt.id
        elif request.form.get('tag_existente'):
            entrada.tag_id = int(request.form.get('tag_existente'))

        db.session.commit()
        flash('Memória atualizada!', 'success')
        return redirect('/dashboard')
    return render_template('add_entry.html', entrada=entrada, editando=True)

@app.route('/excluir/<int:id>')
@login_required
def excluir(id):
    entrada = Diario.query.get_or_404(id)
    if entrada.user_id == current_user.id:
        db.session.delete(entrada)
        db.session.commit()
        flash('Memória excluída.', 'info')
    return redirect('/dashboard')

@app.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil():
    if request.method == 'POST':
        current_user.username = request.form['username']
        current_user.email = request.form['email']
        if request.form['password']:
            current_user.set_password(request.form['password'])
        try:
            db.session.commit()
            flash('Perfil atualizado!', 'success')
        except:
            flash('Erro: Nome de usuário já existe.', 'danger')
    return render_template('profile.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.check_password(request.form['password']):
            login_user(user)
            return redirect('/dashboard')
        flash('Usuário ou senha incorretos.', 'danger')
    return render_template('login.html')

# --- ROTA DE CADASTRO ATUALIZADA ---
@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        # Verifica duplicidade
        if User.query.filter_by(username=request.form['username']).first():
            flash('Este nome de usuário já existe. Escolha outro.', 'warning')
            return redirect('/cadastro')
            
        # Cria usuário
        u = User(username=request.form['username'], email=request.form['email'])
        u.set_password(request.form['password'])
        db.session.add(u)
        db.session.commit()
        
        # Manda mensagem e vai para Login
        flash('Sua conta foi criada com sucesso! Faça login para começar.', 'success')
        return redirect('/login')
        
    return render_template('register.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)