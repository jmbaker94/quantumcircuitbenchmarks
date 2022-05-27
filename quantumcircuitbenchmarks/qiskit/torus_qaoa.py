import qiskit
import numpy as np
import random

def generate_torus_qaoa_x_y(x, y, seed=0xDEADBEEF):
    i = x*y
    qr = qiskit.QuantumRegister(i)
    qc = qiskit.QuantumCircuit(qr)
    pairs = []
    for x_val in range(x):
        for y_val in range(y):
            q_num_1 = x_val*y + y_val
            q_num_2 = x_val*y + y_val + 1
            if y_val == y-1:
                q_num_2 = x_val*y
            pairs.append((q_num_1, q_num_2))
            if x_val < x - 1:
                q_num_1 = x_val*y + y_val
                q_num_2 = (1 + x_val)*y + y_val
                pairs.append((q_num_1, q_num_2))
            elif x_val == x-1:
                q_num_2 = y_val
                pairs.append((q_num_1, q_num_2))
    random.seed(seed)
    random.shuffle(pairs)
    for pair in pairs:
        first = random.randint(0, 1)
        second = 1 - first
        qc.cx(pair[first], pair[second])
        qc.z(pair[second])
        qc.cx(pair[first], pair[second])
    return qc

def generate_torus_qaoa_max_size(max_size, seed=0xDEADBEEF):
    x = int(np.floor(np.sqrt(max_size)))
    y = int(np.floor(max_size // x))
    return generate_torus_qaoa_x_y(x, y, seed)