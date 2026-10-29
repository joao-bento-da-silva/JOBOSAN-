import os
import sqlite3
import secrets
from functools import wraps
from datetime import datetime, timezone
from flask import Flask, Response, get_flashed_messages
from flask import (
    Flask, render_template_string, request, redirect,
    url_for, session, flash, jsonify
)
from werkzeug.security import (
    generate_password_hash, check_password_hash
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)

DATABASE_PATH = os.environ.get(
    "DATABASE_PATH",
    os.path.join(os.path.dirname(__file__), "jobosan_jogos.db")
)

@app.route('/google510f4f340be76af9.html')
def google_verification():
    return "google-site-verification: google510f4f340be76af9.html"

@app.route('/robots.txt')
def robots():
    content = """User-agent: *
Allow: /
Sitemap: https://jobosan.onrender.com/sitemap.xml
"""
    return Response(content, mimetype='text/plain')

@app.route('/sitemap.xml')
def sitemap():
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://jobosan.onrender.com/</loc>
    <priority>1.0</priority>
  </url>
</urlset>
"""
    return Response(xml_content, mimetype='application/xml')

# =======================================================

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

inicializar_banco()

def login_obrigatorio(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("usuario_id"):
            return redirect(url_for("entrar"))
        return fn(*args, **kwargs)
    return wrapper

# LAYOUT COM METADADOS PARA O GOOGLE E ASSINATURA DE AUTORIA JUDICIAL
LAYOUT_GERAL = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Fuga dos Plebeus - O Xadrez Inverso. Um jogo estratégico criado por João Bento da Silva (JOBOSAN Jogos).">
    <meta name="author" content="João Bento da Silva">
    <title>{{ title }}</title>
    <style>
        body { font-family: Arial, sans-serif; background: #121212; color: #f0f0f0; margin: 0; padding: 0; display: flex; flex-direction: column; min-height: 100vh; }
        header { background: #1f1f1f; padding: 15px 20px; display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #333; }
        header h1 { margin: 0; font-size: 1.5rem; color: #ffcc00; }
        nav a, nav button { color: #fff; background: #333; border: none; padding: 8px 15px; margin-left: 10px; border-radius: 4px; text-decoration: none; cursor: pointer; }
        nav a:hover, nav button:hover { background: #555; }
        .container { flex: 1; max-width: 950px; margin: 20px auto; padding: 20px; background: #1e1e1e; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.5); width: 92%; }
        footer { text-align: center; padding: 15px; background: #1a1a1a; color: #888; font-size: 0.85rem; border-top: 1px solid #333; }
        .flashes { margin-bottom: 15px; }
        .flash { padding: 10px; border-radius: 4px; margin-bottom: 5px; font-size: 0.9rem; }
        .flash.erro { background: #800000; color: #fff; }
        .flash.sucesso { background: #006600; color: #fff; }
        
        .jogo-layout { display: flex; flex-direction: column; gap: 20px; }
        @media(min-width: 768px) { .jogo-layout { flex-direction: row; } }
        .painel-lateral { flex: 1; background: #252525; padding: 15px; border-radius: 6px; }
        .area-tabuleiro { flex: 2; display: flex; flex-direction: column; align-items: center; }
        .tabuleiro-xadrez { display: grid; grid-template-columns: repeat(8, 45px); grid-template-rows: repeat(8, 45px); border: 3px solid #444; background: #333; gap: 1px; }
        .casa { width: 45px; height: 45px; display: flex; align-items: center; justify-content: center; font-size: 24px; cursor: pointer; user-select: none; }
        .casa.clara { background: #f0d9b5; color: #000; }
        .casa.escura { background: #b58863; color: #000; }
        .casa:hover { opacity: 0.8; }
        .status-alerta { margin-bottom: 10px; font-weight: bold; color: #ffcc00; text-align: center; }
        .btn-acao { background: #d9534f; color: white; border: none; padding: 10px; width: 100%; border-radius: 4px; cursor: pointer; font-weight: bold; margin-top: 15px; }
        .btn-acao:hover { background: #c9302c; }
        
        .auth-container { max-width: 400px; margin: 40px auto; }
        .campo { margin-bottom: 15px; }
        .campo label { display: block; margin-bottom: 5px; color: #ccc; }
        .campo input { width: 100%; padding: 10px; background: #2a2a2a; border: 1px solid #444; color: #fff; border-radius: 4px; box-sizing: border-box; }
        .btn-submit { background: #0275d8; color: white; border: none; padding: 10px; width: 100%; border-radius: 4px; font-weight: bold; cursor: pointer; }
        .btn-submit:hover { background: #025aa5; }
        .auth-footer { text-align: center; margin-top: 15px; font-size: 0.9rem; }
        .auth-footer a { color: #5bc0de; text-decoration: none; }
    </style>
</head>
<body>
    <header>
        <h1>🏰 Fuga dos Plebeus</h1>
        <nav>
            {% if session.get('usuario_id') %}
                <span>Olá, <strong>{{ session.get('usuario_nome') }}</strong></span>
                <a href="{{ url_for('painel') }}">Painel</a>
                <a href="{{ url_for('jogo') }}">Jogar</a>
                <form action="{{ url_for('sair') }}" method="POST" style="display:inline;">
                    <button type="submit">Sair</button>
                </form>
            {% else %}
                <a href="{{ url_for('entrar') }}">Entrar</a>
                <a href="{{ url_for('cadastro') }}">Criar Conta</a>
            {% endif %}
        </nav>
    </header>

    <main class="container">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                <div class="flashes">
                    {% for cat, msg in messages %}
                        <div class="flash {{ cat }}">{{ msg }}</div>
                    {% endfor %}
                </div>
            {% endif %}
        {% endwith %}

        {{ content | safe }}
    </main>

    <footer>
        <p>&copy; 2026 JOBOSAN Jogos — Criado e Desenvolvido por <strong>João Bento da Silva</strong>. Todos os direitos reservados.</p>
    </footer>
</body>
</html>
"""

@app.route("/")
def index():
    if session.get("usuario_id"):
        return redirect(url_for("painel"))
    conteudo = """
    <div style="text-align: center; padding: 30px;">
        <h2>♟️ Fuga dos Plebeus — O Xadrez Inverso</h2>
        <p style="font-style: italic; color: #ffcc00; margin: 15px 0;">"Não é força que vence, mas sim a sabedoria de saber para onde ir."</p>
        <div style="background: #252525; padding: 20px; border-radius: 6px; text-align: left; margin: 20px 0; line-height: 1.6;">
            <h3 style="color: #ffcc00; margin-top: 0;">📖 A História do Reino de Valverde</h3>
            <p>Há muito tempo, no Reino de Valverde, o povo simples vivia em paz. Mas um dia, a Corte Real perdeu a razão. O Rei, a Rainha, os Bispos e os soldados decidiram que os plebeus já não tinham lugar no reino. Eles queriam tomar tudo para si.</p>
            <p>Agora, o reino está fechado. As ruas viraram labirintos vigiados. Os soldados do Rei patrulham cada beco. E só existe uma única saída para a liberdade.</p>
        </div>
        <div style="margin-top: 25px;">
            <a href=""" + url_for('cadastro') + """ style="background: #5cb85c; color: #fff; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold; margin-right: 10px;">Criar Conta e Jogar</a>
            <a href=""" + url_for('entrar') + """ style="background: #0275d8; color: #fff; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold;">Entrar</a>
        </div>
    </div>
    """
    return render_template_string(LAYOUT_GERAL, title="Fuga dos Plebeus — JOBOSAN Jogos", content=conteudo)

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
        elif len(senha) < 6:
            flash("A senha precisa ter pelo menos 6 caracteres.", "erro")
        else:
            try:
                with conectar() as conn:
                    cur = conn.execute(
                        "INSERT INTO usuarios (nome, email, senha_hash, criado_em) VALUES (?, ?, ?, ?)",
                        (nome, email, generate_password_hash(senha), agora())
                    )
                    uid = cur.lastrowid
                    conn.execute(
                        "INSERT INTO progresso (usuario_id, atualizado_em) VALUES (?, ?)",
                        (uid, agora())
                    )
                session.clear()
                session["usuario_id"] = uid
                session["usuario_nome"] = nome
                flash("Conta criada com sucesso! Bem-vindo, " + nome + "!", "sucesso")
                return redirect(url_for("painel"))
            except sqlite3.IntegrityError:
                flash("Esse e-mail já está cadastrado. Tente fazer login.", "erro")

    conteudo = """
    <div class="auth-container">
        <h2>Criar Nova Conta</h2>
        <form method="POST">
            <div class="campo"><label>Nome</label><input type="text" name="nome" required></div>
            <div class="campo"><label>E-mail</label><input type="email" name="email" required></div>
            <div class="campo"><label>Senha</label><input type="password" name="senha" required></div>
            <button type="submit" class="btn-submit">Cadastrar</button>
        </form>
        <div class="auth-footer"><p>Já tem conta? <a href=""" + url_for('entrar') + """>Entrar aqui</a></p></div>
    </div>
    """
    return render_template_string(LAYOUT_GERAL, title="Cadastro — JOBOSAN", content=conteudo)

@app.route("/entrar", methods=["GET", "POST"])
def entrar():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")
        
        with conectar() as conn:
            usuario = conn.execute(
                "SELECT * FROM usuarios WHERE email = ?",
                (email,)
            ).fetchone()
        
        if not usuario:
            flash("E-mail não encontrado. Verifique ou crie uma conta nova.", "erro")
        elif not check_password_hash(usuario["senha_hash"], senha):
            flash("Senha incorreta. Tente novamente.", "erro")
        else:
            session.clear()
            session["usuario_id"] = usuario["id"]
            session["usuario_nome"] = usuario["nome"]
            flash("Bem-vindo de volta, " + usuario["nome"] + "!", "sucesso")
            return redirect(url_for("painel"))

    conteudo = """
    <div class="auth-container">
        <h2>Entrar no Jogo</h2>
        <form method="POST">
            <div class="campo"><label>E-mail</label><input type="email" name="email" required></div>
            <div class="campo"><label>Senha</label><input type="password" name="senha" required></div>
            <button type="submit" class="btn-submit">Entrar</button>
        </form>
        <div class="auth-footer"><p>Não tem conta ainda? <a href=""" + url_for('cadastro') + """>Crie uma agora</a></p></div>
    </div>
    """
    return render_template_string(LAYOUT_GERAL, title="Entrar — JOBOSAN", content=conteudo)

@app.route("/sair", methods=["POST"])
def sair():
    session.clear()
    flash("Você saiu com sucesso!", "sucesso")
    return redirect(url_for("index"))

@app.route("/painel")
@login_obrigatorio
def painel():
    with conectar() as conn:
        prog = conn.execute(
            "SELECT * FROM progresso WHERE usuario_id = ?",
            (session["usuario_id"],)
        ).fetchone()
    
    pontos = prog["pontos"] if prog else 0
    fases = prog["fases_concluidas"] if prog else 0
    partidas = prog["partidas"] if prog else 0

    conteudo = f"""
    <div>
        <h2>Painel do Jogador — Reino de Valverde</h2>
        <div style="display: flex; gap: 15px; margin: 20px 0; flex-wrap: wrap;">
            <div style="background: #252525; padding: 15px; border-radius: 5px; flex: 1; min-width: 140px;"><h3>Pontos</h3><p style="font-size: 1.5rem; color: #ffcc00;">{pontos}</p></div>
            <div style="background: #252525; padding: 15px; border-radius: 5px; flex: 1; min-width: 140px;"><h3>Fases Concluídas</h3><p style="font-size: 1.5rem; color: #5cb85c;">{fases} / 4</p></div>
            <div style="background: #252525; padding: 15px; border-radius: 5px; flex: 1; min-width: 140px;"><h3>Partidas</h3><p style="font-size: 1.5rem; color: #5bc0de;">{partidas}</p></div>
        </div>

        <h3 style="margin-top: 30px; color: #ffcc00;">Estágios da Fuga</h3>
        <table style="width: 100%; border-collapse: collapse; margin-top: 10px; background: #25
        
 @app.route("/jogo")
@login_obrigatorio
def jogo():
    return render_template_string(LAYOUT_GERAL, title="Jogo — Fuga dos Plebeus", content="""
    <div class="jogo-layout">
        <aside class="painel-lateral">
            <div class="status-box">
                <h3>Status da Partida</h3>
                <p><strong>Fase Atual:</strong> <span id="fase-atual">1</span> / 4</p>
                <p><strong>Turnos Restantes:</strong> <span id="turnos-restantes">20</span></p>
                <p><strong>Plebeus Restantes:</strong> <span id="plebeus-restantes">3</span></p>
                <p><strong>Pontos da Partida:</strong> <span id="pontos-acumulados">0</span></p>
            </div>

            <div class="regras-box">
                <h4>Regras de Movimento</h4>
                <ul>
                    <li><strong>Plebeus:</strong> Clica para selecionar, depois clica em uma casa ao lado para mover.</li>
                    <li><strong>Rei:</strong> Persegue 1 casa por vez em qualquer direção.</li>
                    <li><strong>Rainha:</strong> Persegue em linha reta ou diagonal, uma casa por turno.</li>
                    <li><strong>Bispo:</strong> Apenas na diagonal — se não estiver na diagonal, não se move!</li>
                    <li><strong>🚪 Saída:</strong> Leve todos os plebeus até a saída para vencer!</li>
                </ul>
            </div>

            <button id="btn-reiniciar" class="btn-acao">Reiniciar Fase</button>
        </aside>

        <section class="area-tabuleiro">
            <h2>Fuga dos Plebeus</h2>
            <div id="mensagem-status" class="status-alerta">Selecione um plebeu para mover!</div>
            <div id="tabuleiro" class="tabuleiro-xadrez"></div>
        </section>
    </div>

    <script>
        window.GAME_CONFIG = {{ config | tojson }};
        window.REGRAS = {{ regras | tojson }};
        window.FASES = {{ fases | tojson }};
    </script>
    <script src="/static/game.js"></script>
    """,
        config={
            "titulo": "Fuga dos Plebeus",
            "limite_turnos": 20,
        },
        regras={},
        fases={}
    )


@app.route("/api/resultado", methods=["POST"])
@login_obrigatorio
def resultado():
    dados = request.get_json(silent=True) or {}
    try:
        pontos = int(dados.get("pontos", 0))
        fases_concluidas = int(dados.get("fases_concluidas", 0))
    except (TypeError, ValueError):
        return jsonify(ok=False, erro="Dados inválidos."), 400

    with conectar() as conn:
        conn.execute("""
            UPDATE progresso
            SET pontos = pontos + ?,
                fases_concluidas = MAX(fases_concluidas, ?),
                partidas = partidas + 1,
                atualizado_em = ?
            WHERE usuario_id = ?
        """, (pontos, fases_concluidas, datetime.now(timezone.utc).isoformat(), session["usuario_id"]))
    
    return jsonify(ok=True)


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )
