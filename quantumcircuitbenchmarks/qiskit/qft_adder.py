import numpy as np
import qiskit

def qft_adder(c, a, b):    
    b = b[::-1]
    
    qft = qiskit.circuit.library.basis_change.QFT(num_qubits=len(a))
    c.append(qft, a)
    a = a[::-1]
    
    for i in range(len(a)):
        for j in range(len(b)):
            c.crz(np.pi ** (2 * 1/(2 ** (i + 1))), b[j], a[j - 1])
            
    a = a[::-1]
    qftinv = qiskit.circuit.library.basis_change.QFT(num_qubits=len(a), inverse=True)
    c.append(qftinv, a)
    

def generate_qft_adder(n):
    c = qiskit.circuit.QuantumCircuit(n)
    qs = list(range(n))
    qft_adder(c, qs[:int(n/2)], qs[int(n/2):])
    return c