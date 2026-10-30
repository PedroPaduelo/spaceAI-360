"""Enriquecimento v2 (camada de apresentacao) — idempotente.
Uso: python3 enriquecer.py <arquivo.html> [<arquivo2.html> ...]
- CSS: painel lateral maior (sem tocar no SVG).
- Card 'Como ler este diagrama' no topo do painel.
- Card 'Glossario' no fim do painel.
- JS: auto-enquadra uma vez apos carregar (equivale a apertar 0).
Marca: enriquecimento-v2. Roda de novo sem duplicar.
"""
import re, sys, shutil

CSS = """
<style id="enriquecimento-v2">
.reader-rail .cards{font-size:16px !important;line-height:1.7 !important}
.reader-rail .card h3{font-size:17px !important;line-height:1.4 !important}
.reader-rail .card li{margin-bottom:8px !important}
.reader-rail .card{padding:16px 18px !important}
.diagram-guide,.node-finder{font-size:15px !important;line-height:1.65 !important}
.reader-rail kbd{background:rgba(127,127,127,.18);border:1px solid rgba(127,127,127,.35);border-radius:4px;padding:0 5px;font-size:.85em}
@media (max-width:900px){.reader-rail .cards{font-size:15px !important}}
</style>"""

CARD_LER = """
      <div class="card" id="card-como-ler">
        <div class="card-header">
          <div class="card-dot emerald"></div>
          <h3>Como ler este diagrama</h3>
        </div>
        <ul>
          <li><b>Enquadrar tudo na tela:</b> aperte <kbd>0</kbd> (ou o botao % do canto). Se ainda precisar rolar, o fluxo e grande — use <kbd>F</kbd> para o modo apresentacao em tela cheia.</li>
          <li><b>Zoom com qualidade:</b> <kbd>+</kbd> e <kbd>-</kbd> ampliam sem borrar (e vetor, nao imagem). Para ver o geral, volte com <kbd>0</kbd>.</li>
          <li><b>Achar um no:</b> <kbd>/</kbd> busca por nome, responsabilidade ou id estavel.</li>
          <li><b>Seguir uma chamada:</b> <kbd>R</kbd> traca a rota entre dois nos na direcao documentada.</li>
          <li><b>Claro/escuro:</b> <kbd>T</kbd> troca o tema. <kbd>E</kbd> exporta PNG/WebP/SVG.</li>
          <li><b>Caixinhas clicaveis:</b> cada no abre detalhes (entradas, saidas, erros). As evidencias entre parenteses (arquivo:linha) apontam o codigo-fonte exato.</li>
        </ul>
      </div>
"""

CARD_GLOSS = """
      <div class="card" id="card-glossario">
        <div class="card-header">
          <div class="card-dot slate"></div>
          <h3>Glossario</h3>
        </div>
        <ul>
          <li><b>MCP</b> — Model Context Protocol: o canal pelo qual o agente chama tools (pedido/resposta em JSON).</li>
          <li><b>Tool / tool call</b> — funcao que o agente invoca; <i>handler</i> valida e executa, <i>service</i> contem a regra de negocio.</li>
          <li><b>Escopo (scope)</b> — permissao exigida (<i>read</i> le, <i>write</i>/<i>github:write</i> escreve). Sem escopo, a chamada e recusada antes do banco.</li>
          <li><b>Anti-BOLA</b> — checagem de que o chamador so enxerga objetos do proprio projeto (BOLA = acessar objeto alheio trocando o id).</li>
          <li><b>Envelope / isError</b> — resposta padrao <i>{ok, data}</i> ou <i>{ok:false, error}</i>; <i>isError</i> avisa a interface que deu erro.</li>
          <li><b>Zod</b> — validador dos argumentos (tipo, tamanho, formato) antes de qualquer I/O.</li>
          <li><b>Prisma</b> — ORM do banco Postgres; <i>findUnique/findMany</i> leem, transacoes gravam tudo-ou-nada.</li>
          <li><b>Transacao / FOR UPDATE</b> — trava a linha durante a escrita para duas execucoes nao se atropelarem.</li>
          <li><b>Lease / claim</b> — reserva temporaria ("estou cuidando disso"); idempotente = repetir nao duplica.</li>
          <li><b>OIDC / JWT / RBAC</b> — login federado / token de sessao / permissao por papel.</li>
          <li><b>SSE / WebSocket</b> — a resposta do modelo desce em eventos de texto ao vivo.</li>
          <li><b>FTS / trigram / RRF</b> — busca textual: indice de texto, similaridade de trigramas e fusao de rankings.</li>
        </ul>
      </div>
"""

JS = """
<script id="enriquecimento-v2-js">
(function(){var n=0;var t=setInterval(function(){try{var b=document.querySelector('[data-view="reset"]');if(b){b.click();clearInterval(t);}}catch(e){}if(++n>25)clearInterval(t);},400);})();
</script>"""


def fechar_cards(html, start):
    """A partir do <div class="cards"> em start, acha o </div> que o fecha (contando divs). Retorna indice do inicio desse </div>."""
    tag = re.compile(r"<(/?)div\b[^>]*>", re.I)
    depth = 0
    for m in tag.finditer(html, start):
        if m.group(1) == "":
            depth += 1
        else:
            depth -= 1
            if depth == 0:
                return m.start()
    return -1


def enriquecer(path):
    s = open(path, encoding="utf-8", errors="ignore").read()
    if 'id="enriquecimento-v2"' in s:
        return "ja-enriquecido"
    shutil.copy(path, path + ".bak-v2")
    if "</head>" in s:
        s = s.replace("</head>", CSS + "\n</head>", 1)
    abertura = s.find('<div class="cards">')
    if abertura == -1:
        return "sem-painel-cards"
    s = s[:abertura + len('<div class="cards">')] + CARD_LER + s[abertura + len('<div class="cards">'):]
    # recalcula: o fechamento deslocou; reacha a partir da abertura
    abertura2 = s.find('<div class="cards">')
    fim = fechar_cards(s, abertura2)
    if fim == -1:
        return "fecho-nao-achado"
    s = s[:fim] + CARD_GLOSS + "\n" + s[fim:]
    if "</body>" in s:
        s = s.replace("</body>", JS + "\n</body>", 1)
    else:
        s = s + JS
    s = s.replace("</html>", "<!-- enriquecimento-v2: tipografia + como-ler + glossario + auto-fit -->\n</html>", 1)
    open(path, "w", encoding="utf-8").write(s)
    return "ok"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("uso: enriquecer.py arquivo.html [...]")
    else:
        for p in sys.argv[1:]:
            try:
                print(p, "->", enriquecer(p))
            except Exception as e:
                print(p, "-> ERRO:", e)
