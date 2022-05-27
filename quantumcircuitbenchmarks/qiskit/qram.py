import qiskit
import numpy as np

def generate_quantum_qram_circuit_by_index(index_val):
    num_qubits = index_val + 2**index_val + 1
    qr = qiskit.QuantumRegister(num_qubits)
    qc = qiskit.QuantumCircuit(qr)

    for i in range(index_val, 0, -1):
        max_val = 2**i
        half_val = max_val // 2
        for j in range(index_val + max_val, index_val + half_val, -1):
            qc.cswap(i - 1, j - 1, j - 1 - half_val)

    qc.swap(index_val, num_qubits - 1)

    for i in range(1, index_val + 1):
        max_val = 2**i
        half_val = (max_val // 2)
        for j in range(index_val + half_val + 1, index_val + max_val + 1):
            qc.cswap(i - 1, j - 1, j - 1 - half_val)
    
    return qc

def generate_quantum_qram_circuit_by_size(max_size):
    max_val = None
    for j in range(max_size // 2, 0, -1):
        if j + 1 + 2**j <= max_size:
            max_val = j
            break
    if max_val == None:
        return None
    return generate_quantum_qram_circuit_by_index(max_val)