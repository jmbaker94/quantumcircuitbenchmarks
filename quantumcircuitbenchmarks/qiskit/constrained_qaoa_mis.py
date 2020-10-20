# Making a better MIS circuit
import numpy as np
import networkx as nx
import sys
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.aqua.operators import WeightedPauliOperator
from qiskit.circuit import Parameter
from qiskit.quantum_info import Pauli
from itertools import combinations
import random
import qiskit
from .cnx_n_m import *

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
    shift = -num_nodes / 2
    return WeightedPauliOperator(paulis=pauli_list), shift

def qaoa_mis(g, num_rounds, num_ancilla, maxn, max_anc_per_node):
    '''
        g: graph to do MIS on
        num_rounds: number of times to repeat
        num_ancilla: total ancilla available
        maxn: what types of gates can be done as is, natively
        
        Ignores the RX (easy to change, jsut current decomps don't have it incorporated)
    
    '''
    assert max_anc_per_node <= num_ancilla
    
    def obj(x):
        return -sum(x)
    
    N = len(g.nodes)
    M = num_ancilla
    
    C, offset = get_max_independent_set_operator(N)
    
    # Mixer circuit
    beta = Parameter('beta')
    # First, allocate registers
    gqubits = QuantumRegister(N)
    
    if M > 0:
        aqubits = QuantumRegister(M)
        mcircuit = qiskit.QuantumCircuit(gqubits, aqubits)
    else:
        mcircuit = qiskit.QuantumCircuit(gqubits)
        
    # Sort the nodes by their degree
    
    curr_ancilla_index = 0

    for u in sorted(g.degree, key=lambda x: x[1], reverse=False):
        node, degree = u[0], u[1]

        nl = list(g.neighbors(node))
        if not nl:
            mcircuit.rx(2 * beta, gqubits[node])
        else:
            # Need to give some ancilla from the pool to the gates executing if number of controls too big
            if len(nl) <= maxn:
                # Don't decompose just do it as is with no ancilla
                mcircuit.x([gqubits[q] for q in nl])
                mcircuit.mct([gqubits[q] for q in nl], node)
                mcircuit.x([gqubits[q] for q in nl])
            else:
                # Needs Ancilla to decompose with our MACT decomp
                # Evenly divide ancilla, i.e. round robin them into these circuits
                if len(nl) - 2 < max_anc_per_node: # Just give it that many
                    anc = []
                    while len(anc) < len(nl) - 2:
                        anc.append(aqubits[curr_ancilla_index])
                        curr_ancilla_index = (curr_ancilla_index + 1) % len(aqubits)
                    
                    acnx_n_m_maxn(mcircuit, [gqubits[q] for q in nl], node, anc, maxn)
                else:
                    anc = []
                    while len(anc) < max_anc_per_node:
                        anc.append(aqubits[curr_ancilla_index])
                        curr_ancilla_index = (curr_ancilla_index + 1) % len(aqubits)
                    
                    acnx_n_m_maxn(mcircuit, [gqubits[q] for q in nl], node, anc, maxn)
            
        
    # manually set up the initial state circuit
    initial_state_circuit = QuantumCircuit(gqubits)
    
    angles = []
    for i in range(2*num_rounds):
        angles.append(random.random() *  2 * np.pi)
    circuit = QuantumCircuit(gqubits, aqubits)
    circuit += initial_state_circuit

    for idx in range(num_rounds):
        beta_val, gamma = angles[idx], angles[idx + num_rounds]
        circuit += C.evolve(
            evo_time=gamma, num_time_slices=1, quantum_registers=gqubits
        )
        # beta_parameter = mixer_circuit.parameters.pop() # checked in constructor that there's only one parameter
        circuit += mcircuit# .bind_parameters({beta: beta_val})
        
    return circuit
