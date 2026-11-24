# Resolucao 3: Dijkstra O(V^2) em matriz, com testes

Criterio: **robustez de entrada e testabilidade**. E a versao para entregar se
a preocupacao for "vai rodar com mapa estranho sem quebrar" e "da para provar
que esta certo".

    python3 main.py
    python3 tests.py

## Como funciona

- Grafo em matriz de adjacencia, como a resolucao 2, mas a busca e Dijkstra na
  versao classica O(V^2): a cada iteracao escolhe por varredura linear o vertice
  nao fechado de menor distancia. Sem `heapq`, sem dicionario de predecessores:
  so vetores indexados por vertice (`dist`, `anterior`, `fechado`).
- Justificativa: em grafos densos a varredura linear empata ou ganha do heap, e
  nao precisa de tratamento de decrease-key. Para V na ordem de milhares, as
  duas versoes sao instantaneas.
- Caminho reconstruido andando para tras no vetor `anterior`.

## Robustez

- `Mapa.de_texto` (usado por `Mapa.de_arquivo`) valida tudo antes de aceitar:
  cabecalho inteiro, contagem exata de campos, nomes repetidos, vertice
  desconhecido em aresta, laco, peso nao inteiro, peso nao positivo, aresta
  repetida. Qualquer falha levanta `ErroMapa` com mensagem localizada
  (por exemplo `aresta 7 tem peso nao positivo: -3`), e a CLI mostra o erro sem
  encerrar.
- Arquivo inexistente ou ilegivel vira mensagem, nao traceback.
- `executar(linha, maquina)` separa o despacho de comandos do laço de leitura,
  o que deixa a CLI testavel sem subprocesso.

## Testes (`tests.py`)

1. Leitura: `derry.txt` (50 vertices, 108 arestas), 3 mapas validos em formatos
   equivalentes e 12 mapas invalidos, cada um rejeitado pelo motivo esperado.
2. Sessao de exemplo do enunciado, com as mensagens exatas, mais a CLI real via
   subprocesso (inclusive `comando desconhecido` e arquivo ausente).
3. Regra especial: origem removida ainda e ponto de partida; vertice removido
   bloqueia passagem (a distancia muda de 2 m para 101 m no mapa de teste);
   destino inalcancavel nao altera posicao nem visitas.
4. Conferencia cruzada: 300 grafos aleatorios com remocoes aleatorias,
   comparando `distancias` com uma implementacao de referencia independente
   (Bellman-Ford), que nao compartilha codigo com o Dijkstra.

Resultado atual: 58/58 verificacoes passaram.
