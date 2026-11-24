#!/usr/bin/env python3
"""ALEST II - T2: Pennywise e os caminhos mais curtos pelos esgotos de Derry.

Resolucao 3 de 3 - criterio: robustez e facilidade de teste.

  * representacao: matriz de adjacencia N x N (lista de listas de inteiros).
    Sem heap e sem dicionario de predecessores: so vetores indexados.
  * busca: Dijkstra na versao classica O(V^2), com escolha do vertice de
    menor distancia por varredura linear. Nao depende de heapq.
  * reconstrucao do caminho: vetor `anterior` indexado por vertice.
  * entrada: o mapa passa por validacao completa antes de ser aceito; a CLI
    nunca encerra por erro de digitacao.
  * acompanha tests.py, que roda a sessao de exemplo do enunciado e compara
    o resultado com uma implementacao de referencia independente
    (Bellman-Ford) em grafos aleatorios.

Justificativa do O(V^2): com heap o custo e O((V + E) log V), mas em grafos
densos a varredura linear costuma sair mais rapida e nao exige tratamento de
decrease-key. Para V da ordem de milhares, as duas versoes sao instantaneas.
"""

import sys

INF = None  # ausencia de aresta na matriz
SEM_CAMINHO = float("inf")

AJUDA = """comandos disponiveis:
  carregar <arquivo>  le o mapa do arquivo indicado (uma vez por execucao)
  iniciar <crianca>   define a posicao inicial de Pennywise
  onde                mostra o nome do local onde Pennywise esta
  distancias          menor distancia da posicao atual ate cada crianca disponivel
  rota <crianca>      mostra a rota minima, sem deslocar Pennywise
  ir <crianca>        mostra a rota minima, vai ate a crianca e a marca como visitada
  ajuda               lista os comandos disponiveis
  sair                encerra o programa"""


class ErroMapa(Exception):
    """Arquivo de mapa ilegivel ou fora do formato."""


class Mapa:
    """Grafo ponderado nao direcionado guardado em matriz de adjacencia."""

    def __init__(self, nomes, matriz, n_arestas):
        self.nomes = nomes
        self.matriz = matriz            # matriz[i][j] = peso ou None
        self.n_arestas = n_arestas
        self.indice = {nome: i for i, nome in enumerate(nomes)}

    @classmethod
    def de_arquivo(cls, caminho):
        try:
            with open(caminho, "r", encoding="utf-8-sig") as arq:
                texto = arq.read()
        except OSError as erro:
            raise ErroMapa(f"nao foi possivel ler '{caminho}': {erro.strerror or erro}")
        except UnicodeDecodeError:
            raise ErroMapa(f"'{caminho}' nao parece um arquivo de texto UTF-8")

        return cls.de_texto(texto, origem_do_erro=caminho)

    @classmethod
    def de_texto(cls, texto, origem_do_erro="<memoria>"):
        """Monta o mapa a partir do conteudo. Levanta ErroMapa se algo falhar."""
        tokens = texto.split()
        if len(tokens) < 2:
            raise ErroMapa("arquivo vazio ou sem o cabecalho N M")

        if not tokens[0].lstrip("+-").isdigit() or not tokens[1].lstrip("+-").isdigit():
            raise ErroMapa("o cabecalho deve conter dois inteiros: N M")

        n, m = int(tokens[0]), int(tokens[1])
        if n <= 0:
            raise ErroMapa(f"N invalido no cabecalho: {n}")
        if m < 0:
            raise ErroMapa(f"M invalido no cabecalho: {m}")

        esperado = 2 + n + 3 * m
        if len(tokens) != esperado:
            raise ErroMapa(
                f"o arquivo tem {len(tokens)} campos; para N={n} e M={m} esperava {esperado}"
            )

        nomes = tokens[2:2 + n]
        if len(set(nomes)) != n:
            raise ErroMapa("ha nomes de vertices repetidos na lista")

        indice = {nome: i for i, nome in enumerate(nomes)}
        matriz = [[None] * n for _ in range(n)]
        pares_vistos = set()
        cursor = 2 + n
        for numero in range(1, m + 1):
            origem, destino, peso_txt = tokens[cursor:cursor + 3]
            cursor += 3
            if origem not in indice:
                raise ErroMapa(f"aresta {numero} usa vertice desconhecido: {origem}")
            if destino not in indice:
                raise ErroMapa(f"aresta {numero} usa vertice desconhecido: {destino}")
            if origem == destino:
                raise ErroMapa(f"aresta {numero} e um laco: {origem}")
            if not peso_txt.lstrip("+-").isdigit():
                raise ErroMapa(f"aresta {numero} tem peso nao inteiro: {peso_txt}")
            peso = int(peso_txt)
            if peso <= 0:
                raise ErroMapa(f"aresta {numero} tem peso nao positivo: {peso}")
            chave = (min(origem, destino), max(origem, destino))
            if chave in pares_vistos:
                raise ErroMapa(f"aresta repetida: {origem} {destino}")
            pares_vistos.add(chave)
            a, b = indice[origem], indice[destino]
            matriz[a][b] = peso
            matriz[b][a] = peso

        return cls(nomes, matriz, m)


def dijkstra(nomes, matriz, origem, removidos):
    """Dijkstra O(V^2) a partir de `origem`, sem atravessar `removidos`.

    `origem` vale mesmo se estiver em `removidos`: Pennywise continua no
    local e pode comecar dali. Nenhum outro removido entra no caminho.
    """
    n = len(nomes)
    dist = [SEM_CAMINHO] * n
    anterior = [-1] * n
    fechado = [False] * n

    inicio = origem
    dist[inicio] = 0

    for _ in range(n):
        atual, melhor = -1, SEM_CAMINHO
        for i in range(n):
            if not fechado[i] and dist[i] < melhor:
                atual, melhor = i, dist[i]
        if atual == -1:
            break
        fechado[atual] = True
        linha = matriz[atual]
        for j in range(n):
            peso = linha[j]
            if peso is None or fechado[j]:
                continue
            if j != inicio and nomes[j] in removidos:
                continue
            candidato = dist[atual] + peso
            if candidato < dist[j]:
                dist[j] = candidato
                anterior[j] = atual

    return dist, anterior


def reconstruir(nomes, anterior, inicio, destino):
    caminho = [destino]
    passo = destino
    while passo != inicio:
        passo = anterior[passo]
        if passo == -1:
            return None
        caminho.append(passo)
    caminho.reverse()
    return [nomes[i] for i in caminho]


class Pennywise:
    """Estado da sessao: mapa, posicao e criancas visitadas."""

    def __init__(self):
        self.mapa = None
        self.removidos = set()
        self.posicao = None
        self.viagens = 0

    # -- utilidades ------------------------------------------------------

    def _pronto(self):
        """Devolve uma mensagem de erro se a navegacao ainda nao pode comecar."""
        if self.mapa is None:
            return "carregue um mapa antes: carregar <arquivo>"
        if self.posicao is None:
            return "posicao indefinida: use iniciar <crianca>"
        return None

    def _planejar(self, destino):
        """(caminho, custo) ate `destino` no estado atual, ou (None, None)."""
        inicio = self.mapa.indice[self.posicao]
        dist, anterior = dijkstra(self.mapa.nomes, self.mapa.matriz, inicio, self.removidos)
        alvo = self.mapa.indice[destino]
        if dist[alvo] == SEM_CAMINHO:
            return None, None
        return reconstruir(self.mapa.nomes, anterior, inicio, alvo), dist[alvo]

    @staticmethod
    def _resumo(caminho, custo):
        return [f"Rota: {' -> '.join(caminho)}", f"Distancia: {custo} m"]

    # -- comandos --------------------------------------------------------

    def carregar(self, args):
        if len(args) != 1:
            return "uso: carregar <arquivo>"
        if self.mapa is not None:
            return "mapa ja carregado: so um carregamento por execucao"
        try:
            mapa = Mapa.de_arquivo(args[0])
        except ErroMapa as erro:
            return f"erro no mapa: {erro}"
        self.mapa = mapa
        return f"Mapa carregado: {len(mapa.nomes)} locais e {mapa.n_arestas} tuneis."

    def iniciar(self, args):
        if len(args) != 1:
            return "uso: iniciar <crianca>"
        if self.mapa is None:
            return "carregue um mapa antes: carregar <arquivo>"
        if self.viagens > 0:
            return "a posicao nao pode mais ser alterada depois da primeira viagem"
        if args[0] not in self.mapa.indice:
            return f"crianca inexistente: {args[0]}"
        self.posicao = args[0]
        return f"Posicao atual: {self.posicao}."

    def onde(self, args):
        if len(args) != 0:
            return "uso: onde"
        erro = self._pronto()
        if erro:
            return erro
        return self.posicao

    def distancias(self, args):
        if len(args) != 0:
            return "uso: distancias"
        erro = self._pronto()
        if erro:
            return erro
        inicio = self.mapa.indice[self.posicao]
        dist, _ = dijkstra(self.mapa.nomes, self.mapa.matriz, inicio, self.removidos)
        saida = []
        for nome in sorted(self.mapa.nomes):
            if nome in self.removidos:
                continue
            d = dist[self.mapa.indice[nome]]
            saida.append(f"{nome}: inalcancavel" if d == SEM_CAMINHO else f"{nome}: {d} m")
        return "\n".join(saida)

    def _validar_destino(self, args, uso):
        if len(args) != 1:
            return uso, None
        erro = self._pronto()
        if erro:
            return erro, None
        destino = args[0]
        if destino not in self.mapa.indice:
            return f"crianca inexistente: {destino}", None
        if destino in self.removidos:
            return "Crianca ja visitada.", None
        return None, destino

    def rota(self, args):
        erro, destino = self._validar_destino(args, "uso: rota <crianca>")
        if erro:
            return erro
        caminho, custo = self._planejar(destino)
        if caminho is None:
            return f"inalcancavel: nao ha caminho de {self.posicao} ate {destino}"
        return "\n".join(self._resumo(caminho, custo))

    def ir(self, args):
        erro, destino = self._validar_destino(args, "uso: ir <crianca>")
        if erro:
            return erro
        caminho, custo = self._planejar(destino)
        if caminho is None:
            return (f"inalcancavel: nao ha caminho de {self.posicao} ate {destino}; "
                    "posicao e visitas inalteradas")
        linhas = self._resumo(caminho, custo)
        self.removidos.add(destino)
        self.posicao = destino
        self.viagens += 1
        linhas.append(f"{destino} visitada.")
        return "\n".join(linhas)


COMANDOS = {"carregar", "iniciar", "onde", "distancias", "rota", "ir"}


def executar(linha, maquina):
    """Executa um comando e devolve (texto_de_saida, deve_encerrar)."""
    partes = linha.split()
    if not partes:
        return "", False

    nome, args = partes[0], partes[1:]
    if nome == "sair":
        if args:
            return "uso: sair", False
        return "Ate a proxima cacada.", True
    if nome == "ajuda":
        return (AJUDA, False) if not args else ("uso: ajuda", False)
    if nome in COMANDOS:
        return getattr(maquina, nome)(args), False
    return f"comando desconhecido: {nome}. Use ajuda.", False


def principal():
    maquina = Pennywise()
    print("Navegador dos esgotos de Derry. Digite ajuda para ver os comandos.")
    while True:
        try:
            linha = input("Pennywise> ")
        except EOFError:
            print()
            break
        except KeyboardInterrupt:
            print()
            continue
        saida, encerrar = executar(linha, maquina)
        if saida:
            print(saida)
        if encerrar:
            break


if __name__ == "__main__":
    principal()
