 {% extends "base.html" %}
{% block conteudo %}
<div class="area-batalha">
    <h2>🏰 Fuga dos Gladiadores no Castelo</h2>
    
    <div class="status-jogo">
        <p>Gladiadores: <span id="qtd-gladiadores">4</span> | Turno: <span id="turno-atual">1</span> / 20 | <a href="{{ url_for('painel') }}">Sair para o Painel</a></p>
    </div>

    <!-- É ESTA CAIXINHA QUE FALTAVA DESENHAR O LABIRINTO NA TELA! -->
    <div id="tabuleiro-labirinto" class="tabuleiro-grid"></div>

    <div class="painel-comandos">
        <h3>Comandos do Gladiador</h3>
        <div class="botoes-direcao">
            <button class="btn-acao" onclick="moverGladiador('cima')">⬆️ Cima</button>
            <div class="botoes-meio">
                <button class="btn-acao" onclick="moverGladiador('esquerda')">⬅️ Esquerda</button>
                <button class="btn-acao" onclick="moverGladiador('direita')">➡️ Direita</button>
            </div>
            <button class="btn-acao" onclick="moverGladiador('baixo')">⬇️ Baixo</button>
        </div>
        <button class="btn-ataque" onclick="tentarContraAtaque()">⚔️ Contra-Atacar Nobreza</button>
    </div>
</div>

<!-- Importa o script do jogo -->
<script src="{{ url_for('static', filename='game.js') }}"></script>
{% endblock %}
