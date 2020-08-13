from cirq.ops import gate_features
from cirq import ops
import cirq

from .util import reduce_circuit_or_op


class CuccaroAdder(ops.Gate):
	"""
		Performs a ripple-carry reversible adder according to https://arxiv.org/pdf/quant-ph/0410184.pdf
		in place onto B with carryin and carryout
	"""
	def __init__(self, register_size):
		"""
		initializes a Cuccarro-style ripple carry reversible adder with strings
		cin a0 a1 a2 ... an b0 b1 ... bn cout

		Args:
			register_size: the number of bits in the input strings A, B

		"""
		self._register_size = register_size
		self._num_qubits = 2 * self._register_size + 2

	def num_qubits(self):
		return self._num_qubits


	def _circuit_diagram_info_(self, args):
		"""
		--ci--
		--a0--
		--a1--
		--..--
		--an--
		--b1--
		--b2--
		--..--
		--bn--
		--co--
		"""
		return cirq.protocols.CircuitDiagramInfo(
			('ci',) +
			tuple(f'a{i}' for i in range(self._register_size)) +
			tuple(f'b{i}' for i in range(self._register_size)) +
			('co',))

	@staticmethod
	def _maj(reg):
		"""
			applies the MAJ operator to a three bit register

			------X--@----
			---X--|--@----
			---@--@--X----

		"""
		yield ops.CNOT(reg[2], reg[1])
		yield ops.CNOT(reg[2], reg[0])
		yield ops.CCX(reg[0], reg[1], reg[2])


	@staticmethod
	def _uma_parallel(reg):
		"""
			applies the UMA operator which maximizes parallism

			------@---@----X-----
			--X---X---@--X-|--X--
			----------X----@--@--

		"""
		yield ops.X(reg[1])
		yield ops.CNOT(reg[0], reg[1])
		yield ops.CCX(reg[0], reg[1], reg[2])
		yield ops.X(reg[1])
		yield ops.CNOT(reg[2], reg[0])
		yield ops.CNOT(reg[2], reg[1])


	def _decompose_(self, qubits):
		"""
		applies the Cuccaro adder decomposition according to https://arxiv.org/pdf/quant-ph/0410184.pdf

		Args:
			qubits: |qubits| = 2 * self.register_size + 2
		"""

		qubits = list(qubits)
		assert len(qubits) == 2 * self._register_size + 2, f'must provide the correct number of inputs'

		A = qubits[1:self._register_size + 1]
		B = qubits[self._register_size + 1:-1]

		cin = qubits[0]
		cout = qubits[-1]

		yield self._maj([cin, B[0], A[0]])

		for i in range(1, len(B)):
			yield self._maj([A[i-1], B[i], A[i]])

		yield ops.CNOT(A[-1], cout)

		for i in reversed(range(1, len(B))):
			yield self._uma_parallel([A[i-1], B[i], A[i]])

		yield self._uma_parallel([cin, B[0], A[0]])


def generate_cuccaro_adder(n, to_toffoli=False):
    '''
        n: total size of circuit (each register is (n-2) / 2 sized)
    '''
    if n % 2 != 0:
        raise ValueError('Odd number of qubits')

    gate = CuccaroAdder((n-2) // 2)
    c = reduce_circuit_or_op(
            gate(*cirq.LineQubit.range(n)),
            to_toffoli=to_toffoli,
        )
    return c
