from cirq.ops import gate_features
from cirq import ops
import cirq

from .util import reduce_circuit_or_op


class QFTAdder(ops.Gate):
	"""
		Performs a QFT adder according to https://arxiv.org/pdf/quant-ph/0008033.pdf
		A + B inplace onto A. B remains unmodified
	"""

	def __init__(self, size_of_inputs):
		"""
		initializes a QFT adder based on the size of inputs A = a0a1a2...an and B = b0b1b2...bn
		require |A| = |B|

		Args:
			size_of_inputs: number of bits in the input strings A, B

		"""
		self._size_of_inputs = size_of_inputs
		self._num_qubits = 2*size_of_inputs


	def num_qubits(self):
		return self._num_qubits


	def _circuit_diagram_info_(self, args):
		"""
		for A + B, display as
		--a_0--
		--a_1--
		--...--
		--a_n--
		-+b_0--
		-+b_1--
		--...--
		-+b_n--

		"""
		return cirq.protocols.CircuitDiagramInfo(
			tuple(f'a_{i}' for i in range(self._size_of_inputs)) + tuple(f'+b_{i}' for i in range(self._size_of_inputs)))

	@staticmethod
	def _apply_qft(register):
		"""
		applies the qft to the register according to https://arxiv.org/pdf/quant-ph/0008033.pdf
		"""
		rreg = register[::-1]
		for i, q in enumerate(rreg):
			yield ops.H(q)
			for j in range(i+1, len(rreg)):
				yield ops.CZ(rreg[j], q) ** (2 * 1/(2**(j+1)))

	def _decompose_(self, qubits):
		"""
		Implements the decomposition of Draper provided in https://arxiv.org/pdf/quant-ph/0008033.pdf

		Args:
			qubits: |qubits| = 2 * self.size_of_inputs, in order a0 a1 ... an b0 b1 ... bn

		"""

		# For slicing
		qubits = list(qubits)

		assert len(qubits) == 2 * self._size_of_inputs, f'A and B must be of the same length.'

		# A and B register appear in order
		A = qubits[:self._size_of_inputs]
		B = qubits[self._size_of_inputs:][::-1]

		yield self._apply_qft(A)

		A = A[::-1]

		for i in range(self._size_of_inputs):
			for j in range(i, self._size_of_inputs):
				yield ops.CZ(B[j], A[j-i]) ** (2 * 1/(2**(i+1)))
                
		A = A[::-1]
                
		yield cirq.inverse(self._apply_qft(A))

def generate_qft_adder(n, m=None):
	if n % 2 != 0:
		raise ValueError('Odd number of qubits')

	gate = QFTAdder(n // 2)
	c = reduce_circuit_or_op(
			gate(*cirq.LineQubit.range(n))
		)
	return c
