import numpy as np
import qiskit

from .incrementer_borrowedbit import *
from .cnx_dirty import *

def cnx_inplace(circuit, controls, target):
    def _startdecompose(qubits):
        circuit.h(qubits[-1])
        cnx_any_dirty(circuit, qubits[:-2], qubits[-1], [qubits[-2]])
        circuit.tdg(qubits[-1])
        circuit.cx(qubits[-2], qubits[-1])
        circuit.t(qubits[-1])
        cnx_any_dirty(circuit, qubits[:-2], qubits[-1], [qubits[-2]])
        circuit.tdg(qubits[-1])
        circuit.cx(qubits[-2], qubits[-1])
        circuit.t(qubits[-1])
        circuit.h(qubits[-1])
        
        incrementer_borrowed_bit(circuit, qubits)
        
        angle = -np.pi / (2 ** (len(qubits) - 1))
        for i in range(1, len(qubits) - 1):
            circuit.rz(angle, qubits[i])
            angle *= 2
        
        for i in range(len(qubits) - 1):
            circuit.x(qubits[i])
        incrementer_borrowed_bit(circuit, qubits)
        for i in range(len(qubits) - 1):
            circuit.x(qubits[i])
            
        angle = -np.pi / (2 ** (len(qubits) - 1))
        for i in range(1, len(qubits) - 1):
            circuit.rz(angle, qubits[i])
            angle *= 2
            
    if len(controls) == 1:
        circuit.cx(controls[0], target)
    elif len(controls) == 2:
        circuit.toffoli(controls[0], controls[1], target)
    elif len(controls) == 0:
        circuit.x(target)
    else:
        _startdecompose(controls + [target])
        
    
            
def generate_cnx_inplace(n):
    qs = list(range(n))
    c = qiskit.circuit.QuantumCircuit(n)
    cnx_inplace(c, qs[:-1], qs[-1])
    return c