import os
import sqlite3
import secrets
from datetime import timedelta
from functools import wraps
from datetime import datetime, timezone
from flask import Flask, Response
from flask import (
    Flask, render_template_string, request, redirect,
    url_for, session, flash, jsonify
)
from werkzeug.security import (
    generate_password_hash, check_password_hash
)

app = Flask(__name__)

# Configurações de Sessão e Banco
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=30)
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'OK'}), 200

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

# Funções Utilitárias e Banco de Dados
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

# Layout Geral HTML
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

# Template HTML do Cadastro / Registro
REGISTRO_HTML = """
<div class="auth-container">
    <h2>Criar Conta</h2>
    <form method="POST">
        <div class="campo">
            <label for="nome">Nome</label>
            <input type="text" id="nome" name="nome" required>
        </div>
        <div class="campo">
            <label for="email">E-mail</label>
            <input type="email" id="email" name="email" required>
        </div>
        <div class="campo">
            <label for="senha">Senha (mínimo 6 dígitos)</label>
            <input type="password" id="senha" name="senha" required>
        </div>
        <button type="submit" class="btn-submit">Cadastrar</button>
    </form>
    <div class="auth-footer">
        <p>Já tem uma conta? <a href="{{ url_for('entrar') }}">Entrar</a></p>
    </div>
</div>
"""

# Template HTML de Login
LOGIN_HTML = """
<div class="auth-container">
    <h2>Entrar</h2>
    <form method="POST">
        <div class="campo">
            <label for="email">E-mail</label>
            <input type="email" id="email" name="email" required>
        </div>
        <div class="campo">
            <label for="senha">Senha</label>
            <input type="password" id="senha" name="senha" required>
        </div>
        <button type="submit" class="btn-submit">Entrar</button>
    </form>
    <div class="auth-footer">
        <p>Não tem uma conta? <a href="{{ url_for('cadastro') }}">Criar Conta</a></p>
    </div>
</div>
"""

# Rotas Principais
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

@app.route("/entrar", methods=["GET", "POST"])
def entrar():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")
        
        with conectar() as conn:
            user = conn.execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()
            
        if user and check_password_hash(user["senha_hash"], senha):
            session.permanent = True
            session["usuario_id"] = user["id"]
            session["usuario_nome"] = user["nome"]
            return redirect(url_for("painel"))
        else:
            flash("E-mail ou senha incorretos.", "erro")
            
    return render_template_string(LAYOUT_GERAL, title="Entrar — JOBOSAN", content=LOGIN_HTML)

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
        <h2>Painel do Jogador — Reino de Valverde</h2>
        <div style="display: flex; gap: 15px; margin: 20px 0;">
            <div style="background: #252525; padding: 15px; border-radius: 5px; flex: 1;"><h3>Pontos</h3><p style="font-size: 1.5rem; color: #ffcc00;">{pontos}</p></div>
            <div style="background: #252525; padding: 15px; border-radius: 5px; flex: 1;"><h3>Fases Concluídas</h3><p style="font-size: 1.5rem; color: #5cb85c;">{fases} / 4</p></div>
            <div style="background: #252525; padding: 15px; border-radius: 5px; flex: 1;"><h3>Partidas</h3><p style="font-size: 1.5rem; color: #5bc0de;">{partidas}</p></div>
        </div>

        <h3 style="margin-top: 30px; color: #ffcc00;">Estágios da Fuga</h3>
        <table style="width: 100%; border-collapse: collapse; margin-top: 10px; background: #252525; border-radius: 6px; overflow: hidden;">
            <thead>
                <tr style="background: #333; text-align: left;">
                    <th style="padding: 10px;">Fase</th>
                    <th style="padding: 10px;">Nome</th>
                    <th style="padding: 10px;">Desafio</th>
                    <th style="padding: 10px;">Pontuação</th>
                </tr>
            </thead>
            <tbody>
                <tr style="border-bottom: 1px solid #444;"><td style="padding: 10px;">1</td><td style="padding: 10px;">🌾 A Vila Fechada</td><td style="padding: 10px;">Labirinto pequeno, poucos guardas — aprenda a ler os caminhos</td><td style="padding: 10px; color: #ffcc00;">100 pontos</td></tr>
                <tr style="border-bottom: 1px solid #444;"><td style="padding: 10px;">2</td><td style="padding: 10px;">🌲 A Floresta Cercada</td><td style="padding: 10px;">Mais paredes, mais soldados — a saída está bem escondida</td><td style="padding: 10px; color: #ffcc00;">250 pontos</td></tr>
                <tr style="border-bottom: 1px solid #444;"><td style="padding: 10px;">3</td><td style="padding: 10px;">🏰 Os Muros do Reino</td><td style="padding: 10px;">Labirinto complexo, guardas em pontos estratégicos — calma e atenção</td><td style="padding: 10px; color: #ffcc00;">400 pontos</td></tr>
                <tr><td style="padding: 10px;">4</td><td style="padding: 10px;">🌅 O Último Portão</td><td style="padding: 10px;">Todos os perseguidores te cercam, labirinto enorme, UMA saída apenas — consegue?</td><td style="padding: 10px; color: #ffcc00;">600 pts + Troféu</td></tr>
            </tbody>
        </table>

        <div style="text-align: center; margin-top: 35px;">
            <a href="{url_for('jogo')}" style="background: #f0ad4e; color: #111; padding: 15px 35px; text-decoration: none; border-radius: 6px; font-size: 1.2rem; font-weight: bold;">Iniciar Fuga ♟️</a>
        </div>
    </div>
    """
    return render_template_string(LAYOUT_GERAL, title="Painel do Jogador — JOBOSAN", content=conteudo)

@app.route("/jogo")
@login_obrigatorio
def jogo():
    conteudo = """
    <div class="jogo-layout">
        <aside class="painel-lateral">
            <h3 id="titulo-fase-painel" style="color: #ffcc00; margin-top: 0;">Fase 1: A Vila Fechada</h3>
            <p><strong>Turnos Restantes:</strong> <span id="turnos">20</span></p>
            <p><strong>Plebeus Vivos:</strong> <span id="plebeus">3</span></p>
            <p id="descricao-desafio" style="font-size: 0.85rem; color: #bbb; margin-top: 10px;">Labirinto pequeno, poucos guardas — aprenda a ler os caminhos</p>
            <button id="btn-reiniciar" class="btn-acao">Reiniciar Fase</button>
        </aside>
        <section class="area-tabuleiro">
            <div id="status-msg" class="status-alerta">Toque no seu plebeu (🛡️) para selecioná-lo!</div>
            <div id="tabuleiro" class="tabuleiro-xadrez"></div>
        </section>
    </div>
    <script>
        document.addEventListener("DOMContentLoaded", () => {
            const tabuleiro = document.getElementById("tabuleiro");
            const statusMsg = document.getElementById("status-msg");
            const btnReiniciar = document.getElementById("btn-reiniciar");
            const spanTurnos = document.getElementById("turnos");
            const spanPlebeus = document.getElementById("plebeus");
            const tituloFasePainel = document.getElementById("titulo-fase-painel");
            const descDesafio = document.getElementById("descricao-desafio");

            let faseAtual = 1;
            let turnos = 20;
            
            const dadosFases = {
                1: { nome: "🌾 A Vila Fechada", desafio: "Labirinto pequeno, poucos guardas — aprenda a ler os caminhos", turnos: 20, saida: {r: 0, c: 7}, plebeusPos: [{r:7, c:2}, {r:7, c:3}, {r:7, c:4}], cortes: [{tipo: 'rei', r: 1, c: 3}, {tipo: 'bispo', r: 2, c: 0}] },
                2: { nome: "🌲 A Floresta Cercada", desafio: "Mais paredes, mais soldados — a saída está bem escondida", turnos: 18, saida: {r: 0, c: 0}, plebeusPos: [{r:7, c:5}, {r:7, c:6}, {r:7, c:7}], cortes: [{tipo: 'rei', r: 3, c: 2}, {tipo: 'rainha', r: 5, c: 3}, {tipo: 'bispo', r: 1, c: 4}] },
                3: { nome: "🏰 Os Muros do Reino", desafio: "Labirinto complexo, guardas em pontos estratégicos — calma e atenção", turnos: 15, saida: {r: 0, c: 3}, plebeusPos: [{r:7, c:1}, {r:7, c:2}, {r:7, c:3}, {r:7, c:4}], cortes: [{tipo: 'rei', r: 1, c: 3}, {tipo: 'rainha', r: 3, c: 5}, {tipo: 'bispo', r: 4, c: 1}, {tipo: 'bispo', r: 2, c: 6}] },
                4: { nome: "🌅 O Último Portão", desafio: "Todos os perseguidores te cercam, labirinto enorme, UMA saída apenas — consegue?", turnos: 12, saida: {r: 0, c: 7}, plebeusPos: [{r:7, c:0}, {r:7, c:1}, {r:7, c:2}, {r:7, c:3}], cortes: [{tipo: 'rei', r: 1, c: 4}, {tipo: 'rainha', r: 3, c: 3}, {tipo: 'rainha', r: 5, c: 6}, {tipo: 'bispo', r: 2, c: 1}] }
            };

            let config = dadosFases[faseAtual];
            let plebeus = JSON.parse(JSON.stringify(config.plebeusPos));
            let cortes = JSON.parse(JSON.stringify(config.cortes));
            let indiceSelecionado = null;

            function atualizarPainel() {
                tituloFasePainel.textContent = `Fase ${faseAtual}: ${config.nome}`;
                descDesafio.textContent = config.desafio;
                spanTurnos.textContent = turnos;
                spanPlebeus.textContent = plebeus.length;
            }

            function desenhar() {
                tabuleiro.innerHTML = "";
                atualizarPainel();

                for (let r = 0; r < 8; r++) {
                    for (let c = 0; c < 8; c++) {
                        const casa = document.createElement("div");
                        casa.className = `casa ${(r + c) % 2 === 0 ? 'clara' : 'escura'}`;
                        
                        if (r === config.saida.r && c === config.saida.c) {
                            casa.innerHTML = "🚪";
                        }

                        plebeus.forEach((p, idx) => {
                            if (p.r === r && p.c === c) {
                                casa.innerHTML = "🛡️";
                                if (indiceSelecionado === idx) {
                                    casa.style.border = "3px solid #ffcc00";
                                    casa.style.backgroundColor = "#444";
                                }
                            }
                        });

                        cortes.forEach(cp => {
                            if (cp.r === r && cp.c === c) {
                                if (cp.tipo === 'rei') casa.innerHTML = "👑";
                                else if (cp.tipo === 'rainha') casa.innerHTML = "♕";
                                else if (cp.tipo === 'bispo') casa.innerHTML = "♗";
                            }
                        });

                        let cr = r, cc = c;
                        casa.addEventListener("click", () => lidarClique(cr, cc));
                        tabuleiro.appendChild(casa);
                    }
                }
            }

            function lidarClique(r, c) {
                let clicadoIdx = plebeus.findIndex(p => p.r === r && p.c === c);
                if (clicadoIdx !== -1) {
                    indiceSelecionado = clicadoIdx;
                    statusMsg.textContent = `Plebeu selecionado! Toque em uma casa vizinha para mover.`;
                    desenhar();
                    return;
                }

                if (indiceSelecionado !== null) {
                    let p = plebeus[indiceSelecionado];
                    let diffR = Math.abs(r - p.r);
                    let diffC = Math.abs(c - p.c);

                    if ((diffR + diffC) === 1) {
                        p.r = r;
                        p.c = c;
                        indiceSelecionado = null;
                        turnos--;

                        if (r === config.saida.r && c === config.saida.c) {
                            statusMsg.textContent = "✨ Um plebeu escapou para a liberdade!";
                            plebeus.splice(indiceSelecionado !== null ? indiceSelecionado : 0, 1);
                        }

                        moverCorte();
                        verificarCaptura();

                        if (plebeus.length === 0) {
                            alert(`Vitória na fase ${faseAtual} (${config.nome})!`);
                            avancarFase();
                            return;
@app.route("/jogo")
@login_obrigatorio
def jogo():
    conteudo = """
    <div class="jogo-layout">
        <aside class="painel-lateral">
            <h3 id="titulo-fase-painel" style="color:#ffcc00; margin-top:0;">
                Fase 1
            </h3>

            <p><strong>Turnos restantes:</strong> <span id="turnos">20</span></p>
            <p><strong>Plebeus vivos:</strong> <span id="plebeus">3</span></p>

            <p id="descricao-desafio" style="font-size:0.85rem; color:#bbb; margin-top:10px;"></p>

            <button id="btn-reiniciar" class="btn-acao">
                Reiniciar Fase
            </button>
        </aside>

        conteudo += """
        </aside>

        <section class="area-tabuleiro">
            <div id="status-msg" class="status-alerta">
                Toque em um plebeu (🛡️) para selecioná-lo!
            </div>

            <div id="tabuleiro" class="tabuleiro-xadrez"></div>
        </section>
    </div>

    <script>
    document.addEventListener("DOMContentLoaded", function () {

        // AQUI CONTINUA TODO O SEU JAVASCRIPT ORIGINAL

    });
    </script>
"""
    document.addEventListener("DOMContentLoaded", function () {

        const tabuleiro = document.getElementById("tabuleiro");
        const statusMsg = document.getElementById("status-msg");
        const btnReiniciar = document.getElementById("btn-reiniciar");
        const spanTurnos = document.getElementById("turnos");
        const spanPlebeus = document.getElementById("plebeus");
        const tituloFasePainel = document.getElementById("titulo-fase-painel");
        const descDesafio = document.getElementById("descricao-desafio");

        let faseAtual = 1;
        let turnos = 20;
        let indiceSelecionado = null;

        const dadosFases = {
            1: {
                nome: "🌾 A Vila Fechada",
                desafio: "Labirinto pequeno, poucos guardas — aprenda a ler os caminhos",
                turnos: 20,
                saida: {r: 0, c: 7},
                plebeusPos: [
                    {r: 7, c: 2},
                    {r: 7, c: 3},
                    {r: 7, c: 4}
                ],
                cortes: [
                    {tipo: "rei", r: 1, c: 3},
                    {tipo: "bispo", r: 2, c: 0}
                ]
            },

            2: {
                nome: "🌲 A Floresta Cercada",
                desafio: "Mais guardas — encontre a saída e proteja os plebeus",
                turnos: 18,
                saida: {r: 0, c: 0},
                plebeusPos: [
                    {r: 7, c: 5},
                    {r: 7, c: 6},
                    {r: 7, c: 7}
                ],
                cortes: [
                    {tipo: "rei", r: 3, c: 2},
                    {tipo: "rainha", r: 5, c: 3},
                    {tipo: "bispo", r: 1, c: 4}
                ]
            },

            3: {
                nome: "🏰 Os Muros do Reino",
                desafio: "Mais perseguidores em pontos estratégicos",
                turnos: 15,
                saida: {r: 0, c: 3},
                plebeusPos: [
                    {r: 7, c: 1},
                    {r: 7, c: 2},
                    {r: 7, c: 3},
                    {r: 7, c: 4}
                ],
                cortes: [
                    {tipo: "rei", r: 1, c: 3},
                    {tipo: "rainha", r: 3, c: 5},
                    {tipo: "bispo", r: 4, c: 1},
                    {tipo: "bispo", r: 2, c: 6}
                ]
            },

            4: {
                nome: "🌅 O Último Portão",
                desafio: "Todos os perseguidores estão em campo. Encontre a única saída!",
                turnos: 12,
                saida: {r: 0, c: 7},
                plebeusPos: [
                    {r: 7, c: 0},
                    {r: 7, c: 1},
                    {r: 7, c: 2},
                    {r: 7, c: 3}
                ],
                cortes: [
                    {tipo: "rei", r: 1, c: 4},
                    {tipo: "rainha", r: 3, c: 3},
                    {tipo: "rainha", r: 5, c: 6},
                    {tipo: "bispo", r: 2, c: 1}
                ]
            }
        };

        let config;
        let plebeus = [];
        let cortes = [];

        function atualizarPainel() {
            tituloFasePainel.textContent =
                "Fase " + faseAtual + ": " + config.nome;

            descDesafio.textContent = config.desafio;
            spanTurnos.textContent = turnos;
            spanPlebeus.textContent = plebeus.length;
        }

        function reiniciarFase() {
            config = dadosFases[faseAtual];

            turnos = config.turnos;

            plebeus = JSON.parse(
                JSON.stringify(config.plebeusPos)
            );

            cortes = JSON.parse(
                JSON.stringify(config.cortes)
            );

            indiceSelecionado = null;

            statusMsg.textContent =
                "Fase " + faseAtual + " iniciada! Encontre a saída.";

            desenhar();
        }

        function desenhar() {
            tabuleiro.innerHTML = "";

            atualizarPainel();

            for (let r = 0; r < 8; r++) {
                for (let c = 0; c < 8; c++) {

                    const casa = document.createElement("div");

                    casa.className =
                        "casa " + ((r + c) % 2 === 0 ? "clara" : "escura");

                    if (
                        r === config.saida.r &&
                        c === config.saida.c
                    ) {
                        casa.innerHTML = "🚪";
                    }

                    plebeus.forEach(function (p, idx) {
                        if (p.r === r && p.c === c) {
                            casa.innerHTML = "🛡️";

                            if (indiceSelecionado === idx) {
                                casa.style.border = "3px solid #ffcc00";
                                casa.style.backgroundColor = "#444";
                            }
                        }
                    });

                    cortes.forEach(function (cp) {
                        if (cp.r === r && cp.c === c) {

                            if (cp.tipo === "rei") {
                                casa.innerHTML = "👑";
                            } else if (cp.tipo === "rainha") {
                                casa.innerHTML = "♕";
                            } else if (cp.tipo === "bispo") {
                                casa.innerHTML = "♗";
                            }
                        }
                    });

                    casa.addEventListener("click", function () {
                        lidarClique(r, c);
                    });

                    tabuleiro.appendChild(casa);
                }
            }
        }

        function lidarClique(r, c) {

            const clicadoIdx = plebeus.findIndex(function (p) {
                return p.r === r && p.c === c;
            });

            if (clicadoIdx !== -1) {
                indiceSelecionado = clicadoIdx;

                statusMsg.textContent =
                    "Plebeu selecionado! Escolha uma casa vizinha.";

                desenhar();
                return;
            }

            if (indiceSelecionado === null) {
                statusMsg.textContent =
                    "Selecione um plebeu primeiro.";
                return;
            }

            const p = plebeus[indiceSelecionado];

            const diffR = Math.abs(r - p.r);
            const diffC = Math.abs(c - p.c);

            if ((diffR + diffC) !== 1) {
                statusMsg.textContent =
                    "Movimento inválido! Mova apenas uma casa por vez.";
                return;
            }

            const ocupadoPorPlebeu = plebeus.some(function (outro, idx) {
                return idx !== indiceSelecionado &&
                       outro.r === r && outro.c === c;
            });

            if (ocupadoPorPlebeu) {
                statusMsg.textContent =
                    "Essa casa já está ocupada por outro plebeu.";
                return;
            }

            const ocupadoPelaCorte = cortes.some(function (cp) {
                return cp.r === r && cp.c === c;
            });

            if (ocupadoPelaCorte) {
                statusMsg.textContent =
                    "A Corte está nessa casa! Escolha outro caminho.";
                return;
            }

            // Guarda o índice antes de remover o plebeu.
            const indiceMovido = indiceSelecionado;

            p.r = r;
            p.c = c;

            turnos--;
            indiceSelecionado = null;

            // Verifica se o plebeu chegou à saída.
            if (
                r === config.saida.r &&
                c === config.saida.c
            ) {
                plebeus.splice(indiceMovido, 1);

                statusMsg.textContent =
                    "✨ Um plebeu conseguiu escapar!";

                // Se todos escaparam, a fase termina imediatamente.
                if (plebeus.length === 0) {
                    alert(
                        "🏆 Vitória! Todos os plebeus conseguiram escapar!"
                    );

                    avancarFase();
                    return;
                }
            }

            // Todos os perseguidores tentam avançar uma vez.
            moverCorte();

            const todosCapturados = verificarCaptura();

            if (todosCapturados) {
                alert(
                    "A Corte capturou todos os plebeus. Tente novamente!"
                );

                reiniciarFase();
                return;
            }

            if (turnos <= 0) {
                alert(
                    "O tempo acabou! A fase será reiniciada."
                );

                reiniciarFase();
                return;
            }

            desenhar();
        }

        function moverCorte() {

            const movimentosTodos = [
                {r: -1, c: -1},
                {r: -1, c: 0},
                {r: -1, c: 1},
                {r: 0, c: -1},
                {r: 0, c: 1},
                {r: 1, c: -1},
                {r: 1, c: 0},
                {r: 1, c: 1}
            ];

            const movimentosBispo = [
                {r: -1, c: -1},
                {r: -1, c: 1},
                {r: 1, c: -1},
                {r: 1, c: 1}
            ];

            cortes.forEach(function (cp) {

                if (plebeus.length === 0) {
                    return;
                }

                // Cada perseguidor procura o plebeu mais próximo.
                let alvo = plebeus[0];
                let menorDistancia = Infinity;

                plebeus.forEach(function (p) {
                    const distancia =
                        Math.abs(p.r - cp.r) +
                        Math.abs(p.c - cp.c);

                    if (distancia < menorDistancia) {
                        menorDistancia = distancia;
                        alvo = p;
                    }
                });

                // O bispo só pode andar na diagonal.
                // Rei e rainha avançam uma casa em qualquer direção.
                const movimentos =
                    cp.tipo === "bispo"
                    ? movimentosBispo
                    : movimentosTodos;

                const candidatos = [];

                movimentos.forEach(function (mov) {

                    const novoR = cp.r + mov.r;
                    const novoC = cp.c + mov.c;

                    // Não permite sair do tabuleiro.
                    if (
                        novoR < 0 || novoR > 7 ||
                        novoC < 0 || novoC > 7
                    ) {
                        return;
                    }

                    // Não permite que perseguidores ocupem a mesma casa.
                    const casaOcupada = cortes.some(function (outro) {
                        return outro !== cp &&
                               outro.r === novoR &&
                               outro.c === novoC;
                    });

                    if (casaOcupada) {
                        return;
                    }

                    const distanciaAlvo =
                        Math.abs(alvo.r - novoR) +
                        Math.abs(alvo.c - novoC);

                    candidatos.push({
                        r: novoR,
                        c: novoC,
                        distancia: distanciaAlvo
                    });
                });

                if (candidatos.length === 0) {
                    return;
                }

                // Escolhe a casa que aproxima o perseguidor do alvo.
                candidatos.sort(function (a, b) {
                    return a.distancia - b.distancia;
                });

                cp.r = candidatos[0].r;
                cp.c = candidatos[0].c;
            });
        }

        function verificarCaptura() {

            const quantidadeAntes = plebeus.length;

            plebeus = plebeus.filter(function (p) {

                const capturado = cortes.some(function (cp) {
                    return cp.r === p.r && cp.c === p.c;
                });

                if (capturado) {
                    statusMsg.textContent =
                        "⚔️ Um plebeu foi capturado pela Corte!";
                }

                return !capturado;
            });

            atualizarPainel();

            return quantidadeAntes > 0 && plebeus.length === 0;
        }

        function avancarFase() {

            if (faseAtual < 4) {
                faseAtual++;

                alert("Parabéns! Você avançou para a fase " + faseAtual + ".");

                reiniciarFase();

            } else {

                alert(
                    "🏆 Parabéns! Você conquistou o Troféu Liberdade!"
                );

                faseAtual = 1;
                reiniciarFase();
            }
        }

        btnReiniciar.addEventListener("click", function () {
            reiniciarFase();
        });

        reiniciarFase();
    });
    </script>
    """

    return render_template_string(
        LAYOUT_GERAL,
        title="Fuga dos Plebeus — Jogo",
        content=conteudo
    )
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

                session.permanent = True
                session["usuario_id"] = uid
                session["usuario_nome"] = nome
                
                return redirect(url_for("painel"))
            except sqlite3.IntegrityError:
                flash("Este e-mail já está cadastrado.", "erro")

    return render_template_string(LAYOUT_GERAL, title="Criar Conta — JOBOSAN", content=REGISTRO_HTML)

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )
