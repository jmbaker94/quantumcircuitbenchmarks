import cirq
import networkx as nx
from typing import Union

def generate_QAOA_circuit(graph: nx.Graph, p : int):
    '''
        Doesn't actually generate any angles. This is more about compilation than execution.
        
        The edges in the graph dictate which ZZ interations we perform; we ignore Z interactions (single qubit gates affect compilation very little)
    '''
    assert p > 0, f'Number of rounds, p, must be postive; gave p={p}'
    
    qubits = cirq.LineQubit.range(len(graph))
    
    node_qbit_map = {}
    for i, n in enumerate(graph.nodes):
        node_qbit_map[n] = qubits[i]
    
    c = cirq.Circuit()
    
    for i in range(p):
        for edge in graph.edges:
            c.append(cirq.CNOT(node_qbit_map[edge[0]], node_qbit_map[edge[1]]))
            c.append(cirq.Z(node_qbit_map[edge[1]]))
            c.append(cirq.CNOT(node_qbit_map[edge[0]], node_qbit_map[edge[1]]))
            
        for node in graph.nodes:
            c.append(cirq.X(node_qbit_map[node]))
            
    return c

def generate_random_QAOA(N : int, prob : float, p : int, seed : Union[int, None]=None):

    g = nx.fast_gnp_random_graph(n=N, p=prob, seed=seed)
    
    return generate_QAOA_circuit(graph=g, p=p)