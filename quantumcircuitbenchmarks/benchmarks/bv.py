import cirq
from .util import reduce_circuit_or_op

class BernsteinVaziraniGate(cirq.Gate):
    def __init__(self, hidden_bit_string):
        self._nq = len(hidden_bit_string) + 1
        self.hidden_bit_string = hidden_bit_string

    def num_qubits(self):
        return self._nq

    def _decompose_(self, qubits):
        qubits = list(qubits)

        yield cirq.X(qubits[-1])
        
        for qubit in qubits:
            yield cirq.H(qubit)
            
        for i in range(len(self.hidden_bit_string)):
            if self.hidden_bit_string[i] == 1:
                yield cirq.CNOT(qubits[i], qubits[-1])

        for qubit in qubits:
            yield cirq.H(qubit)
            
            
def generate_bv(bit_string):
    '''
        bit_string: list of 0, 1 values
    '''
    gate = BernsteinVaziraniGate(bit_string)
    qubits = cirq.LineQubit.range(gate.num_qubits())
    return reduce_circuit_or_op(gate(*qubits))
    
