# Resolucao: Dijkstra O(V^2) em matriz,
    python3 main.py
    python3 tests.py

## Como funciona

- Grafo em matriz de adjacencia, como a resolucao 2, mas a busca e Dijkstra na
  versao classica O(V^2): a cada iteracao escolhe por varredura linear o vertice
  nao fechado de menor distancia.
- Justificativa: em grafos densos a varredura linear empata ou ganha do heap, e
  nao precisa de tratamento de decrease-key. Para V na ordem de milhares, as
  duas versoes sao instantaneas.
- Caminho reconstruido andando para tras no vetor `anterior`.




