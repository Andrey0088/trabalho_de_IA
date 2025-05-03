# zodiaco_solver_a_star.py
import sys
from queue import PriorityQueue
from PIL import Image, ImageDraw

class Cavaleiro:
    def __init__(self, nome, poder):
        self.nome = nome
        self.poder = poder
        self.energia = 5

    def pode_lutar(self):
        return self.energia > 0

    def lutar(self):
        self.energia -= 1

class Node():
    def __init__(self, state, parent, action, cost, heuristic):
        self.state = state
        self.parent = parent
        self.action = action
        self.cost = cost
        self.heuristic = heuristic

    def __lt__(self, other):
        return (self.cost + self.heuristic) < (other.cost + other.heuristic)

class ZodiacoMap:
    def __init__(self, filename):
        self.walls = []
        self.casas = {}
        self.start = None
        self.goal = None
        self.solucoes = []
        self.tempo_total = 0
        self.casas_visitadas = set()
        self.vez_do_cavaleiro = 0

        with open(filename) as f:
            contents = f.read().splitlines()

        self.height = len(contents)
        self.width = max(len(line) for line in contents)
        contents = [line.ljust(self.width) for line in contents]

        casa_count = 1
        for i in range(self.height):
            row = []
            for j in range(self.width):
                c = contents[i][j]
                if c == "R":
                    self.start = (i, j)
                    row.append("plano")
                elif c == "G":
                    self.goal = (i, j)
                    row.append("plano")
                elif c == "#":
                    row.append("montanha")
                elif c == ".":
                    row.append("rochoso")
                elif c == "C":
                    self.casas[(i, j)] = casa_count
                    casa_count += 1
                    row.append("plano")
                else:
                    row.append("plano")
            self.walls.append(row)

        if not self.start or not self.goal:
            raise Exception("Mapa precisa ter R e G")

        self.dificuldades = {
            1: 50, 2: 55, 3: 60, 4: 70, 5: 75, 6: 80,
            7: 85, 8: 90, 9: 95, 10: 100, 11: 110, 12: 120
        }

        self.cavaleiros = [
            Cavaleiro("Seiya", 1.5),
            Cavaleiro("Shiryu", 1.4),
            Cavaleiro("Hyoga", 1.3),
            Cavaleiro("Shun", 1.2),
            Cavaleiro("Ikki", 1.1)
        ]

    def custo_terreno(self, state):
        tipo = self.walls[state[0]][state[1]]
        return {"plano": 1, "rochoso": 5, "montanha": 200}.get(tipo, 1)

    def neighbors(self, state):
        row, col = state
        dirs = [("up", (row-1, col)), ("down", (row+1, col)), ("left", (row, col-1)), ("right", (row, col+1))]
        return [(a, s) for a, s in dirs if 0 <= s[0] < self.height and 0 <= s[1] < self.width and self.walls[s[0]][s[1]] != "montanha"]

    def selecionar_time(self):
        vivos = [c for c in self.cavaleiros if c.pode_lutar()]
        if not vivos:
            raise Exception("Todos os cavaleiros estao mortos!")

        # Rotaciona entre os cavaleiros vivos, 2 por luta
        time = []
        for _ in range(2):
            if not vivos:
                break
            c = vivos[self.vez_do_cavaleiro % len(vivos)]
            time.append(c)
            self.vez_do_cavaleiro += 1

        return time

    def lutar_em_casa(self, casa_id, state):
        if state in self.casas_visitadas:
            return
        dificuldade = self.dificuldades.get(casa_id, 100)
        time = self.selecionar_time()
        poder_total = sum(c.poder for c in time)
        tempo = round(dificuldade / poder_total, 2)
        for c in time:
            c.lutar()
        nomes = ", ".join(c.nome for c in time)
        self.solucoes.append(f"Casa {casa_id}: {nomes} lutaram. Tempo: {tempo} min")
        self.tempo_total += tempo
        self.casas_visitadas.add(state)

    def resumo(self):
        print("CAMINHO:")
        for s in self.solucoes:
            print(s)
        print(f"\nTempo total: {round(self.tempo_total, 2)} minutos")
        print(f"Nós explorados: {len(self.explored)}")

    def visualizar(self, nome_arquivo):
        cell = 15
        borda = 1
        img = Image.new("RGB", (self.width * cell, self.height * cell), "black")
        draw = ImageDraw.Draw(img)
 
        # Garante que a solução seja um conjunto de células
        solucao = set(self.solution[1]) if hasattr(self, 'solution') and self.solution else set()

        for i in range(self.height):
            for j in range(self.width):
                x0, y0 = j * cell + borda, i * cell + borda
                x1, y1 = (j + 1) * cell - borda, (i + 1) * cell - borda
                fill = (40, 40, 40) if self.walls[i][j] == "montanha" else (237, 240, 252)
                if (i, j) == self.start:
                    fill = (255, 0, 0)  # Início em vermelho
                elif (i, j) == self.goal:
                    fill = (0, 255, 0)  # Objetivo em verde
                elif (i, j) in solucao:
                    fill = (255, 255, 0)  # Caminho da solução em amarelo
                elif (i, j) in self.casas:
                    fill = (0, 0, 255)  # Casas em azul

                draw.rectangle([x0, y0, x1, y1], fill=fill)

        img.save(nome_arquivo)
        print(f"Imagem salva como {nome_arquivo}")

class ZodiacoMapAStar(ZodiacoMap):
    def heuristic(self, state):
        row1, col1 = state
        row2, col2 = self.goal
        return abs(row1 - row2) + abs(col1 - col2)

    def solve(self):
        start = Node(state=self.start, parent=None, action=None, cost=0, heuristic=self.heuristic(self.start))
        frontier = PriorityQueue()
        frontier.put((start.cost + start.heuristic, start))
        self.explored = set()

        while not frontier.empty():
            _, node = frontier.get()

            # Verifica se o objetivo foi alcançado e todas as casas foram visitadas
            if node.state == self.goal and len(self.casas_visitadas) == 12:
                actions = []
                cells = []
                while node.parent:
                    actions.append(node.action)
                    cells.append(node.state)
                    node = node.parent
                actions.reverse()
                cells.reverse()
                self.solution = (actions, cells)  # Armazena a solução corretamente
                print(f"Nós explorados: {len(self.explored)}")
                print(f"Caminho encontrado: {len(cells)} passos")
                return

            self.explored.add(node.state)

            for action, state in self.neighbors(node.state):
                if state not in self.explored:
                    custo = node.cost + self.custo_terreno(state)
                    if state in self.casas:
                        self.lutar_em_casa(self.casas[state], state)
                    h = self.heuristic(state)
                    child = Node(state=state, parent=node, action=action, cost=custo, heuristic=h)
                    frontier.put((child.cost + child.heuristic, child))

if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit("Uso: python zodiaco_solver_a_star.py mapa.txt")

    z = ZodiacoMapAStar(sys.argv[1])
    print("Resolvendo com A*...")
    z.solve()
    z.resumo()
    z.visualizar("saida_zodiaco_astar.png")