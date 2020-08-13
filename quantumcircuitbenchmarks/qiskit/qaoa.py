import qiskit
import networkx as nx


def generate_QAOA_circuit(graph:nx.Graph, p:int):
    '''
        Doesn't actually generate any angles. This is more about compilation than execution.
        
        The edges in the graph dictate which ZZ interations we perform; we ignore Z interactions (single qubit gates affect compilation very little)
    '''
    assert p > 0, f'Number of rounds, p, must be postive; gave p={p}'
    
    c = qiskit.circuit.QuantumCircuit(len(graph))
    qs = list(range(len(graph)))
    
    node_qbit_map = {}
    for i, n in enumerate(graph.nodes):
        node_qbit_map[n] = qs[i]
    
    for i in range(p):
        for edge in graph.edges:
            c.cx(node_qbit_map[edge[0]], node_qbit_map[edge[1]])
            c.z(node_qbit_map[edge[1]])
            c.cx(node_qbit_map[edge[0]], node_qbit_map[edge[1]])
            
        for node in graph.nodes:
            c.x(node_qbit_map[node])
            
    return c

def generate_random_QAOA(N:int, prob:float, p:int, seed=None):

    g = nx.fast_gnp_random_graph(n=N, p=prob, seed=seed)
    
    return generate_QAOA_circuit(graph=g, p=p)
