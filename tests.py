#!/usr/bin/env python3
"""Testes da resolucao 3 (res03_dijkstra_matriz).

Cobre tres frentes:
  1. leitura de mapa: arquivo valido e uma bateria de arquivos invalidos;
  2. sessao de exemplo do enunciado, comparando as mensagens exatas;
  3. conferencia do Dijkstra contra uma implementacao de referencia
     independente (Bellman-Ford) em grafos aleatorios, com remocoes
     aleatorias de vertices.

Uso: python3 tests.py
"""

import random
import subprocess
import sys
from pathlib import Path

import main as m

AQUI = Path(__file__).resolve().parent
DERRY = AQUI / "derry.txt"

SEM_CAMINHO = float("inf")
falhas = []
total = 0


def checar(condicao, descricao, extra=""):
    global total
    total += 1
    if not condicao:
        falhas.append(f"{descricao} {extra}".strip())
        print(f"FALHOU: {descricao} {extra}".strip())
    return condicao


def igual(obtido, esperado, descricao):
    return checar(obtido == esperado, descricao, f"| obtido={obtido!r} esperado={esperado!r}")


# --------------------------------------------------------------------------
# 1. Leitura de mapa
# --------------------------------------------------------------------------

def testes_de_leitura():
    mapa = m.Mapa.de_arquivo(str(DERRY))
    igual(len(mapa.nomes), 50, "derry.txt tem 50 vertices")
    igual(mapa.n_arestas, 108, "derry.txt tem 108 arestas")
    igual(mapa.matriz[mapa.indice["Oscar_Wilson"]][mapa.indice["Stephanie_Price"]],
          400, "peso Oscar_Wilson-Stephanie_Price")
    igual(mapa.matriz[mapa.indice["Stephanie_Price"]][mapa.indice["Oscar_Wilson"]],
          400, "grafo tratado como nao direcionado")

    validos = {
        "minimo": "2 1 a b\na b 7\n",
        "com quebras de linha irrelevantes": "2   1\n a\n b\n a  b  7\n",
        "com espacos sobrando": "  2 1  a b \n\n a b 7 \n\n",
    }
    for caso, texto in validos.items():
        try:
            mapa = m.Mapa.de_texto(texto)
            checar(mapa.matriz[0][1] == 7, f"mapa valido aceito: {caso}")
        except m.ErroMapa as erro:
            checar(False, f"mapa valido recusado: {caso}", f"| {erro}")

    invalidos = {
        "vazio": "",
        "so cabecalho": "3",
        "cabecalho nao inteiro": "N M\na\nb\nc\na b 1\n",
        "contagem de campos errada": "3 2 a b c\na b 1\n",
        "vertice desconhecido": "3 1 a b c\na z 1\n",
        "laco": "3 1 a b c\na a 1\n",
        "peso zero": "3 1 a b c\na b 0\n",
        "peso negativo": "3 1 a b c\na b -5\n",
        "peso nao inteiro": "3 1 a b c\na b sete\n",
        "aresta repetida": "3 2 a b c\na b 1\nb a 2\n",
        "nome repetido": "3 1 a a c\na c 1\n",
        "N zero": "0 0\n",
    }
    for caso, texto in invalidos.items():
        try:
            m.Mapa.de_texto(texto)
            checar(False, f"mapa invalido aceito: {caso}")
        except m.ErroMapa:
            checar(True, f"mapa invalido recusado: {caso}")

    try:
        m.Mapa.de_arquivo(str(AQUI / "nao_existe.txt"))
        checar(False, "arquivo inexistente gera erro tratado")
    except m.ErroMapa:
        checar(True, "arquivo inexistente gera erro tratado")


# --------------------------------------------------------------------------
# 2. Sessao de exemplo do enunciado
# --------------------------------------------------------------------------

def testes_da_sessao():
    comandos = [
        ("carregar derry.txt", ["Mapa carregado: 50 locais e 108 tuneis."]),
        ("iniciar Oscar_Wilson", ["Posicao atual: Oscar_Wilson."]),
        ("onde", ["Oscar_Wilson"]),
        ("rota Betty_Ripsom",
         ["Rota: Oscar_Wilson -> Stephanie_Price -> Betty_Ripsom", "Distancia: 690 m"]),
        ("ir Betty_Ripsom",
         ["Rota: Oscar_Wilson -> Stephanie_Price -> Betty_Ripsom",
          "Distancia: 690 m", "Betty_Ripsom visitada."]),
        ("onde", ["Betty_Ripsom"]),
        ("rota Betty_Ripsom", ["Crianca ja visitada."]),
        ("rota Jessica_Hanlon",
         ["Rota: Betty_Ripsom -> Sally_Mueller -> Lucas_Bennett -> Oscar_Bowers -> Jessica_Hanlon",
          "Distancia: 810 m"]),
    ]

    maquina = m.Pennywise()
    for comando, esperados in comandos:
        saida, _ = m.executar(comando, maquina)
        linhas = saida.split("\n")
        for esperado in esperados:
            checar(esperado in linhas, f"comando '{comando}' produz '{esperado}'")

    # a crianca visitada sai da lista de distancias
    saida, _ = m.executar("distancias", maquina)
    nomes_listados = [linha.split(":")[0] for linha in saida.split("\n")]
    checar("Betty_Ripsom" not in nomes_listados, "crianca visitada sai de distancias")
    checar("Oscar_Wilson" in nomes_listados, "crianca nao visitada continua em distancias")
    checar(nomes_listados == sorted(nomes_listados), "distancias em ordem lexicografica")

    # o destino inalcancavel nao muda o estado
    antes = (maquina.posicao, set(maquina.removidos), maquina.viagens)
    saida, _ = m.executar("ir Ninguem_Assim", maquina)
    checar("inexistente" in saida, "comando com crianca inexistente avisa")
    igual((maquina.posicao, set(maquina.removidos), maquina.viagens), antes,
          "estado intacto apos comando invalido")

    # a posicao inicial nao muda depois da primeira viagem
    saida, _ = m.executar("iniciar Oscar_Wilson", maquina)
    checar("nao pode mais ser alterada" in saida, "iniciar bloqueado apos viagem")

    # a CLI inteira, via subprocesso, com a entrada da sessao de exemplo
    entrada = "\n".join(c for c, _ in comandos) + "\nrota Betty_Ripsom\nsair\n"
    resultado = subprocess.run(
        [sys.executable, str(AQUI / "main.py")],
        input=entrada, capture_output=True, text=True, cwd=AQUI,
    )
    igual(resultado.returncode, 0, "CLI encerra com codigo 0")
    for trecho in ("Mapa carregado: 50 locais e 108 tuneis.",
                   "Rota: Oscar_Wilson -> Stephanie_Price -> Betty_Ripsom",
                   "Distancia: 690 m",
                   "Distancia: 810 m",
                   "Betty_Ripsom visitada.",
                   "Crianca ja visitada."):
        checar(trecho in resultado.stdout, f"CLI imprime '{trecho}'")

    # comando desconhecido e carregamento de arquivo ausente nao derrubam a CLI
    resultado = subprocess.run(
        [sys.executable, str(AQUI / "main.py")],
        input="xpto\ncarregar nada.txt\nsair\n", capture_output=True, text=True, cwd=AQUI,
    )
    igual(resultado.returncode, 0, "CLI sobrevive a comandos invalidos")
    checar("comando desconhecido" in resultado.stdout, "CLI avisa comando desconhecido")
    checar("erro no mapa" in resultado.stdout, "CLI avisa arquivo inexistente")


# --------------------------------------------------------------------------
# 3. Conferencia contra a referencia independente
# --------------------------------------------------------------------------

def referencia_bellman_ford(nomes, matriz, inicio, removidos):
    """Menores distancias por Bellman-Ford. Nao compartilha codigo com o Dijkstra."""
    n = len(nomes)
    permitidos = [i for i in range(n) if nomes[i] not in removidos or i == inicio]
    dist = {i: SEM_CAMINHO for i in permitidos}
    dist[inicio] = 0
    for _ in range(len(permitidos)):
        mudou = False
        for a in permitidos:
            if dist[a] == SEM_CAMINHO:
                continue
            for b in permitidos:
                peso = matriz[a][b]
                if peso is None:
                    continue
                if dist[a] + peso < dist[b]:
                    dist[b] = dist[a] + peso
                    mudou = True
        if not mudou:
            break
    return dist


def grafo_aleatorio(sorteio, n_vertices, densidade):
    nomes = [f"v{i:02d}" for i in range(n_vertices)]
    n = len(nomes)
    matriz = [[None] * n for _ in range(n)]
    linhas = [f"{n} 0"]
    for i in range(n):
        linhas.append(nomes[i])
    arestas = []
    for i in range(n):
        for j in range(i + 1, n):
            if sorteio.random() < densidade:
                peso = sorteio.randint(1, 60)
                matriz[i][j] = matriz[j][i] = peso
                arestas.append(f"{nomes[i]} {nomes[j]} {peso}")
    linhas[0] = f"{n} {len(arestas)}"
    return "\n".join(linhas + arestas) + "\n", nomes, matriz


def testes_contra_referencia(rodadas=300):
    sorteio = random.Random(20261123)
    caminho = AQUI / "_mapa_temporario.txt"
    diferentes = 0
    try:
        for _ in range(rodadas):
            n_vertices = sorteio.randint(2, 12)
            texto, nomes, matriz = grafo_aleatorio(sorteio, n_vertices, sorteio.uniform(0.2, 0.6))
            caminho.write_text(texto, encoding="utf-8")

            removidos = {nome for nome in nomes if sorteio.random() < 0.3}
            inicio_nome = sorteio.choice(nomes)
            inicio = nomes.index(inicio_nome)

            maquina = m.Pennywise()
            maquina.carregar([str(caminho)])
            maquina.posicao = inicio_nome
            maquina.removidos = set(removidos)

            obtido = {}
            for linha in maquina.distancias([]).split("\n"):
                if ": " not in linha:
                    continue
                nome, valor = linha.rsplit(": ", 1)
                obtido[nome] = SEM_CAMINHO if valor == "inalcancavel" else int(valor.split()[0])

            esperado = referencia_bellman_ford(nomes, matriz, inicio, removidos)
            for i, nome in enumerate(nomes):
                if nome in removidos:
                    continue
                if obtido.get(nome) != esperado[i]:
                    diferentes += 1
                    print(f"DIVERGENCIA: {nome} em {texto!r} removidos={sorted(removidos)} "
                          f"obtido={obtido.get(nome)} esperado={esperado[i]}")
                    break
    finally:
        caminho.unlink(missing_ok=True)

    checar(diferentes == 0, f"{rodadas} grafos aleatorios sem divergencia do Bellman-Ford",
           f"| divergencias={diferentes}")


def testes_da_regra_especial():
    # cadeia a-b-c-d de peso 1, mais um atalho direto a-d de peso 100
    texto = "4 4\na b c d\na b 1\nb c 1\nc d 1\na d 100\n"

    # 1) origem removida continua valendo como ponto de partida
    maquina = m.Pennywise()
    maquina.mapa = m.Mapa.de_texto(texto)
    maquina.posicao = "b"
    maquina.removidos = {"b"}

    distancias = dict(l.rsplit(": ", 1) for l in maquina.distancias([]).split("\n"))
    checar("b" not in distancias, "origem removida nao aparece em distancias")
    igual(distancias.get("a"), "1 m", "origem removida alcanca vizinho livre")
    igual(distancias.get("d"), "2 m", "rota curta usa o caminho ainda livre")

    saida = maquina.rota(["c"])
    checar("Rota: b -> c" in saida, "rota a partir da origem removida")

    # 2) vertice removido bloqueia a passagem, mas o desvio continua valendo
    maquina.removidos = {"b", "c"}
    distancias = dict(l.rsplit(": ", 1) for l in maquina.distancias([]).split("\n"))
    checar("c" not in distancias, "vertice removido fora de distancias")
    igual(distancias.get("d"), "101 m", "com c removido sobra o desvio por a")

    # 3) destino inalcancavel: posicao e visitas intactas
    maquina3 = m.Pennywise()
    maquina3.mapa = m.Mapa.de_texto("3 1\na b c\na b 1\n")
    maquina3.posicao = "c"
    maquina3.removidos = {"c"}
    saida = maquina3.ir(["a"])
    checar("inalcancavel" in saida, "destino inalcancavel avisa")
    igual(maquina3.posicao, "c", "posicao mantida apos viagem inexistente")
    igual(len(maquina3.removidos), 1, "visitas mantidas apos viagem inexistente")


if __name__ == "__main__":
    testes_de_leitura()
    testes_da_sessao()
    testes_da_regra_especial()
    testes_contra_referencia()

    print(f"\n{total - len(falhas)}/{total} verificacoes passaram")
    if falhas:
        print("falhas:")
        for f in falhas:
            print(f"  - {f}")
        sys.exit(1)
    print("tudo certo")
