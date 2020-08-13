import qiskit

from .cnx_halfdirty import cnx_halfdirty

def cnx_any_dirty(circuit, controls, target, ancilla):
    def find_dirty(groups, g):
        d = []
        for f in groups:
            for e in f:
                if e not in g and e not in d:
                    d.append(e)
                    if len(d) == len(g) - 3:
                        return d
        return d
    
    m = len(ancilla)
    assert m > 0, f'If 0 ancilla are provided, please use a cnx_inplace gate instead.'

    if len(controls) == 2:
        circuit.toffoli(controls[0], controls[1], target)
    elif len(controls) == 1:
        circuit.cx(controls[0], target)
    else:
        if len(ancilla) > len(controls) - 2:
            cnx_halfdirty(circuit, controls, target, ancilla)   
        else:
            # Group the controls into m + 1 groups, do as many toffoli's as possible then start filling until can't be done
            groups = [[] for _ in range(m + 1)]

            groups[0].append(controls[0])
            for i in range(m + 1):
                groups[i].append(controls[i+1])

            i = m+2
            which_group = -1
            while i < len(controls):
                if which_group == 0:
                    groups[0].append(controls[i])
                    i += 1
                    which_group = -1
                else:
                    g = groups[-1]
                    free = sum([len(gg) if gg != g else 0 for gg in groups]) + len(ancilla) - 1
                    while len(g) + 1 < free + 2:
                        g.append(controls[i])
                        i += 1
                        if i >= len(controls):
                            break
                    if i >= len(controls):
                        break
                    which_group = 0

            for i in range(m + 1):
                if i != 0:
                    groups[i].insert(0, groups[i-1][-1])
                if i < m:
                    groups[i].append(ancilla.pop(0))
                else:
                    groups[i].append(target)

            def forward(groups):
                for g in reversed(groups):
                    if len(g) == 3:
                        circuit.toffoli(*g)
                    elif len(g) == 2:
                        circuit.cx(*g)
                    else:
                        cnx_halfdirty(circuit, controls=g[:-1], target=g[-1], ancilla=find_dirty(groups, g))

            def backward(groups):
                for g in groups[1:-1]:
                    if len(g) == 3:
                        circuit.toffoli(*g)
                    elif len(g) == 2:
                        circuit.cx(*g)
                    else:
                        cnx_halfdirty(circuit, controls=g[:-1], target=g[-1], ancilla=find_dirty(groups, g))

            forward(groups)
            backward(groups)
            forward(groups)
            backward(groups)
            
def generate_dirty_multicontrol(n, m):
    qs = list(range(n + m + 1))
    c = qiskit.circuit.QuantumCircuit(n + m + 1)
    cnx_any_dirty(c, qs[:n], qs[n], qs[n+1:])
    return c