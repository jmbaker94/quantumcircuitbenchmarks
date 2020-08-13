from cirq.ops import gate_features
from cirq import ops
import cirq

# Requires use of incrementer_borrowedbit_gate.py
from .cnx_dirty_gate import CnXDirtyGate
from .incrementer_borrowedbit_gate import IncrementLinearWithBorrowedBitGate
from .util import reduce_circuit_or_op


import numpy as np


# Source: https://algassert.com/circuits/2015/06/22/Using-Quantum-Gates-instead-of-Ancilla-Bits.html
# Implemented by: Jonathan M. Baker (jmbaker@uchicago.edu)
# Verfified on all pure state inputs up to 10 qubits.

# TODO: Documentation

class CnXLinearGate(ops.Gate):
	# From http://algassert.com/circuits/2015/06/22/Using-Quantum-Gates-instead-of-Ancilla-Bits.html
	def __init__(self, reg_size):
		self._num_qubits = reg_size

	def num_qubits(self):
		return self._num_qubits

	def text_diagram_info(self):
		syms = ('@',) * (int(args.known_qubit_count) - 1)
		return ops.TextDiagramInfo(syms+('X',), connected=True)

	def _decompose_(self, qubits):
		qubits = list(qubits)
		if len(qubits) == 2:
			yield ops.CNOT(*qubits)
		elif len(qubits) == 1:
			yield ops.X(*qubits)
		elif len(qubits) == 3:
			yield ops.CCX(*qubits)
		else:
			yield self._startdecompose(qubits)

	def _startdecompose(self, qubits):
		# qubits = [c1, c2, ..., cn, T]
		# Will "bootstrap" an ancilla
		CnXOneBorrow = CnXDirtyGate(num_controls=len(qubits[:-2]), num_ancilla=1)

		yield ops.H(qubits[-1])
		yield CnXOneBorrow(*(qubits[:-2] + [qubits[-1]] + [qubits[-2]]))
		yield ops.Z(qubits[-1])**-0.25
		yield ops.CNOT(qubits[-2], qubits[-1])
		yield ops.Z(qubits[-1])**0.25
		yield CnXOneBorrow(*(qubits[:-2] + [qubits[-1]] + [qubits[-2]]))
		yield ops.Z(qubits[-1])**-0.25
		yield ops.CNOT(qubits[-2], qubits[-1])
		yield ops.Z(qubits[-1])**0.25
		yield ops.H(qubits[-1])

		IncrementLinearWithBorrowedBitOp = IncrementLinearWithBorrowedBitGate(register_size=len(qubits)-1)

		# Perform a +1 Gate on all of the top bits with bottom bit as borrowed
		yield IncrementLinearWithBorrowedBitOp(*qubits)

		# Perform  -rt Z gates
		for i in range(1, len(qubits) - 1):
			yield ops.Z(qubits[i])**(-1 * 1/(2**(len(qubits) - i)))

		# Perform a -1 Gate on the top bits
		for i in range(len(qubits) - 1):
			yield ops.X(qubits[i])
		yield IncrementLinearWithBorrowedBitOp(*qubits)
		for i in range(len(qubits) - 1):
			yield ops.X(qubits[i])

		# Perform  rt Z gates
		for i in range(1, len(qubits) - 1):
			yield ops.Z(qubits[i])**(1/(2**(len(qubits) - i)))
		yield ops.Z(qubits[0])**(1/(2**(len(qubits) - 1)))

def generate_cnx_linear(n, to_toffoli=False):
    '''
        n: total number of qubits, including target
    '''
    gate = CnXLinearGate(reg_size=n)
    c = reduce_circuit_or_op(
            gate(*cirq.LineQubit.range(gate.num_qubits())),
            to_toffoli=to_toffoli,
        )
    return c
