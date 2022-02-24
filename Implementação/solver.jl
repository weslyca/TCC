import Pkg

# Pkg.add("JuMP")
# Pkg.add("SCIP")

using JuMP
using SCIP

merc = Model(SCIP.Optimizer)

# ======================== Input ============================
# Esta parte do código lê um grafo, o grafo inicial para a otimização

betas = Dict()

# na primeira linha, o número de cidades/bairros
# e o número de arestas ou ruas
nCities, nEdges = split(readline())
println(nCities)
println(nEdges)
nCities = parse(Int64, nCities)
nEdges = parse(Int64, nEdges)

# na segunda linha, o número de suscetíveis de cada bairro,
# separados por um espaço

S = []
s_values = split(readline())

for s_value in s_values
    push!(S, parse(Int64, s_value))
end

# na terceira linha,  o número de infectados de cada bairros,
# separados por um espaço

I = []
i_values = split(readline())

for i_value in i_values
    push!(I, parse(Int64, i_value))
end

println(S)
println(I)

# para cada uma das linhas subsequentes, temos a especificação de uma aresta
# i j w implica uma aresta do vértice i para o vértice j, com beta w

for l=1:nEdges
    local i, j, w
    i, j, w = split(readline())
    i = parse(Int64, i)
    j = parse(Int64, j)
    w = parse(Float64, w)
    betas[i, j] = w
end

# =========================================================

v = 0.5 # virulência

# criamos a variável x[i,j], indicando se a aresta[i,j] está aberta
@variable(merc, x[i=1:nCities,j=1:nCities; i!= j && haskey(betas, (i, j))], Bin)

# restrição de que o fluxo é bidirecional
for i=1:nCities
    for j=(i+1):nCities
        if i != j && haskey(betas, (i, j))
            @constraint(merc, x[i, j] == x[j, i])
        end
    end
end

# a população inicial de cada cidade
pops = [S[i]+I[i] for i=1:nCities]

# ======= Lendo um limite superior com a árvore =================================

# aqui lemos a árvore que encontramos com nossa busca iterada...
# número de cidades e número de arestas
n_given, m_given = split(readline())
println(n_given)
println(m_given)
n_given = parse(Int64, n_given)
m_given = parse(Int64, m_given)

mst_edges = Dict()

# cada uma das arestas da árvore
for l=1:m_given
    local i, j, w
    i, j = split(readline())
    i = parse(Int64, i)
    j = parse(Int64, j)
    mst_edges[i, j] = 1
    mst_edges[j, i] = 1
end

# e por fim, o limite encontrado anteriormente
bound = readline()
println(bound)
total_infected = parse(Float64, bound)

# ==============================================================================

# a variável moving[i,j] representa a proporção de pessoas usando a rua i,j
moving = Dict()
for i=1:nCities
    for j=1:nCities
        if i != j && haskey(betas, (i, j))
            moving[i, j] = @expression(merc, betas[i, j]*x[i, j])
        end
    end
end

# as outras pessoas ficaram no próprio vértice
for i=1:nCities
    moving[i, i] = @expression(merc, (1 - sum(moving[i, j] for j=1:nCities if j!= i && haskey(betas, (i, j)))))
end

@variable(merc, z, upper_bound=total_infected)

# damos a árvore geradora mínima encontrada como uma solução
for i=1:nCities
    for j=1:nCities
        if haskey(mst_edges, (i, j))
            set_start_value(x[i, j], mst_edges[i, j])
        elseif haskey(x, (i, j))
            set_start_value(x[i, j], 0)
        end
    end
end

# a probabilidade de ocorrer um encontro
@NLexpression(merc, q[i=1:nCities], (sum(moving[j, i]*I[j] for j=1:nCities if haskey(moving, (j, i))) /
                                    (sum(moving[j, i]*I[j] for j=1:nCities if haskey(moving, (j, i))) +
                                     sum(moving[j, i]*S[j] for j=1:nCities if haskey(moving, (j, i))))))

@NLexpression(merc, newInfect[i=1:nCities], v*sum(moving[i, j]*S[i]*q[j] for j=1:nCities if haskey(moving, (i, j))))

# vamos minimizar z, que corresponde ao número de infectados depois de uma iteração
@NLconstraint(merc, z == @NLexpression(merc, sum(I[i] for i=1:nCities) + sum(newInfect[i] for i=1:nCities)))


# adicionamos as restrições com o método da mercadoria para garantir a conexidade
# escolhemos arbitrariamente o vértice 1 como fonte
@variable(merc, f[i=1:nCities, j=1:nCities; i != j && haskey(betas, (i, j))] >= 0, Int)

for i=2:nCities
    @constraint(merc, sum(f[i, j] for j=1:nCities if i != j && haskey(betas, (i, j))) + 1 ==
                      sum(f[j, i] for j=1:nCities if i != j && haskey(betas, (j, i))))
end

for i=1:nCities
    for j=1:nCities
        if haskey(f, (i, j))
            @constraint(merc, f[i, j] <= nCities)
        end
    end
end

@constraint(merc, sum(f[1, j] for j=2:nCities if haskey(betas, (1, j))) == (nCities - 1))


for i=1:nCities
    for j=1:nCities
        if haskey(betas, (i, j))
            @constraint(merc, nCities*x[i, j] >= f[i, j])
        end
    end
end


@objective(merc, Min, z)

set_optimizer_attribute(merc, "limits/nodes", 4000000)

optimize!(merc)
print(solution_summary(merc, verbose=true))

println("Value of x:")
println(value.(x))
println("Value of f")
println(value.(f))
