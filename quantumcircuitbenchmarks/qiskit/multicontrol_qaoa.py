import numpy as np
import networkx as nx
import sys
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.aqua.operators import WeightedPauliOperator
from qiskit.circuit import Parameter
from qiskit.quantum_info import Pauli
from itertools import combinations

import random

def mact(circuit, q_controls, q_target, ancilla):
    """
    Apply multiple anti-control Toffoli gate 

    Args:
        circuit (QuantumCircuit): The QuantumCircuit object to apply the mct gate on.
        q_controls (QuantumRegister or list(Qubit)): The list of control qubits
        q_target (Qubit): The target qubit
        q_ancilla (QuantumRegister or list(Qubit)): The list of ancillary qubits
    """
    circuit.x(q_controls)
    circuit.mct(q_controls, q_target[0], ancilla)
    circuit.x(q_controls)


def get_max_independent_set_operator(num_nodes):
    """
    Contructs the cost operator for max independent set
    1/2 \sum_i Z_i

    Args:
        num_nodes (int): Number of nodes
    """
    pauli_list = []
    for i in range(num_nodes):
        x_p = np.zeros(num_nodes, dtype=np.bool)
        z_p = np.zeros(num_nodes, dtype=np.bool)
        z_p[i] = True
        pauli_list.append([0.5, Pauli(z_p, x_p)])
    shift = -num_nodes/2
    return WeightedPauliOperator(paulis=pauli_list), shift

def generate_QAOA_multicontrol_circuit(G: nx.Graph, p: int,
    initial_state_string='', initial_state_variation='all_zero'):
    
    vertex_num = G.number_of_nodes()
    
    def obj(x):
        return -sum(x)

    # Generate cost Hamiltonian
    C, offset = get_max_independent_set_operator(vertex_num)

    # Mixer circuit
    beta = Parameter('beta')
    # First, allocate registers
    qu = QuantumRegister(vertex_num)
    ancilla_for_multi_toffoli = QuantumRegister(vertex_num - 2)
    ancilla_for_rx = QuantumRegister(1)
    cu = ClassicalRegister(vertex_num)
        
    mixer_circuit = QuantumCircuit(qu, ancilla_for_multi_toffoli, ancilla_for_rx, cu)
    
    for u in G.nodes():
        neighbor_list = list(G.neighbors(u))
        if not neighbor_list:
            mixer_circuit.rx(2 * beta, qu[u])
        else:
            mact(mixer_circuit, list(qu[x] for x in G.neighbors(u)), ancilla_for_rx, ancilla_for_multi_toffoli)

            mixer_circuit.mcrx(2 * beta, ancilla_for_rx, qu[u])

            mact(mixer_circuit, list(qu[x] for x in G.neighbors(u)), ancilla_for_rx, ancilla_for_multi_toffoli)

    # manually set up the initial state circuit
    initial_state_circuit = QuantumCircuit(qu)

    assert isinstance(initial_state_string, str), "need to pass the initial state as a string"
    if initial_state_string != '':
        assert len(initial_state_string) == vertex_num, "string length need to equal the number of nodes"
    for i in range(len(initial_state_string)):
        current_state = initial_state_string[i]
        # Qiskit is doing in reverse order. For the first number in the initial_state, it means the last qubit
        actual_i = len(initial_state_string) - 1 - i
        if current_state == '1':
            initial_state_circuit.x(actual_i)

    # initialize circuit, possibly based on given register/initial state
    angles = []
    for i in range(2*p):
        angles.append(random.random() *  2 * np.pi)
    circuit = QuantumCircuit(qu, ancilla_for_multi_toffoli, ancilla_for_rx, cu)
    circuit += initial_state_circuit

    for idx in range(p):
        beta_val, gamma = angles[idx], angles[idx + p]
        circuit += C.evolve(
            evo_time=gamma, num_time_slices=1, quantum_registers=qu
        )
        # beta_parameter = mixer_circuit.parameters.pop() # checked in constructor that there's only one parameter
        circuit += mixer_circuit.bind_parameters({beta: beta_val})

    return circuit

def generate_random_regular_multicontrol_qaoa(n, degree, p,
    graph_seed=0xDEADBEEF, angle_seed=0xC0FFEE):
    data_qubits = (n + 1) // 2
    G = nx.random_regular_graph(degree, data_qubits, graph_seed)
    random.seed(angle_seed)
    return generate_QAOA_multicontrol_circuit(G, p)


def generate_random_multicontrol_qaoa(n, max_degree, p, prob,
    graph_seed=0xDEADBEEF, angle_seed=0xC0FFEE):
    data_qubits = (n + 1) // 2
    edges = combinations(range(data_qubits), 2)
    G = nx.Graph()
    G.add_nodes_from(range(data_qubits))
    assert prob < 1, "prob must be between 0 and 1"
    if prob > 0:
        random.seed(graph_seed)
        degrees = {}
        for n in G.nodes(): degrees[n] = 0
        at_max = set()

        for e in edges:
            if len(at_max) == data_qubits:
                break
            if degrees[e[0]] >= max_degree or degrees[e[1]] >= max_degree:
                continue
            f = random.random()
            if f < prob:
                G.add_edge(*e)
                degrees[e[0]] += 1
                degrees[e[1]] += 1
                if degrees[e[0]] >= max_degree:
                    at_max.add(e[0])
                if degrees[e[1]] >= max_degree:
                    at_max.add(e[1])

    random.seed(angle_seed)
    return generate_QAOA_multicontrol_circuit(G, p)
