from cirq.ops import gate_features
from cirq import ops
import cirq
import numpy as np
import math

from .util import reduce_circuit_or_op

# requires n-2 clean ancilla for a register_size of n
class CnXLogDepth(ops.Gate):
	def __init__(self, register_size):
		self.reg_size = register_size
		self._num_qubits = self.reg_size + self.reg_size - 1

	def __pow__(self, exponent):
		if exponent == 1:
			return self
		elif exponent == -1:
			return self
		else:
			return NotImplemented

	def num_qubits(self):
		return self._num_qubits

	def _circuit_diagram_info_(self, args):
		return cirq.protocols.CircuitDiagramInfo(
			('@',) * self.reg_size  + ('X',) + ('A',) * (args.known_qubit_count-self.reg_size-1))

	def _decompose_(self, qubits):
		qubits = list(qubits)

		controls = qubits[:self.reg_size]
		target = qubits[self.reg_size]
		ancilla = qubits[self.reg_size+1:]

		if len(controls) == 2:
			yield ops.CCX(controls[0], controls[1], target)
		elif len(controls) == 1:
			yield ops.CNOT(controls[0], target)
		else:
			# Build the list
			depth = int(np.ceil(np.log2(len(controls))) - 1)
			new_bits = controls
			curr_ancil = 0
			store_gates = []
			for layer in range(depth):
				bits = new_bits
				new_bits = []
				for i in range(len(bits)//2):
					g = ops.CCX(bits[2*i], bits[2*i+1], ancilla[curr_ancil])
					yield g
					store_gates.append(g)
					new_bits.append(ancilla[curr_ancil])
					curr_ancil = curr_ancil + 1
				if len(bits) % 2 == 1:
					new_bits.append(bits[-1])
			yield ops.CCX(new_bits[0], new_bits[1], target)
			# Get the ancilla back
			yield from cirq.inverse(store_gates)

def generate_cnx_log_depth(r):
    '''
        r: total number of qubits, including ancilla and target
    '''
    if (r + 1) % 2 != 0:
        raise ValueError('Invalid')

    gate = CnXLogDepth(register_size=(r+1)//2)
    c = reduce_circuit_or_op(
            gate(*cirq.LineQubit.range(gate.num_qubits()))
        )
    return c
