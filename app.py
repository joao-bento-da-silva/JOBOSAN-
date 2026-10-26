import os
import sqlite3
import secrets
import random
from functools import wraps
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify 
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("COOKIE_SECURE", "0") == "1"

# Caminho do banco de dados SQLite
DATABASE_PATH = os.environ.get("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "jobosan_jogos.db"))

def conectar():
    conn = sqlite3.connect(DATABASE_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn

def inicializar_banco():
    pasta = os.path.dirname(DATABASE_PATH)
    if pasta:
        os.makedirs(pasta, exist_ok=True)
    with conectar() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                senha_hash TEXT NOT NULL,
                criado_em TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS progresso (
                usuario_id INTEGER PRIMARY KEY,
                pontos INTEGER NOT NULL DEFAULT 0,
                fases_concluidas INTEGER NOT NULL DEFAULT 0,
                partidas INTEGER NOT NULL DEFAULT 0,
                atualizado_em TEXT NOT NULL,
                FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
            )
        """)

inicializar_banco()

def login_obrigatorio(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("usuario_id"):
            return redirect(url_for("entrar"))
        return fn(*args, **kwargs)
    return wrapper

@app.route("/")
def index():
    if session.get("usuario_id"):
        return redirect(url_for("painel"))
    return render_template("index.html")

@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")
        if len(nome) < 2:
            flash("Informe seu nome (pelo menos 2 caracteres).", "erro")
        elif "@" not in email or len(email) > 254:
            flash("Informe um e-mail válido.", "erro")
        elif len(senha) < 8:
            flash("A senha precisa ter pelo menos 8 caracteres.", "erro")
        else:
            try:
                with conectar() as conn:
                    cur = conn.execute(
                        "INSERT INTO usuarios (nome, email, senha_hash, criado_em) VALUES (?, ?, ?, ?)",
                        (nome, email, generate_password_hash(senha), datetime.utcnow().isoformat())
                    )
                    usuario_id = cur.lastrowid
                    conn.execute(
                        "INSERT INTO progresso (usuario_id, atualizado_em) VALUES (?, ?)",
                        (usuario_id, datetime.utcnow().isoformat())
                    )
                session.clear()
                session["usuario_id"] = usuario_id
                session["usuario_nome"] = nome
                return redirect(url_for("painel"))
            except sqlite3.IntegrityError:
                flash("Esse e-mail já está cadastrado. Entre na sua conta.", "erro")
    return render_template("auth.html", titulo="Criar conta", cadastro=True)

@app.route("/entrar", methods=["GET", "POST"])
def entrar():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")
        with conectar() as conn:
            usuario = conn.execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()
        if usuario and check_password_hash(usuario["senha_hash"], senha):
            session.clear()
            session["usuario_id"] = usuario["id"]
            session["usuario_nome"] = usuario["nome"]
            return redirect(url_for("painel"))
        flash("E-mail ou senha incorretos.", "erro")
    return render_template("auth.html", titulo="Entrar", cadastro=False)

@app.route("/sair", methods=["POST"])
def sair():
    session.clear()
    return redirect(url_for("index"))

@app.route("/painel")
@login_obrigatorio
def painel():
    with conectar() as conn:
        progresso = conn.execute(
            "SELECT * FROM progresso WHERE usuario_id = ?",
            (session["usuario_id"],)
        ).fetchone()
    return render_template("painel.html", progresso=progresso)

# Rota principal do Jogo com as novas especificações dos Gladiadores
@app.route("/jogo")
@login_obrigatorio
def jogo():
    # Passamos as configurações padrão do Labirinto para a renderização do HTML
    config_jogo = {
        "qtd_gladiadores": 4,
        "limite_turnos": 20,
        "saida_dinamica": True
    }
    return render_template("jogo.html", config=config_jogo)

@app.route("/api/resultado", methods=["POST"])
@login_obrigatorio
def resultado():
    dados = request.get_json(silent=True) or {}
    try:
        pontos = int(dados.get("pontos", 0))
        fases = int(dados.get("fases_concluidas", 0))
    except (TypeError, ValueError):
        return jsonify(ok=False, erro="Resultado inválido."), 400

    pontos = max(0, min(pontos, 5000))
    fases = max(0, min(fases, 4))
    agora = datetime.utcnow().isoformat()
    with conectar() as conn:
        conn.execute("""
            UPDATE progresso
            SET pontos = pontos + ?,
                fases_concluidas = MAX(fases_concluidas, ?),
                partidas = partidas + 1,
                atualizado_em = ?
            WHERE usuario_id = ?
        """, (pontos, fases, agora, session["usuario_id"]))
    return jsonify(ok=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=False)
