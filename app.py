import os
import sqlite3
import secrets
from functools import wraps
from datetime import datetime, timezone

from flask import (
    Flask, render_template_string, request, redirect,
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

DATABASE_PATH = os.environ.get(
    "DATABASE_PATH",
    os.path.join(os.path.dirname(__file__), "jobosan_jogos.db")
)

FASES = {
    1: {"plebeus": 3, "limite_turnos": 20, "pontos": 100, "movimentos_corte": 1},
    2: {"plebeus": 4, "limite_turnos": 18, "pontos": 150, "movimentos_corte": 1},
    3: {"plebeus": 5, "limite_turnos": 15, "pontos": 200, "movimentos_corte": 2},
    4: {"plebeus": 6, "limite_turnos": 12, "pontos": 300, "movimentos_corte": 2},
}

HISTORIA = {
    "titulo": "Fuga dos Plebeus — O Xadrez Inverso",
    "reino": "Reino de Valverde",
    "texto": (
        "Há muito tempo, no Reino de Valverde, o povo simples vivia em paz. "
        "Mas a Corte Real perdeu a razão. O Rei, a Rainha, os Bispos e os soldados "
        "decidiram que os plebeus já não tinham lugar no reino. "
        "Agora, o reino está fechado, as ruas viraram labirintos vigiados e "
        "os soldados patrulham os becos. Só existe uma saída para a liberdade."
    ),
    "lema": "Não é força que vence, mas sim a sabedoria de saber para onde ir.",
}

REGRAS = {
    "movimento_plebeu": "Uma casa por vez: cima, baixo, esquerda ou direita.",
    "captura": "Um plebeu alcançado pela Corte é capturado e removido.",
    "objetivo": "Conduzir os plebeus até a saída do labirinto.",
    "vitoria": "Concluir o objetivo da fase dentro do limite de turnos.",
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
        conn.execute("""
            INSERT OR IGNORE INTO progresso (usuario_id, atualizado_em)
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

# --- LAYOUT BASE HTML ---
BASE_HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Fuga dos Plebeus{% endblock %}</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
    <header class="navbar">
        <div class="logo">
            <h1>🏰 Fuga dos Plebeus</h1>
        </div>
        <nav>
            {% if session.get('usuario_id') %}
                <span>Olá, <strong>{{ session.get('usuario_nome') }}</strong></span>
                <a href="{{ url_for('painel') }}">Painel</a>
                <a href="{{ url_for('jogo') }}">Jogar</a>
                <form action="{{ url_for('sair') }}" method="POST" style="display:inline;">
                    <button type="submit" class="btn-sair">Sair</button>
                </form>
            {% else %}
                <a href="{{ url_for('entrar') }}">Entrar</a>
                <a href="{{ url_for('cadastro') }}" class="btn-destaque">Criar Conta</a>
            {% endif %}
        </nav>
    </header>

    <main class="container">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                <div class="flashes">
                    {% for category, message in messages %}
                        <div class="flash {{ category }}">{{ message }}</div>
                    {% endfor %}
                </div>
            {% endif %}
        {% endwith %}

        {% block content %}{% endblock %}
    </main>

    <footer>
        <p>&copy; JOBOSAN Jogos - Reino de Valverde. Todos os direitos reservados.</p>
    </footer>

    {% block scripts %}{% endblock %}
</body>
</html>
"""

@app.route("/")
def index():
    if session.get("usuario_id"):
        return redirect(url_for("painel"))
    
    html = BASE_HTML.replace("{% block title %}Fuga dos Plebeus{% endblock %}", "{% block title %}Início — Fuga dos Plebeus{% endblock %}")
    conteudo = """
    {% block content %}
    <section class="hero">
        <h2>Fuga dos Plebeus — O Xadrez Inverso</h2>
        <p class="lema">"Não é força que vence, mas sim a sabedoria de saber para onde ir."</p>
        <div class="card-historia">
            <h3>A História de Valverde</h3>
            <p>Há muito tempo, no Reino de Valverde, o povo simples vivia em paz. Mas a Corte Real perdeu a razão. O Rei, a Rainha, os Bispos e os soldados decidiram que os plebeus já não tinham lugar no reino.</p>
            <p>Agora, o reino está fechado, as ruas viraram labirintos vigiados e os soldados patrulham os becos. Só existe uma saída para a liberdade.</p>
        </div>
        <div class="acoes-inicio">
            <a href="{{ url_for('cadastro') }}" class="btn-principal">Começar a Jogar</a>
            <a href="{{ url_for('entrar') }}" class="btn-secundario">Já tenho conta</a>
        </div>
    </section>
    {% endblock %}
    """
    return render_template_string(html.replace("{% block content %}{% endblock %}", conteudo))

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
                        (nome, email, generate_password_hash(senha), agora())
                    )
                    usuario_id = cur.lastrowid
                    conn.execute("INSERT INTO progresso (usuario_id, atualizado_em) VALUES (?, ?)", (usuario_id, agora()))
                session.clear()
                session["usuario_id"] = usuario_id
                session["usuario_nome"] = nome
                return redirect(url_for("painel"))
            except sqlite3.IntegrityError:
                flash("Esse e-mail já está cadastrado. Entre na sua conta.", "erro")

    html = BASE_HTML.replace("{% block title %}Fuga dos Plebeus{% endblock %}", "{% block title %}Criar conta — Fuga dos Plebeus{% endblock %}")
    conteudo = """
    {% block content %}
    <div class="auth-container">
        <h2>Criar conta</h2>
        <form method="POST" class="form-auth">
            <div class="campo">
                <label for="nome">Nome Completo</label>
                <input type="text" id="nome" name="nome" placeholder="Seu nome ou apelido" required minlength="2">
            </div>
            <div class="campo">
                <label for="email">E-mail</label>
                <input type="email" id="email" name="email" placeholder="seuemail@exemplo.com" required>
            </div>
            <div class="campo">
                <label for="senha">Senha</label>
                <input type="password" id="senha" name="senha" placeholder="••••••••" required minlength="8">
            </div>
            <button type="submit" class="btn-submit">Criar Minha Conta</button>
        </form>
        <div class="auth-footer">
            <p>Já tem uma conta? <a href="{{ url_for('entrar') }}">Faça login aqui</a></p>
        </div>
    </div>
    {% endblock %}
    """
    return render_template_string(html.replace("{% block content %}{% endblock %}", conteudo))

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

    html = BASE_HTML.replace("{% block title %}Fuga dos Plebeus{% endblock %}", "{% block title %}Entrar — Fuga dos Plebeus{% endblock %}")
    conteudo = """
    {% block content %}
    <div class="auth-container">
        <h2>Entrar</h2>
        <form method="POST" class="form-auth">
            <div class="campo">
                <label for="email">E-mail</label>
                <input type="email" id="email" name="email" placeholder="seuemail@exemplo.com" required>
            </div>
            <div class="campo">
                <label for="senha">Senha</label>
                <input type="password" id="senha" name="senha" placeholder="••••••••" required>
            </div>
            <button type="submit" class="btn-submit">Entrar no Jogo</button>
        </form>
        <div class="auth-footer">
            <p>Ainda não tem conta? <a href="{{ url_for('cadastro') }}">Cadastre-se gratuitamente</a></p>
        </div>
    </div>
    {% endblock %}
    """
    return render_template_string(html.replace("{% block content %}{% endblock %}", conteudo))

@app.route("/sair", methods=["POST"])
def sair():
    session.clear()
    return redirect(url_for("index"))

@app.route("/painel")
@login_obrigatorio
def painel():
    with conectar() as conn:
        progresso = conn.execute("SELECT * FROM progresso WHERE usuario_id = ?", (session["usuario_id"],)).fetchone()
    
    html = BASE_HTML.replace("{% block title %}Fuga dos Plebeus{% endblock %}", "{% block title %}Painel do Jogador — Fuga dos Plebeus{% endblock %}")
    conteudo = f"""
    {{% block content %}}
    <section class="painel-container">
        <h2>Seu Desempenho no Reino de Valverde</h2>
        <div class="cards-progresso">
            <div class="card-status">
                <h3>🏆 Pontuação Total</h3>
                <p class="valor">{progresso['pontos'] if progresso else 0} pts</p>
            </div>
            <div class="card-status">
                <h3>🚩 Fases Concluídas</h3>
                <p class="valor">{progresso['fases_concluidas'] if progresso else 0} / 4</p>
            </div>
            <div class="card-status">
                <h3>⚔️ Partidas Jogadas</h3>
                <p class="valor">{progresso['partidas'] if progresso else 0}</p>
            </div>
        </div>
        <div class="tabela-fases">
            <h3>Estágios da Fuga</h3>
            <table>
                <thead>
                    <tr><th>Fase</th><th>Nome</th><th>Desafio</th><th>Recompensa</th></tr>
                </thead>
                <tbody>
                    <tr><td>1</td><td>🌾 A Vila Fechada</td><td>Labirinto pequeno, poucos guardas</td><td>100 pontos</td></tr>
                    <tr><td>2</td><td>🌲 A Floresta Cercada</td><td>Mais paredes, mais soldados</td><td>150 pontos</td></tr>
                    <tr><td>3</td><td>🏰 Os Muros do Reino</td><td>Labirinto complexo, guardas estratégicos</td><td>200 pontos</td></tr>
                    <tr><td>4</td><td>🌅 O Último Portão</td><td>Perseguidores te cercam, labirinto enorme</td><td>300 pontos</td></tr>
                </tbody>
            </table>
        </div>
        <div class="area-acao">
            <a href="{{{{ url_for('jogo') }}}}" class="btn-jogar-grande">Iniciar Fuga ♟️</a>
        </div>
    </section>
    {{% endblock %}}
    """
    return render_template_string(html.replace("{% block content %}{% endblock %}", conteudo))

@app.route("/jogo")
@login_obrigatorio
def jogo():
    html = BASE_HTML.replace("{% block title %}Fuga dos Plebeus{% endblock %}", "{% block title %}Tabuleiro — Fuga dos Plebeus{% endblock %}")
    conteudo = """
    {% block content %}
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
                <h4>Petição de Movimentos</h4>
                <ul>
                    <li><strong>Plebeus:</strong> Ortogonal (uma casa por vez).</li>
                    <li><strong>Rei:</strong> Uma casa (qualquer direção).</li>
                    <li><strong>Rainha:</strong> Linhas retas e diagonais.</li>
                    <li><strong>Bispo:</strong> Apenas diagonais.</li>
                </ul>
            </div>
            <button id="btn-reiniciar" class="btn-secundario">Reiniciar Fase</button>
        </aside>
        <section class="area-tabuleiro">
            <div id="mensagem-status" class="status-alerta">Selecione um plebeu para mover!</div>
            <div id="tabuleiro" class="tabuleiro-xadrez"></div>
        </section>
    </div>
    {% endblock %}
    {% block scripts %}
    <script>
        window.GAME_CONFIG = {"titulo": "Fuga dos Plebeus — O Xadrez Inverso", "qtd_gladiadores": 4, "limite_turnos": 20, "saida_dinamica": true, "movimento_plebeu": "ortogonal", "captura_automatica": true, "fases": 4};
    </script>
    <script src="{{ url_for('static', filename='game.js') }}"></script>
    {% endblock %}
    """
    return render_template_string(html.replace("{% block content %}{% endblock %}", conteudo).replace("{% block scripts %}{% endblock %}", conteudo_scripts := ""))

@app.route("/api/configuracao", methods=["GET"])
@login_obrigatorio
def configuracao():
    return jsonify(ok=True, historia=HISTORIA, regras=REGRAS, fases=FASES)

@app.route("/api/resultado", methods=["POST"])
@login_obrigatorio
def resultado():
    dados = request.get_json(silent=True) or {}
    try:
        fase = int(dados.get("fase", 0))
        pontos = int(dados.get("pontos", 0))
        fases_concluidas = int(dados.get("fases_concluidas", 0))
    except (TypeError, ValueError):
        return jsonify(ok=False, erro="Resultado inválido."), 400

    if fase not in FASES:
        return jsonify(ok=False, erro="Fase inválida."), 400

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
        """, (pontos, fases_concluidas, agora_atual, session["usuario_id"]))

    return jsonify(ok=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=False)
