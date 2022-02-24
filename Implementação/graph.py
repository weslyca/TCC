from math import ceil, floor
from random import shuffle, randint

class Graph:

    def __init__(self, filename):
        self.v = 0.5
        self.chi = 0.1

        self.n, self.m = map(int, input().split())

        self.S = list(map(int, input().split()))
        self.I = list(map(int, input().split()))
        self.R = [0 for _ in range(self.n)]

        self.S_init = self.S.copy()
        self.I_init = self.I.copy()
        self.R_init = self.R.copy()

        self.neighbors = [set() for _ in range(self.n)]
        self.betas = {}
        self.x = {}

        self.prob = [0 for i in range(self.n)]
        self.parents = [0 for i in range(self.n)]
        self.unused_edges = []

        self.best_found_tree = []

        for i in range(self.m):
            i, j, beta = input().split()
            i, j = int(i), int(j)
            beta = float(beta)
            self.neighbors[i].add(j)
            self.betas[(i, j)] = beta
            self.x[(i, j)] = 1


    def restore_values(self):
        '''Restora os valores de suscetíveis, infectados e recuperados para \
os valores iniciais.'''
        self.S = self.S_init.copy()
        self.I = self.I_init.copy()
        self.R = self.R_init.copy()


    def restore_edges(self, edges=[]):
        '''Libera as estradas correspondentes a lista de arestas dada, ou a todas \
se nenhuma lista for dada, ou ela estiver vazia.'''
        if len(edges) == 0:
            edges = self.x
        for e in edges:
            self.x[e] = 1


    def clear_edges(self):
        '''Bloqueia todas as estradas.'''
        for e in self.x:
            self.x[e] = 0


    def refresh_unused_edges(self):
        '''Atualiza a lista de arestas não usadas (que não estão na árvore atual).'''
        # apenas arestas/arcos (i, j) com i < j
        self.unused_edges = []
        for e in self.x:
            (i, j) = e
            if self.x[e] == 0 and i < j:
                self.unused_edges.append(e)


    def refresh_parents(self):
        '''Atualiza os pais de cada vértice (o vértice no caminho para o vértice \
1). Usado para a troca de arestas na árvore.'''
        # o algoritmo é apenas uma bfs
        visited = [False for _ in range(self.n)]

        vertices = [0]
        visited[0] = True

        while len(vertices) > 0:
            u = vertices.pop(0)
            for v in self.neighbors[u]:
                if not visited[v] and self.x[(u, v)] == 1:
                    vertices.append(v)
                    visited[v] = True
                    self.parents[v] = u


    def find_cycle(self, u, v):
        '''Encontra o ciclo de qual u e v fariam parte se a aresta \
(u, v) fosse adicionada.'''

        # achar o caminho do vértice raiz até u e até v
        u_path = [u]
        i = u
        while i != 0:
            u_path.append(self.parents[i])
            i = self.parents[i]

        v_path = [v]
        i = v
        while i != 0:
            v_path.append(self.parents[i])
            i = self.parents[i]

        u_path.reverse()
        v_path.reverse()

        # achar qual o ancestral comum mais próximo
        i, j = 0, 0

        while u_path[i] == v_path[j]:
            i += 1
            j += 1

            if i == len(u_path) or j == len(v_path):
                break
        i-=1
        j-=1

        u_path = u_path[i:]
        v_path = v_path[j:]
        u_path.reverse()

        return u_path, v_path


    def try_edge(self, unused_edge, bound):
        '''Tenta achar a melhor árvore vizinha à atual (que dê um número de infectados \
menor). Ela adiciona a aresta especificada, criando um ciclo. Logo em seguida, é calculado \
o número de infectados do grafo sem cada uma das outras arestas do ciclo. A melhor é armazenada \
como best_found_tree. '''

        u, v = unused_edge
        if v < u:
            u, v = v, u

        u_path, v_path = self.find_cycle(u, v)
        root = u_path[-1]

        old_edge = (u, v)
        cur = 0

        # executa o "lado esquerdo" primeiro
        while u_path[cur] != root:
            new_edge = old_edge
            x, y = u_path[cur], u_path[cur+1]
            old_edge = (x, y)

            self.switch_edges(old_edge, new_edge)

            # calculando
            result = self.predict_single()
            if result < bound:
                bound = result
                # print("Better neighboring tree found: bound = " + str(bound))
                self.best_found_tree = [e for e in self.x if self.x[e] == 1]
            cur+=1

        # caso especial na subraiz
        # adicionando u ~> r, deletando r ~> v
        # todos os vértices no caminho no momento apontam para r pela direita
        # precisamos fazê-los apontar para r da esquerda

        u_path.insert(0, v)
        v_path.append(u)

        new_edge = (root, u_path[-2])
        old_edge = (root, v_path[1])

        self.switch_edges(old_edge, new_edge)

        # calculando
        result = self.predict_single()
        if result < bound:
            bound = result
            # print("Better neighboring tree found: bound = " + str(bound))
            self.best_found_tree = [e for e in self.x if self.x[e] == 1]

        # executa o lado "direito"
        cur = 1

        old_edge = (root, v_path[1])
        while v_path[cur] != u:
            new_edge = old_edge
            x, y = v_path[cur], v_path[cur+1]

            old_edge = (x, y)

            self.switch_edges(old_edge, new_edge)

            # calculando
            result = self.predict_single()
            if result < bound:
                bound = result
                # print("Better neighboring tree found: bound = " + str(bound))
                self.best_found_tree = [e for e in self.x if self.x[e] == 1]

            cur+=1

        return bound


    def switch_edges(self, old_edge, new_edge):
        '''Troca arestas.'''
        # estamos supondo i1 < j1 e i2 < j2

        i1, j1 = old_edge
        i2, j2 = new_edge

        if j1 < i1:
            i1, j1 = j1, i1
        old_edge = (i1, j1)

        if j2 < i2:
            i2, j2 = j2, i2
        new_edge = (i2, j2)

        self.x[(i1, j1)] = 0
        self.x[(j1, i1)] = 0
        self.x[(i2, j2)] = 1
        self.x[(j2, i2)] = 1

        # atualizar vértices não usados
        self.unused_edges.remove(new_edge)
        self.unused_edges.append(old_edge)

        # alguns vértices agora estão desatualizados

        # atualizar os pais
        # para o nosso método atual, é mais fácil fazer isso na função chamadora
        # para seus vizinhos, basta recalcular seus número de suscetíveis, infectados, etc

        self.recalculate_meetings()


    def print_graph(self):
        '''Imprime o número de suscetíveis, infectados e recuperados para cada vértice.'''
        for i in range(self.n):
            print(f'{i}: Suscetíveis = {self.S[i]}, Infectados = {self.I[i]}, Recuperados = {self.R[i]}')


    def generating_tree(self, minimal=False):
        '''Cria uma árvore geradora. É uma árvore geradora mínima se o gráfico é simétrico e é passada com minimal=True.'''

        edges = [e for e in self.x]
        if minimal:
            edges.sort(key=lambda x: self.betas[x])
        else:
            shuffle(edges)

        parent = [i for i in range(self.n)]
        rank = [1 for _ in range(self.n)]

        def find(x):
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]

        def union(x, y):
            xr, yr = find(x), find(y)

            if xr != yr:
                if rank[xr] > rank[yr]:
                    parent[yr] = xr
                elif rank[xr] < rank[yr]:
                    parent[xr] = yr
                else:
                    parent[yr] = xr
                    rank[xr] += 1

        selected = []

        for (i, j) in edges:
            if find(i) != find(j):
                union(i, j)
                selected.append((i, j))

        for e in self.x:
            self.x[e] = 0

        for (i, j) in selected:
            self.x[(i, j)] = 1
            self.x[(j, i)] = 1

        self.refresh_parents()
        self.refresh_unused_edges()


    def recalculate_meetings(self):
        '''Recalcula os encontros.'''
        prob = self.prob

        for i in range(self.n):
            # quantos moram e ficam aqui?
            S_ii = self.S[i]
            I_ii = self.I[i]
            R_ii = self.R[i]

            for j in self.neighbors[i]:
                S_ii -= (self.betas[(i, j)]*self.x[(i, j)]*self.S[i])
                I_ii -= (self.betas[(i, j)]*self.x[(i, j)]*self.I[i])
                R_ii -= (self.betas[(i, j)]*self.x[(i, j)]*self.R[i])

            S_circ = S_ii
            I_circ = I_ii
            R_circ = R_ii

            #quantos vêm de outros vértices?
            for j in self.neighbors[i]:
                S_circ += (self.betas[(j, i)]*self.x[(j, i)]*self.S[j])
                I_circ += (self.betas[(j, i)]*self.x[(j, i)]*self.I[j])
                R_circ += (self.betas[(j, i)]*self.x[(j, i)]*self.R[j])

            prob[i] = (I_circ/(S_circ + I_circ + R_circ))
        self.prob = prob


    def predict_single(self, report=False):
        '''Faz uma previsão do comportamento de transmissão, retornando o número \
de infectados caso no próximo tempo de acordo com o grafo atual.'''
        next_S = self.S.copy()
        next_I = self.I.copy()
        next_R = self.R.copy()

        self.recalculate_meetings()
        prob = self.prob

        for i in range(self.n):

            S_ii = self.S[i]
            I_ii = self.I[i]
            R_ii = self.R[i]

            for j in self.neighbors[i]:
                S_ii -= (self.betas[(i, j)]*self.x[(i, j)]*self.S[i])
                I_ii -= (self.betas[(i, j)]*self.x[(i, j)]*self.I[i])
                R_ii -= (self.betas[(i, j)]*self.x[(i, j)]*self.R[i])

            esperado = S_ii*prob[i]

            for j in self.neighbors[i]:
                S_ij = (self.betas[(i, j)]*self.x[(i, j)]*self.S[i])

                esperado += S_ij * prob[j]

            next_S[i] = self.S[i] - (self.v*esperado)
            next_I[i] = self.I[i] + (self.v*esperado) - (self.chi*self.I[i])
            next_R[i] = self.R[i] + (self.chi*self.I[i])

        return (sum(next_I) + sum(next_R))


    def print_edges(self):
        for e in self.x:
            if self.x[e] == 1:
                print(e)

    def format_curr_graph(self):
        '''Formata o grafo atual para ser usado nos outros programas.'''
        m = 0
        for (i, j) in self.x:
            if self.x[(i, j)] == 1:
                m+=1
        print(f"{self.n} {m}")
        r = ""
        for i in self.S_init:
            r += str(i) + " "
        print(r[:-1])
        r = ""
        for i in self.I_init:
            r += str(i) + " "
        print(r[:-1])
        for (i, j) in self.x:
            if self.x[(i, j)] == 1:
                print(f"{i+1} {j+1} {self.betas[(i, j)]}")


    def format_curr_tree(self, bound):
        '''Formata a árvore atual para ser usado como entrada no solver.'''
        # n, m
        # arestas
        # limite
        m = 0
        for (i, j) in self.x:
            if j > i and self.x[(i, j)] == 1:
                m+=1
        print(f"{self.n} {m}")
        for (i, j) in self.x:
            if j > i and self.x[(i, j)] == 1:
                print(f"{i+1} {j+1}")

        print(bound)


    def search_neighboring_trees(self, init_bound):
        '''Procura a melhor árvore dentre as árvores vizinhas da atual.'''
        bound = init_bound

        for edge in self.unused_edges:
            x, y = edge
            bound = self.try_edge(edge, bound)

        return bound, self.best_found_tree


    def hill_climb(self, bound):
        '''Executa o algoritmo de hill climb, procurando árvores vizinhas até que \
todas as árvores vizinhas atuais sejam piores (com um número de infectados maior).'''
        self.best_found_tree = [e for e in self.x if self.x[e] == 1]

        while True:
            new_bound, tree_config = self.search_neighboring_trees(bound)

            if new_bound == bound:
                break

            self.clear_edges()
            self.restore_edges(tree_config)
            self.refresh_parents()
            bound = new_bound
        return bound, tree_config


    def random_search_best(self, n_trees):
        '''Executa uma busca iterada, usando o algoritmo de hill climb com várias \
árvores geradoras aleatórias.'''

        self.generating_tree(minimal=True)
        bound = self.predict_single()
        best_found = [e for e in self.x if self.x[e] == 1]

        for i in range(n_trees):
            new_bound, tree_config = self.hill_climb(bound)

            if new_bound == bound:
                continue

            bound = new_bound
            best_found = tree_config

            self.generating_tree(minimal=False)

        self.clear_edges()
        self.restore_edges(best_found)
        self.format_curr_tree(bound)

if __name__ == '__main__':
    g = Graph('qualquer')
    g.format_curr_graph()
    g.random_search_best(2000)
