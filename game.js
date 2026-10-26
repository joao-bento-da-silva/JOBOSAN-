(() => {
  const tamanho = 8;
  const fases = [
    {nome:"Fase 1: O Cerco Inicial", turnos:20, meta:3, pontos:100, nobres:1},
    {nome:"Fase 2: A Guarda Avança", turnos:18, meta:4, pontos:150, nobres:1},
    {nome:"Fase 3: A Fúria do Rei", turnos:15, meta:5, pontos:200, nobres:2},
    {nome:"Fase 4: Fuga Final", turnos:12, meta:6, pontos:300, nobres:2}
  ];
  // # são paredes. E é saída. Os corredores foram desenhados para manter rotas.
  const mapa = [
    "...E....",
    ".##..#..",
    "...#....",
    "#..#.#..",
    "...#....",
    "..##..#.",
    "........",
    "........"
  ];
  const el = id => document.getElementById(id);
  let tab, fase, turno, salvos, capturados, pontos, selecionada, status, mensagem;
  let pontosPartida = 0, fasesPartida = 0, resultadoEnviado = false;

  function iniciar() {
    tab = mapa.map(l => [...l].map(x => x === "." ? "" : x));
    tab[0][0] = "K"; tab[0][7] = "Q"; tab[2][7] = "B";
    for (let c=1;c<=6;c++) tab[7][c] = "P";
    fase=0; turno=0; salvos=0; capturados=0; pontos=0;
    selecionada=null; status="jogando"; mensagem="Selecione um plebeu para começar.";
    pontosPartida=0; fasesPartida=0; resultadoEnviado=false;
    desenhar();
  }

  const dentro=(r,c)=>r>=0&&r<8&&c>=0&&c<8;
  const nobre=p=>["K","Q","B"].includes(p);
  const direcoesRei=[[-1,-1],[-1,0],[-1,1],[0,-1],[0,1],[1,-1],[1,0],[1,1]];
  function movimentosNobre(r,c,tipo) {
    const dirs = tipo==="B" ? [[-1,-1],[-1,1],[1,-1],[1,1]] : direcoesRei;
    const max = tipo==="K" ? 1 : 7;
    const out=[];
    for(const [dr,dc] of dirs) for(let passo=1;passo<=max;passo++){
      const nr=r+dr*passo,nc=c+dc*passo;
      if(!dentro(nr,nc)) break;
      const p=tab[nr][nc];
      if(p==="#"||p==="E"||nobre(p)) break;
      out.push([nr,nc]);
      if(p==="P"||tipo==="K") break;
    }
    return out;
  }

  function distancias(inicio) {
    const dist=new Map(), fila=[inicio];
    dist.set(inicio.join(","),0);
    for(let i=0;i<fila.length;i++){
      const [r,c]=fila[i], d=dist.get([r,c].join(","));
      for(const [dr,dc] of [[-1,0],[1,0],[0,-1],[0,1]]){
        const nr=r+dr,nc=c+dc,k=[nr,nc].join(",");
        if(!dentro(nr,nc)||dist.has(k))continue;
        const p=tab[nr][nc];
        if(p==="#"||p==="E"||nobre(p))continue;
        dist.set(k,d+1);fila.push([nr,nc]);
      }
    }
    return dist;
  }

  function moverCorte(qtd) {
    for(let i=0;i<qtd;i++){
      const ps=[], ns=[];
      for(let r=0;r<8;r++)for(let c=0;c<8;c++){
        if(tab[r][c]==="P")ps.push([r,c]);
        else if(nobre(tab[r][c]))ns.push([r,c,tab[r][c]]);
      }
      if(!ps.length) return;
      ns.sort(()=>Math.random()-.5);
      let best=null, bestD=Infinity, captura=false;
      for(const [r,c,tipo] of ns){
        for(const [nr,nc] of movimentosNobre(r,c,tipo)){
          if(tab[nr][nc]==="P"){best=[r,c,nr,nc,tipo];captura=true;break;}
          const ds=distancias([nr,nc]);
          const d=Math.min(...ps.map(p=>ds.get(p.join(","))??999));
          if(d<bestD){bestD=d;best=[r,c,nr,nc,tipo];captura=false;}
        }
        if(captura)break;
      }
      if(!best)continue;
      const [r,c,nr,nc,tipo]=best;
      if(captura){capturados++;mensagem="A corte capturou um plebeu! Proteja os restantes.";}
      tab[r][c]="";tab[nr][nc]=tipo;
    }
  }

  function terminarPartida() {
    if(resultadoEnviado)return;
    resultadoEnviado=true;
    fetch("/api/resultado",{
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify({pontos:pontosPartida,fases_concluidas:fasesPartida})
    }).catch(()=>{});
  }

  function verificar() {
    const cfg=fases[fase];
    const restantes=tab.flat().filter(p=>p==="P").length;
    if(salvos>=cfg.meta){
      fasesPartida=Math.max(fasesPartida,fase+1);
      if(fase===3){
        status="vitoria";mensagem="Vitória! Você concluiu as quatro fases!";terminarPartida();
      }else{
        fase++;turno=0;salvos=0;
        tab=mapa.map(l=>[...l].map(x=>x==="."?"":x));
        tab[0][0]="K";tab[0][7]="Q";tab[2][7]="B";
        for(let c=1;c<=6;c++)tab[7][c]="P";
        selecionada=null;mensagem=`Fase concluída! Bem-vindo à fase ${fase+1}.`;
      }
      return;
    }
    if(turno>=cfg.turnos||restantes+salvos<cfg.meta){
      status="derrota";mensagem="Fim de jogo! A corte venceu esta fase. Tente novamente.";terminarPartida();
    }
  }

  function jogar(r,c) {
    if(status!=="jogando")return;
    if(selecionada===null){
      if(tab[r][c]==="P"){selecionada=[r,c];mensagem="Plebeu selecionado. Escolha uma casa adjacente.";}
      else mensagem="Selecione um plebeu.";
      desenhar();return;
    }
    if(tab[r][c]==="P"){selecionada=[r,c];mensagem="Outro plebeu foi selecionado.";desenhar();return;}
    const [r1,c1]=selecionada;
    if(Math.abs(r-r1)+Math.abs(c-c1)!==1 || !["","E"].includes(tab[r][c])){
      mensagem="Movimento inválido. Mova uma casa para cima, baixo, esquerda ou direita, sem atravessar paredes.";
      desenhar();return;
    }
    const destino=tab[r][c];tab[r1][c1]="";selecionada=null;turno++;
    if(destino==="E"){
      salvos++;pontos+=fases[fase].pontos;pontosPartida+=fases[fase].pontos;
      mensagem="Plebeu salvo! Ele escapou e não volta ao tabuleiro.";
    }else{tab[r][c]="P";mensagem="Movimento realizado.";}
    if(salvos<fases[fase].meta)moverCorte(fases[fase].nobres);
    verificar();desenhar();
  }

  function desenhar() {
    const board=el("tabuleiro");board.innerHTML="";
    const cfg=fases[fase];
    for(let r=0;r<8;r++)for(let c=0;c<8;c++){
      const p=tab[r][c],b=document.createElement("button");
      b.type="button";b.className="casa "+((r+c)%2===0?"clara":"escura");
      b.setAttribute("aria-label",`Casa ${r+1}, ${c+1}`);
      if(p==="#"){b.classList.add("parede");b.textContent="■";b.disabled=true;}
      else if(p==="E"){b.classList.add("saida");b.textContent="⇧";b.title="Saída";}
      else if(p==="P")b.textContent="♟";
      else if(p==="K")b.textContent="♚";
      else if(p==="Q")b.textContent="♛";
      else if(p==="B")b.textContent="♝";
      if(selecionada&&selecionada[0]===r&&selecionada[1]===c)b.classList.add("selecionada");
      if(selecionada&&Math.abs(r-selecionada[0])+Math.abs(c-selecionada[1])===1&&["","E"].includes(p))b.classList.add("destino");
      b.disabled=b.disabled||status!=="jogando";
      b.addEventListener("click",()=>jogar(r,c));board.appendChild(b);
    }
    el("fase-nome").textContent=cfg.nome;
    el("turno").textContent=`${turno} / ${cfg.turnos}`;
    el("salvos").textContent=`${salvos} / ${cfg.meta}`;
    el("capturados").textContent=capturados;
    el("pontos").textContent=pontos;
    el("mensagem").textContent=mensagem;
    if(status!=="jogando"){
      const final=document.createElement("p");
      final.className="mensagem";
      final.textContent=status==="vitoria"?"Partida vencida!":"Partida encerrada.";
      board.after(final);
    }else{
      const extra=board.nextElementSibling;
      if(extra&&extra.classList.contains("mensagem"))extra.remove();
    }
  }
  el("reiniciar").addEventListener("click",iniciar);
  iniciar();
})();
