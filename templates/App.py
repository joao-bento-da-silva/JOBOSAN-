
import os 
import sqlite3
import secrets
from functools import wraps
from datetime import datetime, timezone

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, jsonify
)
from werkzeug.security import (
    generate_password_hash, check_password_hash
)

app = Flask(__name__)
app.secret_key = (
    os.environ.get("SECRET_KEY") or secrets.token_hex(32)
)

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = (
    os.environ.get("COOKIE_SECURE", "0") == "1"
)

# Banco de dados próprio do JOBOSAN Jogos.
DATABASE_PATH = os.environ.get(
    "DATABASE_PATH",
    os.path.join(os.path.dirname(__file__), "jobosan_jogos.db")
)

# Regras oficiais de Fuga dos Plebeus.
FASES = {
    1: {
        "plebeus": 3,
        "limite_turnos": 20,
        "pontos": 100,
        "movimentos_corte": 1,
    },
    2: {
        "plebeus": 4,
        "limite_turnos": 18,
        "pontos": 150,
        "movimentos_corte": 1,
    },
    3: {
        "plebeus": 5,
        "limite_turnos": 15,
        "pontos": 200,
        "movimentos_corte": 2,
    },
    4: {
        "plebeus": 6,
        "limite_turnos": 12,
        "pontos": 300,
        "movimentos_corte": 2,
    },
}

HISTORIA = {
    "titulo": "Fuga dos Plebeus — O Xadrez Inverso",
    "reino": "Reino de Valverde",
    "texto": (
        "Há muito tempo, no Reino de Valverde, o povo simples "
        "vivia em paz. Mas a Corte Real perdeu a razão. "
        "O Rei, a Rainha, os Bispos e os soldados decidiram "
        "que os plebeus já não tinham lugar no reino. "
        "Agora, o reino está fechado, as ruas viraram "
        "labirintos vigiados e os soldados patrulham os becos. "
        "Só existe uma saída para a liberdade."
    ),
    "lema": (
        "Não é força que vence, mas sim a sabedoria "
        "de saber para onde ir."
    ),
}

REGRAS = {
    "movimento_plebeu": (
        "Uma casa por vez: cima, baixo, esquerda ou direita."
    ),
    "captura": (
        "Um plebeu alcançado pela Corte é capturado e removido."
    ),
    "objetivo": (
        "Conduzir os plebeus até a saída do labirinto."
    ),
    "vitoria": (
        "Concluir o objetivo da fase dentro do limite de turnos."
    ),
    "pecas_corte": {
        "rei": "Uma casa em qualquer direção.",
        "rainha": "Qualquer distância em linha reta ou diagonal.",
        "bispo": "Qualquer distância na diagonal.",
    },
    "restricoes": [
        "Não existem torres nem cavalos.",
        "Os plebeus não podem atravessar paredes.",
        "Os plebeus não podem atravessar uns aos outros.",
        "Os movimentos da Corte devem respeitar o tabuleiro.",
    ],
}


def agora():
    return datetime.now(timezone.utc).isoformat()


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

        # Garante que contas existentes tenham uma linha de progresso.
        conn.execute("""
            INSERT OR IGNORE INTO progresso
                (usuario_id, atualizado_em)
            SELECT id, ? FROM usuarios
        """, (agora(),))


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
                        """
                        INSERT INTO usuarios
                            (nome, email, senha_hash, criado_em)
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            nome,
                            email,
                            generate_password_hash(senha),
                            agora(),
                        ),
                    )
                    usuario_id = cur.lastrowid

                    conn.execute(
                        """
                        INSERT INTO progresso
                            (usuario_id, atualizado_em)
                        VALUES (?, ?)
                        """,
                        (usuario_id, agora()),
                    )

                session.clear()
                session["usuario_id"] = usuario_id
                session["usuario_nome"] = nome
                return redirect(url_for("painel"))

            except sqlite3.IntegrityError:
                flash(
                    "Esse e-mail já está cadastrado. Entre na sua conta.",
                    "erro",
                )

    return render_template(
        "auth.html",
        titulo="Criar conta",
        cadastro=True,
    )


@app.route("/entrar", methods=["GET", "POST"])
def entrar():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")

        with conectar() as conn:
            usuario = conn.execute(
                "SELECT * FROM usuarios WHERE email = ?",
                (email,),
            ).fetchone()

        if usuario and check_password_hash(usuario["senha_hash"], senha):
            session.clear()
            session["usuario_id"] = usuario["id"]
            session["usuario_nome"] = usuario["nome"]
            return redirect(url_for("painel"))

        flash("E-mail ou senha incorretos.", "erro")

    return render_template(
        "auth.html",
        titulo="Entrar",
        cadastro=False,
    )


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
            (session["usuario_id"],),
        ).fetchone()

    return render_template("painel.html", progresso=progresso)


@app.route("/jogo")
@login_obrigatorio
def jogo():
    return render_template(
        "jogo.html",
        historia=HISTORIA,
        regras=REGRAS,
        fases=FASES,
        config={
            "titulo": HISTORIA["titulo"],
            "qtd_gladiadores": 4,
            "limite_turnos": FASES[1]["limite_turnos"],
            "saida_dinamica": True,
            "movimento_plebeu": "ortogonal",
            "captura_automatica": True,
            "fases": 4,
        },
    )


@app.route("/api/configuracao", methods=["GET"])
@login_obrigatorio
def configuracao():
    return jsonify(
        ok=True,
        historia=HISTORIA,
        regras=REGRAS,
        fases=FASES,
    )


@app.route("/api/resultado", methods=["POST"])
@login_obrigatorio
def resultado():
    dados = request.get_json(silent=True) or {}

    try:
        fase = int(dados.get("fase", 0))
        pontos = int(dados.get("pontos", 0))
        fases_concluidas = int(dados.get("fases_concluidas", 0))
    except (TypeError, ValueError):
        return jsonify(
            ok=False,
            erro="Resultado inválido.",
        ), 400

    if fase not in FASES:
        return jsonify(ok=False, erro="Fase inválida."), 400

    # O navegador não pode enviar pontuação negativa ou acima
    # da recompensa prevista para a fase.
    pontos = max(0, min(pontos, FASES[fase]["pontos"]))
    fases_concluidas = max(0, min(fases_concluidas, 4))

    agora_atual = agora()

    with conectar() as conn:
        conn.execute("""
            UPDATE progresso
            SET pontos = pontos + ?,
                fases_concluidas = MAX(fases_concluidas, ?),
                partidas = partidas + 1,
                atualizado_em = ?
            WHERE usuario_id = ?
        """, (
            pontos,
            fases_concluidas,
            agora_atual,
            session["usuario_id"],
        ))

    return jsonify(ok=True)


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "5000")),
        debug=False,
    )
