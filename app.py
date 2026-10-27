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
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)

DATABASE_PATH = os.environ.get(
    "DATABASE_PATH",
    os.path.join(os.path.dirname(__file__), "jobosan_jogos.db")
)

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

# LAYOUT COMPLETO COM ESTILO E TABULEIRO FUNCIONAL EMBUTIDOS
LAYOUT_GERAL = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        body { font-family: Arial, sans-serif; background: #121212; color: #f0f0f0; margin: 0; padding: 0; display: flex; flex-direction: column; min-height: 100vh; }
        header { background: #1f1f1f; padding: 15px 20px; display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #333; }
        header h1 { margin: 0; font-size: 1.5rem; color: #ffcc00; }
        nav a, nav button { color: #fff; background: #333; border: none; padding: 8px 15px; margin-left: 10px; border-radius: 4px; text-decoration: none; cursor: pointer; }
        nav a:hover, nav button:hover { background: #555; }
        .container { flex: 1; max-width: 900px; margin: 20px auto; padding: 20px; background: #1e1e1e; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.5); width: 92%; }
        .flashes { margin-bottom: 15px; }
        .flash { padding: 10px; border-radius: 4px; margin-bottom: 5px; font-size: 0.9rem; }
        .flash.erro { background: #800000; color: #fff; }
        .flash.sucesso { background: #006600; color: #fff; }
        
        /* Estilos do Jogo / Tabuleiro */
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
        
        /* Autenticação */
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

    <div class="container">
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
    </div>
</body>
</html>
"""

@app.route("/")
def index():
    if session.get("usuario_id"):
        return redirect(url_for("painel"))
    conteudo = """
    <div style="text-align: center; padding: 30px;">
        <h2>O Xadrez Inverso de Valverde</h2>
        <p>"Não é força que vence, mas sim a sabedoria de saber para onde ir."</p>
        <p>A Corte Real enlouqueceu e os plebeus precisam encontrar a saída do labirinto!</p>
        <div style="margin-top: 25px;">
            <a href=""" + url_for('cadastro') + """ style="background: #5cb85c; color: #fff; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold; margin-right: 10px;">Criar Conta</a>
            <a href=""" + url_for('entrar') + """ style="background: #0275d8; color: #fff; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold;">Entrar</a>
        </div>
    </div>
    """
    return render_template_string(LAYOUT_GERAL, title="Início — Fuga dos Plebeus", content=conteudo)

@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")
        if len(nome) < 2 or "@" not in email or len(senha) < 6:
            flash("Preencha os campos corretamente (senha mínima de 6 dígitos).", "erro")
        else:
            try:
                with conectar() as conn:
                    cur = conn.execute(
                        "INSERT INTO usuarios (nome, email, senha_hash, criado_em) VALUES (?, ?, ?, ?)",
                        (nome, email, generate_password_hash(senha), agora())
                    )
                    uid = cur.lastrowid
                    conn.execute("INSERT INTO progresso (usuario_id, atualizado_em) VALUES (?, ?)", (uid, agora()))
                session.clear()
                session["usuario_id"] = uid
                session["usuario_nome"] = nome
                return redirect(url_for("painel"))
            except sqlite3.IntegrityError:
                flash("Este e-mail já está cadastrado.", "erro")

    conteudo = """
    <div class="auth-container">
        <h2>Criar Nova Conta</h2>
        <form method="POST">
            <div class="campo"><label>Nome</label><input type="text" name="nome" required></div>
            <div class="campo"><label>E-mail</label><input type="email" name="email" required></div>
            <div class="campo"><label>Senha</label><input type="password" name="senha" required></div>
            <button type="submit" class="btn-submit">Cadastrar</button>
        </form>
        <div class="auth-footer"><p>Já tem conta? <a href=""" + url_for('entrar') + """>Entrar</a></p></div>
    </div>
    """
    return render_template_string(LAYOUT_GERAL, title="Cadastro", content=conteudo)

@app.route("/entrar", methods=["GET", "POST"])
def entrar():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")
        with conectar() as conn:
            user = conn.execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()
        if user and check_password_hash(user["senha_hash"], senha):
            session.clear()
            session["usuario_id"] = user["id"]
            session["usuario_nome"] = user["nome"]
            return redirect(url_for("painel"))
        flash("E-mail ou senha incorretos.", "erro")

    conteudo = """
    <div class="auth-container">
        <h2>Entrar no Jogo</h2>
        <form method="POST">
            <div class="campo"><label>E-mail</label><input type="email" name="email" required></div>
            <div class="campo"><label>Senha</label><input type="password" name="senha" required></div>
            <button type="submit" class="btn-submit">Entrar</button>
        </form>
        <div class="auth-footer"><p>Não tem conta? <a href=""" + url_for('cadastro') + """>Cadastre-se</a></p></div>
    </div>
    """
    return render_template_string(LAYOUT_GERAL, title="Entrar", content=conteudo)

@app.route("/sair", methods=["POST"])
def sair():
    session.clear()
    return redirect(url_for("index"))

@app.route("/painel")
@login_obrigatorio
def painel():
    with conectar() as conn:
        prog = conn.execute("SELECT * FROM progresso WHERE usuario_id = ?", (session["usuario_id"],)).fetchone()
    
    pontos = prog["pontos"] if prog else 0
    fases = prog["fases_concluidas"] if prog else 0
    partidas = prog["partidas"] if prog else 0

    conteudo = f"""
    <div>
        <h2>Painel do Jogador</h2>
        <div style="display: flex; gap: 15px; margin: 20px 0;">
            <div style="background: #252525; padding: 15px; border-radius: 5px; flex: 1;"><h3>Pontos</h3><p style="font-size: 1.5rem; color: #ffcc00;">{pontos}</p></div>
            <div style="background: #252525; padding: 15px; border-radius: 5px; flex: 1;"><h3>Fases</h3><p style="font-size: 1.5rem; color: #5cb85c;">{fases} / 4</p></div>
            <div style="background: #252525; padding: 15px; border-radius: 5px; flex: 1;"><h3>Partidas</h3><p style="font-size: 1.5rem; color: #5bc0de;">{partidas}</p></div>
        </div>
        <div style="text-align: center; margin-top: 30px;">
            <a href="{url_for('jogo')}" style="background: #f0ad4e; color: #111; padding: 15px 30px; text-decoration: none; border-radius: 6px; font-size: 1.2rem; font-weight: bold;">Iniciar Fuga ♟️</a>
        </div>
    </div>
    """
    return render_template_string(LAYOUT_GERAL, title="Painel", content=conteudo)

@app.route("/jogo")
@login_obrigatorio
def jogo():
    conteudo = """
    <div class="jogo-layout">
        <aside class="painel-lateral">
            <h3>Controle da Partida</h3>
            <p><strong>Fase:</strong> <span id="fase">1</span> / 4</p>
            <p><strong>Turnos:</strong> <span id="turnos">20</span></p>
            <p><strong>Plebeus:</strong> <span id="plebeus">3</span></p>
            <button id="btn-reiniciar" class="btn-acao">Reiniciar Fase</button>
        </aside>
        <section class="area-tabuleiro">
            <div id="status-msg" class="status-alerta">Selecione um plebeu para começar a fuga!</div>
            <div id="tabuleiro" class="tabuleiro-xadrez"></div>
        </section>
    </div>
    <script>
        document.addEventListener("DOMContentLoaded", () => {
            const tabuleiro = document.getElementById("tabuleiro");
            const statusMsg = document.getElementById("status-msg");
            const btnReiniciar = document.getElementById("btn-reiniciar");

            let peaoPos = { r: 7, c: 3 };
            let reiPos = { r: 0, c: 4 };
            let guardaPos = { r: 2, c: 2 };
            let saidaPos = { r: 0, c: 7 };

            function desenhar() {
                tabuleiro.innerHTML = "";
                for (let r = 0; r < 8; r++) {
                    for (let c = 0; c < 8; c++) {
                        const casa = document.createElement("div");
                        casa.className = `casa ${(r + c) % 2 === 0 ? 'clara' : 'escura'}`;
                        
                        if (r === peaoPos.r && c === peaoPos.c) {
                            casa.innerHTML = "🛡️"; // Plebeu
                        } else if (r === reiPos.r && c === reiPos.c) {
                            casa.innerHTML = "👑"; // Rei
                        } else if (r === guardaPos.r && c === guardaPos.c) {
                            casa.innerHTML = "🗡️"; // Guarda
                        } else if (r === saidaPos.r && c === saidaPos.c) {
                            casa.innerHTML = "🚪"; // Saída
                        }

                        casa.addEventListener("click", () => moverPlebeu(r, c));
                        tabuleiro.appendChild(casa);
                    }
                }
            }

            function moverPlebeu(r, c) {
                // Movimento ortogonal simples de 1 casa
                let diffR = Math.abs(r - peaoPos.r);
                let diffC = Math.abs(c - peaoPos.c);

                if ((diffR + diffC) === 1) {
                    peaoPos = { r, c };
                    statusMsg.textContent = "Plebeu movido com sucesso!";
                    
                    // Checar vitória
                    if (peaoPos.r === saidaPos.r && peaoPos.c === saidaPos.c) {
                        statusMsg.textContent = "🎉 Vitória! Você escapou da Corte!";
                        alert("Parabéns! Você concluiu a fuga com sucesso!");
                    } else {
                        // Resposta simples da guarda perseguindo
                        if (guardaPos.r < peaoPos.r) guardaPos.r++;
                        else if (guardaPos.r > peaoPos.r) guardaPos.r--;
                    }
                    desenhar();
                } else {
                    statusMsg.textContent = "Movimento inválido! Mova apenas 1 casa adjacente.";
                }
            }

            btnReiniciar.addEventListener("click", () => {
                peaoPos = { r: 7, c: 3 };
                guardaPos = { r: 2, c: 2 };
                statusMsg.textContent = "Fase reiniciada! Selecione uma casa ao lado do plebeu.";
                desenhar();
            });

            desenhar();
        });
    </script>
    """
    return render_template_string(LAYOUT_GERAL, title="Tabuleiro — Fuga dos Plebeus", content=conteudo)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=False)
