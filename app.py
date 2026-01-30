from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
import time
from sqlalchemy.exc import OperationalError

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sua_chave_secreta_aqui'
# Configuração para o Postgres no Docker
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://user:pass@db:5432/kanban_db')

with app.app_context():
    retries = 5
    while retries > 0:
        try:
            db.create_all()
            print("Banco inicializado com sucesso!")
            break
        except OperationalError:
            retries -= 1
            print(f"Banco não pronto, retry em 5s ({retries})")
            time.sleep(5)


db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- MODELOS ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    columns = db.relationship('Column', backref='owner', lazy=True)

class Column(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tasks = db.relationship('Task', backref='column', cascade="all, delete-orphan", lazy=True)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    column_id = db.Column(db.Integer, db.ForeignKey('column.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- ROTAS (Exemplos) ---
@app.route('/')
@login_required
def index():
    user_columns = Column.query.filter_by(user_id=current_user.id).all()
    return render_template('kanban.html', columns=user_columns)

# Lógica de CRUD simplificada para Colunas
@app.route('/add_column', methods=['POST'])
@login_required
def add_column():
    title = request.form.get('title')
    new_col = Column(title=title, owner=current_user)
    db.session.add(new_col)
    db.session.commit()
    return redirect(url_for('index'))
