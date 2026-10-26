// Estado do Jogo: Fuga dos Gladiadores
let estadoJogo = {
    turno: 1,
    limiteTurnos: 20,
    qtdGladiadores: 4,
    gladiadoresAtivos: 4,
    // Posições no grid (exemplo de grade 8x8)
    posicaoSaida: { x: 7, y: 7 }, 
    gladiadores: [
        { id: 1, x: 0, y: 0, vivo: true },
        { id: 2, x: 0, y: 1, vivo: true },
        { id: 3, x: 1, y: 0, vivo: true },
        { id: 4, x: 1, y: 1, vivo: true }
    ],
    nobres: [
        { tipo: 'Rei', x: 4, y: 4 },
        { tipo: 'Rainha', x: 5, y: 3 },
        { tipo: 'Bispo', x: 3, y: 5 }
    ],
    soldados: [
        { x: 2, y: 2 },
        { x: 5, y: 5 }
    ]
};

// Inicializa o tabuleiro ao carregar a página
document.addEventListener("DOMContentLoaded", () => {
    sortearSaidaDinamica();
    renderizarTabuleiro();
});

// Sorteia uma nova posição para a saída dinâmica (giratória)
function sortearSaidaDinamica() {
    // Garante que a saída mude de posição de forma aleatória nas bordas do labirinto
    const posicoesBorda = [
        { x: 7, y: 0 }, { x: 7, y: 3 }, { x: 0, y: 7 }, { x: 3, y: 7 }, { x: 7, y: 7 }
    ];
    const escolhaAleatoria = posicoesBorda[Math.floor(Math.random() * posicoesBorda.length)];
    estadoJogo.posicaoSaida = escolhaAleatoria;
}

// Renderiza o labirinto e as peças visualmente
function renderizarTabuleiro() {
    const tabuleiro = document.getElementById("tabuleiro-labirinto");
    if (!tabuleiro) return;
    
    tabuleiro.innerHTML = "";
    document.getElementById("turno-atual").innerText = estadoJogo.turno;
    document.getElementById("qtd-gladiadores").innerText = estadoJogo.gladiadoresAtivos;

    // Criando uma grade 8x8
    for (let y = 0; y < 8; y++) {
        for (let x = 0; x < 8; x++) {
            const celula = document.createElement("div");
            celula.classList.add("celula-labirinto");

            // Verifica se é a Saída Dinâmica
            if (x === estadoJogo.posicaoSaida.x && y === estadoJogo.posicaoSaida.y) {
                celula.classList.add("saida");
                celula.innerHTML = "🚪";
                celula.title = "Saída do Castelo";
            }

            // Verifica se tem Gladiador
            const gladiador = estadoJogo.gladiadores.find(g => g.x === x && g.y === y && g.vivo);
            if (gladiador) {
                celula.classList.add("gladiador");
                celula.innerHTML = `🛡️${gladiador.id}`;
            }

            // Verifica se tem Nobre (Rei, Rainha, Bispo)
            const nobre = estadoJogo.nobres.find(n => n.x === x && n.y === y);
            if (nobre) {
                celula.classList.add("nobre");
                celula.innerHTML = nobre.tipo === 'Rei' ? '👑' : nobre.tipo === 'Rainha' ? '👸' : '♗';
            }

            // Verifica se tem Soldado do Castelo
            const soldado = estadoJogo.soldados.find(s => s.x === x && s.y === y);
            if (soldado) {
                celula.classList.add("soldado");
                celula.innerHTML = "⚔️";
            }

            tabuleiro.appendChild(celula);
        }
    }
}

// Movimentação dos gladiadores
function moverGladiador(direcao) {
    // Move o primeiro gladiador vivo como referência principal do jogador
    let g = estadoJogo.gladiadores.find(gl => gl.vivo);
    if (!g) return;

    let novoX = g.x;
    let novoY = g.y;

    if (direcao === 'cima' && g.y > 0) novoY--;
    if (direcao === 'baixo' && g.y < 7) novoY++;
    if (direcao === 'esquerda' && g.x > 0) novoX--;
    if (direcao === 'direita' && g.x < 7) novoX++;

    // Atualiza posição
    g.x = novoX;
    g.y = novoY;

    // Verifica se chegou na saída dinâmica
    if (g.x === estadoJogo.posicaoSaida.x && g.y === estadoJogo.posicaoSaida.y) {
        alert("🎉 Um gladiador conseguiu escapar do castelo!");
        g.vivo = false;
        estadoJogo.gladiadoresAtivos--;
        
        if (estadoJogo.gladiadoresAtivos === 0) {
            alert("Vitória! Todos os gladiadores escaparam!");
            enviarResultadoServidor(1000, 1);
            return;
        }
    }

    // Passa o turno
    estadoJogo.turno++;
    if (estadoJogo.turno > estadoJogo.limiteTurnos) {
        alert("Fim de jogo! O tempo limite de turnos esgotou.");
        window.location.href = "/painel";
        return;
    }

    renderizarTabuleiro();
}

// Mecânica de Contra-Ataque contra a Nobreza
function tentarContraAtaque() {
    let g = estadoJogo.gladiadores.find(gl => gl.vivo);
    if (!g) return;

    // Verifica se há algum nobre adjacente para atacar
    let indiceNobre = estadoJogo.nobres.findIndex(n => Math.abs(n.x - g.x) <= 1 && Math.abs(n.y - g.y) <= 1);

    if (indiceNobre !== -1) {
        let nobreEliminado = estadoJogo.nobres.splice(indiceNobre, 1)[0];
        alert(`⚔️ Contra-ataque bem-sucedido! O gladiador eliminou o ${nobreEliminado.tipo}!`);
        renderizarTabuleiro();
    } else {
        alert("Nenhum nobre por perto para contra-atacar!");
    }
}

// Envia os pontos para o servidor Flask
function enviarResultadoServidor(pontos, fases) {
    fetch('/api/resultado', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pontos: pontos, fases_concluidas: fases })
    }).then(res => res.json()).then(data => {
        if (data.ok) {
            window.location.href = "/painel";
        }
    });
}
