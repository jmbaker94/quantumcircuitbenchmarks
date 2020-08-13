import qiskit
from .cnx_dirty import *


def incrementer_borrowed_bit(circuit, qubits):
    def _prepare_bb_bits(current, qubits):
        new_list = []
        for q in current:
            new_list.append(_find_borrowable(current + new_list, qubits)[0])
            new_list.append(q)
        return new_list
    
    def _find_borrowable(current, qubits):
        for q in qubits:
            if q not in current:
                return [q]
            
    def _linear_increment_n_bb(qubits):
            # Expecting qubits = [x1, A, x2, B, x3, C, ..., Z] i.e. alternating bb with ob = output bit
            for i in range(1, len(qubits) - 2, 2):
                circuit.cx(qubits[0], qubits[i])
                circuit.x(qubits[i+1])
            circuit.x(qubits[-1])

            for i in range(2, len(qubits) - 1, 2):
                circuit.cx(qubits[i-2], qubits[i-1])
                circuit.toffoli(qubits[i], qubits[i-1], qubits[i-2])
                circuit.toffoli(qubits[i-2], qubits[i-1], qubits[i])
            circuit.cx(qubits[-2], qubits[-1])

            for i in reversed(range(2, len(qubits) - 1, 2)):
                circuit.toffoli(qubits[i-2], qubits[i-1], qubits[i])
                circuit.toffoli(qubits[i], qubits[i-1], qubits[i-2])
                circuit.cx(qubits[i], qubits[i-1])

            for i in range(2, len(qubits) - 1, 2):
                circuit.x(qubits[i])

            for i in range(2, len(qubits) - 1, 2):
                circuit.cx(qubits[i-2], qubits[i-1])
                circuit.toffoli(qubits[i], qubits[i-1], qubits[i-2])
                circuit.toffoli(qubits[i-2], qubits[i-1], qubits[i])
            circuit.cx(qubits[-2], qubits[-1])

            for i in reversed(range(2, len(qubits) - 1, 2)):
                circuit.toffoli(qubits[i-2], qubits[i-1], qubits[i])
                circuit.toffoli(qubits[i], qubits[i-1], qubits[i-2])
                circuit.cx(qubits[i], qubits[i-1])

            for i in range(1, len(qubits) - 2, 2):
                circuit.cx(qubits[0], qubits[i])
    
    def _split_incrementer_borrowed_bit(current, qubits):
        top_half = current[:(len(current)-1)//2 + 1]
        bottom_half = current[(len(current)-1)//2 + 1:]
        
        correctly_arranged_qubits_with_borrowed_bits = _prepare_bb_bits([bottom_half[-1]] + bottom_half[:-1], qubits)
        _linear_increment_n_bb(correctly_arranged_qubits_with_borrowed_bits)
        circuit.x(bottom_half[-1])
        
        # CX Block
        for i in range(len(bottom_half) - 1):
            circuit.cx(bottom_half[-1], bottom_half[i])
            
        # Perform a CnX Gate
        cnx_any_dirty(circuit, controls=top_half, target=bottom_half[-1], ancilla=[bottom_half[0]])
        
        # CX Block
        for i in range(len(bottom_half) - 1):
            circuit.cx(bottom_half[-1], bottom_half[i])
            
        # len(bottom) <= len(top)
        for i in range(len(bottom_half)-1):
            circuit.x(bottom_half[i])
        _linear_increment_n_bb(correctly_arranged_qubits_with_borrowed_bits)
        for i in range(len(bottom_half)):
            circuit.x(bottom_half[i])
            
        # CX Block
        for i in range(len(bottom_half) - 1):
            circuit.cx(bottom_half[-1], bottom_half[i])
            
        # Perform a CnX Gate
        cnx_any_dirty(circuit, controls=top_half, target=bottom_half[-1], ancilla=[bottom_half[0]])
        
        # CX Block
        for i in range(len(bottom_half) - 1):
            circuit.cx(bottom_half[-1], bottom_half[i])
            
        if 2 * len(top_half) <= len(qubits):
            correctly_arranged_qubits_with_borrowed_bits = _prepare_bb_bits(top_half, qubits)
            _linear_increment_n_bb(correctly_arranged_qubits_with_borrowed_bits)
        else:
            _split_incrementer_borrowed_bit(top_half + _find_borrowable(top_half, current), qubits)
    
    _split_incrementer_borrowed_bit(list(qubits), list(qubits))
    
def generate_incrementer(n):
    qs = list(range(n))
    c = qiskit.circuit.QuantumCircuit(n)
    incrementer_borrowed_bit(c, qs)
    return c