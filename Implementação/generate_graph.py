from random import shuffle, randint

n = 5

# começamos com um grafo completo
edges = []

for i in range(n):
    for j in range(i+1, n):
        edges.append((i, j))

# escolhemos uma árvore geradora qualquer

shuffle(edges)

parent = [i for i in range(n)]
rank = [1 for _ in range(n)]

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

selected = {}

m = 0

neighbors = [0 for _ in range(n)]

for (i, j) in edges:
    # print(f'{i}, {j} => {parent}')
    if find(i) != find(j):
        union(i, j)
        selected[(i, j)] = 1
        neighbors[i]+=1
        neighbors[j]+=1
        m+=1
    else:
        selected[(i, j)] = 0

extra_percent = 60

for (i, j) in edges:
    if selected[(i, j)] == 0:
        if randint(1, 100) <= extra_percent:
            selected[(i, j)] = 1
            neighbors[i]+=1
            neighbors[j]+=1
            m+=1

# print(neighbors)

print(f'{n} {m}')

# susc = [200 for _ in range(n)]
# inf = [0 for _ in range(n)]
# # one hub of contamination
# susc[0] = 150
# inf[0] = 50

susc = [0 for _ in range(n)]
inf = [0 for _ in range(n)]

# for _ in range(200*n):
#     susc[randint(0, n-1)]+=1
#
# for _ in range(5*n):
#     inf[randint(0, n-1)]+=1

for _ in range(200*n):
    susc[randint(0, (n-1)//2) + randint(0, (n-1)//2 + (n-1)%2)]+=1

for _ in range(5*n):
    inf[randint(0, (n-1)//2) + randint(0, (n-1)//2 + (n-1)%2)]+=1



s = ""
for k in range(n):
    s += str(susc[k]) + " "
print(s[:-1])

i = ""
for k in range(n):
    i += str(inf[k]) + " "
print(i[:-1])

for (i, j) in edges:
    if selected[(i, j)] == 1:
        d = max(neighbors[i], neighbors[j]) + 1
        print(f'{i} {j} {1/d}')
