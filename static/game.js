document.addEventListener("DOMContentLoaded", () => {
  const boardEl = document.getElementById("tabuleiro");
  const msgEl = document.getElementById("instrucoes");
  
  let selectedPiece = null;

  // Matriz de exemplo para o tabuleiro 8x8
  // P = Plebeu, R = Rei, Q = Rainha, B = Bispo, W = Parede, E = Saída, . = Vazio
  const initialMap = [
    ['.', '.', '.', 'W', 'E', 'W', '.', '.'],
    ['.', 'B', '.', '.', '.', '.', 'Q', '.'],
    ['.', '.', '.', 'W', 'W', '.', '.', '.'],
    ['.', 'P', '.', '.', '.', '.', 'P', '.'],
    ['.', '.', 'R', '.', '.', '.', '.', '.'],
    ['.', '.', '.', '.', 'W', '.', '.', '.'],
    ['.', 'P', '.', '.', '.', '.', '.', '.'],
    ['.', '.', '.', '.', '.', '.', '.', '.']
  ];

  const pieceIcons = {
    'P': '♟️',
    'R': '♚',
    'Q': '♛',
    'B': '♝',
    'W': '⬛',
    'E': '🚪'
  };

  function renderBoard() {
    boardEl.innerHTML = '';
    for (let r = 0; r < 8; r++) {
      for (let c = 0; c < 8; c++) {
        const cell = document.createElement('div');
        const isDark = (r + c) % 2 === 1;
        
        cell.classList.add('cell', isDark ? 'dark' : 'light');
        cell.dataset.row = r;
        cell.dataset.col = c;

        const val = initialMap[r][c];
        if (val === 'W') cell.classList.add('wall');
        if (val === 'E') cell.classList.add('exit');
        if (pieceIcons[val]) cell.textContent = pieceIcons[val];

        cell.addEventListener('click', () => handleCellClick(r, c, val, cell));
        boardEl.appendChild(cell);
      }
    }
  }

  function handleCellClick(r, c, val, cellEl) {
    if (val === 'P') {
      // Seleciona Plebeu
      document.querySelectorAll('.cell').forEach(el => el.classList.remove('selected'));
      cellEl.classList.add('selected');
      selectedPiece = { r, c };
      msgEl.textContent = `Plebeu selecionado em (${r+1}, ${c+1}). Clique para mover!`;
    } else if (selectedPiece) {
      // Move o Plebeu
      msgEl.textContent = `Movendo de (${selectedPiece.r+1}, ${selectedPiece.col+1}) para (${r+1}, ${c+1})...`;
      initialMap[selectedPiece.r][selectedPiece.c] = '.';
      initialMap[r][c] = 'P';
      selectedPiece = null;
      renderBoard();
    }
  }

  document.getElementById("btn-reiniciar").addEventListener("click", () => {
    location.reload();
  });

  renderBoard();
});
