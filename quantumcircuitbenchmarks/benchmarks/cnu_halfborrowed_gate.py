from cirq.ops import gate_features
from cirq import ops
import cirq

from .util import reduce_circuit_or_op

class CnUHalfBorrowedGate(ops.Gate):
    def __init__(self, register_size):
        self.reg_size = register_size

        self._num_qubits = self.reg_size + self.reg_size - 3

    def num_qubits(self):
        return self._num_qubits

    def __pow__(self, exponent):
        return CnUHalfBorrowedGate(register_size=self.reg_size)

    def _circuit_diagram_info_(self, args):
        return cirq.protocols.CircuitDiagramInfo(
            ('@',) * (self.reg_size-1)  + ('X',) + ('D',) * (args.known_qubit_count-self.reg_size))

    def _decompose_(self, qubits):
        qubits = list(qubits)

        controls = qubits[:self.reg_size-1]
        target = qubits[self.reg_size-1]
        bbits = qubits[self.reg_size:]

        if len(controls) == 2:
            yield ops.CCX(controls[0], controls[1], target)
        elif len(controls) == 1:
            yield ops.CNOT(controls[0], target)
        else:
            # Build the list
            bits = []
            bits.append(controls[0])
            for i in range(1, len(controls)-1):
                bits.append(controls[i])
                bits.append(bbits[i-1])
            bits.append(controls[-1])
            bits.append(target)

            for i in range(len(bits) - 1, 0, -2):
                yield ops.CCX(bits[i-2], bits[i-1], bits[i])

            for i in range(4, len(bits) - 2, 2):
                yield ops.CCX(bits[i-2], bits[i-1], bits[i])

            for i in range(len(bits) - 1, 0, -2):
                yield ops.CCX(bits[i-2], bits[i-1], bits[i])

            for i in range(4, len(bits) - 2, 2):
                yield ops.CCX(bits[i-2], bits[i-1], bits[i])
                

def generate_cnu_halfborrowed(n):
    '''
        n: total number of qubits, including target and ancilla
    '''
    gate = CnUHalfBorrowedGate(register_size=n)
    qubits = cirq.LineQubit.range(gate.num_qubits())
    return reduce_circuit_or_op(gate(*qubits))
    
