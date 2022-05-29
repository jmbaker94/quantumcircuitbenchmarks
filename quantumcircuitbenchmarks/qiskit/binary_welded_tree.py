import qiskit
import numpy as np
import random

def bwt_level_qubits(levels, num_qubits, seed=0xDEADBEEF):
    random.seed(seed)
    pairs = []
    for l in range(levels):
        if l == 0:
            continue
        for val in range(0, 2**l):
            start = 1 if l == 1 else (2**(l - 1) + 1)
            current_node = start + val
            half_val = (current_node+1) // 2 - 1
            pairs.append((half_val, current_node))
            pairs.append((num_qubits - 1 - half_val, num_qubits - 1 - current_node))
    random.seed(seed)
    random.shuffle(pairs)
    qr = qiskit.QuantumRegister(num_qubits)
    qc = qiskit.QuantumCircuit(qr)
    for pair in pairs:
        first = random.randint(0, 1)
        second = 1 - first
        qc.cx(pair[first], pair[second])
        qc.z(pair[second])
        qc.cx(pair[first], pair[second])
    return qc

def generate_bwt_max_width(width, seed=0xDEADBEEF):
    n = i
    levels = 1
    num_qubits = 1
    max_level = int(np.log2(width))
    while levels < max_level:
        if num_qubits + 2**levels + 2**(levels - 1) >= n:
            break
        num_qubits += 2**levels + 2**(levels - 1)
        levels += 1
    return bwt_level_qubits(levels, num_qubits)

def generate_bwt_max_qubits(max_qubits, seed=0xDEADBEEF):
    n = max_qubits
    levels = 1
    num_qubits = 1
    while num_qubits < n:
        if num_qubits + 2**levels + 2**(levels - 1) >= n:
            break
        num_qubits += 2**levels + 2**(levels - 1)
        levels += 1
    return bwt_level_qubits(levels, num_qubits, seed)