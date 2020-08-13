import cirq
from cirq import ops

from .util import reduce_circuit_or_op


class TakahashiAdder(cirq.Gate):
    def __init__(self, register_size):
        self.register_size = register_size

    def num_qubits(self):
        return 2 * self.register_size

    def _decompose_(self, qubits):
        qubits = list(qubits)

        assert len(qubits) == 2*self.register_size

        A = qubits[:self.register_size]
        B = qubits[self.register_size:]

        for i in range(1, self.register_size):
            yield ops.CNOT(A[i], B[i])

        for i in reversed(range(1, self.register_size-1)):
            yield ops.CNOT(A[i], A[i+1])

        for i in range(self.register_size-1):
            yield ops.CCX(A[i], B[i], A[i+1])

        for i in reversed(range(1, self.register_size)):
            yield ops.CNOT(A[i], B[i])
            yield ops.CCX(A[i-1], B[i-1], A[i])

        for i in range(1, self.register_size-1):
            yield ops.CNOT(A[i], A[i+1])

        for i in range(self.register_size):
            yield ops.CNOT(A[i], B[i])

                 
def generate_takahashi_adder(n, to_toffoli=False):
    '''
        n: total size of circuit (each register is n / 2 sized)
    '''
    if n % 2 != 0:
        raise ValueError('Odd number of qubits')

    gate = TakahashiAdder(n // 2)
    c = reduce_circuit_or_op(
            gate(*cirq.LineQubit.range(gate.num_qubits())),
            to_toffoli=to_toffoli,
        )
    return c
