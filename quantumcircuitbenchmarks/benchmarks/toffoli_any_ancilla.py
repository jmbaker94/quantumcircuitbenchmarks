from cirq.ops import gate_features
from cirq import ops
import cirq
import numpy as np
import math
from collections import defaultdict

from .cnx_logdepth_with_ancilla import CnXLogDepth
from .cnu_halfborrowed_gate import CnUHalfBorrowedGate
from .cnx_inplace import CnXLinearGate
from .util import reduce_circuit_or_op

class MultiControlGate(ops.Gate):
	D = defaultdict()
	C = defaultdict()

	def __init__(self, control_size, ancilla_size):
		self.control_size = control_size
		self.ancilla_size = ancilla_size
		self._num_qubits = control_size + ancilla_size + 1

	def __pow__(self):
		# TODO: inverse
		pass

	def num_qubits(self):
		return self._num_qubits

	def _circuit_diagram_info_(self, args):
		return cirq.protocols.CircuitDiagramInfo(
			('@',) * self.control_size  + ('X',) + ('A',) * self.ancilla_size)

	def _multi_control(self,N,M):
		# Scheme 2 seems to get compressed a lot in practice and decrease the
		# Toff depth a lot on consecutive layers of dirty bit trick
		def _compute(n,m):
			if n <= 1: # base
				return 0
			if n == 2: # cases
				self.C[n,m] = 2
				return 1
			if m == 0: # dirty bit trick will be stored here
				# never need to double it, because scheme 2 makes sure it's only done in the middle
				self.C[n,m] = -1 * n
				return 4*n-8
			if m >= n-2:
				self.C[n,m] = 2
				return (2*int(np.ceil(np.log2(n))) - 1)

			splits = m
			lower = (n+splits-2)/(2*splits)
			upper = (n+2*splits)/(2*splits)
			while np.floor(upper) < lower: # no integer in the interval
				splits = splits - 1
				lower = (n+splits-2)/(2*splits)
				upper = (n+2*splits)/(2*splits)
			if splits < 2:
				i = int(np.ceil(lower))
				scheme2_cost = 2*(4*i-8) + self.D[n-i*splits+splits,m-splits]
			else:
				i = int(np.floor(upper))
				scheme2_cost = 2*(4*i-8) + self.D[n-i*splits+splits,m-splits]
			if i < 3: # This case will always be better to do other strats
				scheme2_cost = self.D[n,0]

			# See if it was already computed
			if (n,m) in self.D.keys():
				return self.D[n,m]

			# Attempt Scheme 1
			i = m+1 #min(m + 1, n-2)
			curr_min = scheme2_cost + 1
			while i > 1:
				a = m
				new_c = 0
				covered = 0
				#mem = [0] * (m+2)
				cost = 2*(2*int(np.ceil(np.log2(i))) - 1)
				for j in range(0,i-1):
					# remember how many of each of these circuits you choose
					k = min(int(a/(i-j-1)), int((n-covered)/(i-j)))
					a = a - k*(i-j-1)
					covered = covered + k*(i-j)
					new_c = new_c + k
					if a == 0 or covered == n:
						break
				n_prime = n - covered + new_c
				m_prime = m - new_c
				if m_prime == 0 and covered < n_prime - 2:
					i = i - 1
					continue # not enough dirty to do dirty ancilla trick
				if cost + self.D[n_prime, m_prime] < curr_min:
					# save strategy in computing
					self.C[n,m] = i
					curr_min = cost + self.D[n_prime, m_prime]
				i = i - 1

			# If Scheme 1 fails, fall back to another scheme
			if curr_min > scheme2_cost:
				splits = m
				lower = (n+splits-2)/(2*splits)
				upper = (n+2*splits)/(2*splits)
				while np.floor(upper) < lower: # no integer in the interval
					splits = splits - 1
					lower = (n+splits-2)/(2*splits)
					upper = (n+2*splits)/(2*splits)
				if splits < 2:
					i = int(np.ceil(lower))
				else:
					i = int(np.floor(upper))
				self.C[n,m] = -1 * i
				curr_min = 2*(4*i-8) + self.D[n-i*splits+splits,m-splits]
			return curr_min

		if (N,M) not in self.D.keys():
			for n in range(1,N+1):
				for m in range(0,M+1):
					d = _compute(n,m)
					self.D[n, m] = d

	def _prep_gates(self, qubits, n, m):
		controls = qubits[:n]
		target = qubits[n]
		ancilla = qubits[(n+1):(n + m + 1)]
		dirty = qubits[(n+m+1):]
		Depth, Construction = self.D, self.C

		if len(controls) == 2 or len(controls) == 1:
			# base case
			return controls, target, ancilla, dirty
		elif m == 0:
			return controls, target, ancilla, dirty
		else:
			if Construction[n,m] > 0: # Scheme 1 at this layer
				i = Construction[n,m]
				a = m
				covered = 0
				covered_ancilla = 0
				new_c = 0
				new_controls = []
				uncomputed_ancilla = []
				for j in range(0,i-1):
					k = min(int(a/(i-j-1)), int((n-covered)/(i-j)))
					# k log_depth circuits with i-j inputs
					for c in range(k):
						cstart = covered + c*(i-j)
						cend = covered + (c+1)*(i-j)
						astart = covered_ancilla + c*(i-j-2) + c
						aend = covered_ancilla + (c+1)*(i-j-2) + c
						# add a log cirucit of depth i-j
						# control with the i-j controls
						# target the end ancilla
						# use the middle ancilla
						log_gate = CnXLogDepth(i-j)
						new_bit_list = controls[cstart:cend] + [ancilla[aend]] + ancilla[astart:aend]
						apply_log = log_gate.on(*new_bit_list)
						yield apply_log
						new_controls.append(ancilla[aend])
						uncomputed_ancilla.extend(ancilla[astart:aend])
						# need to invert the log gate to get ancilla back too
						#log_gate.invert()
					a = a - k*(i-j-1)
					covered = covered + k*(i-j)
					covered_ancilla = covered_ancilla + k*(i-j-1)
					new_c = new_c + k
					if a == 0 or covered == n:
						break
				# recursive call
				# the after the uncovered + written ancilla are new controls
				# target is still target
				# rest of the ancilla are still ancilla, and the rest are dirty bits
				#next_iter_bits = controls[covered:] + ancilla[:new_c] + [target] + ancilla[new_c:] + controls[:covered]
				next_iter_bits = controls[covered:] + new_controls + [target] + uncomputed_ancilla + ancilla[covered_ancilla:] + controls[:covered]
				#rec_gate = MultiControlGate(n - covered + new_c, m - a).on(*next_iter_bits)
				base_controls, base_target, base_ancilla, base_dirty = yield from self._prep_gates(next_iter_bits, n-covered+new_c, m-new_c)

			else: # Scheme 2 at this layer
				i = abs(Construction[n,m])
				dirty_gate = CnUHalfBorrowedGate(i+1)
				k = m
				lower = (n+k-2)/(2*k)
				upper = (n+2*k)/(2*k)
				while np.floor(upper) < lower: # no integer in the interval
					k = k - 1
					lower = (n+k-2)/(2*k)
					upper = (n+2*k)/(2*k)
				dirt = dirty + controls[k*i:]
				for c in range(k): # make m dirty circuits
					cstart = c*i
					cend = (c+1)*i
					dstart = c*(i-2)
					dend = (c+1)*(i-2)
					# control with the i controls
					# target is a clean ancilla
					# the extra bits are the dirty bits
					new_bit_list = controls[cstart:cend] + [ancilla[c]] + dirt[dstart:dend]
					apply_dirty = dirty_gate.on(*new_bit_list)
					yield apply_dirty
				# recursive call
				# the after the uncovered + written ancilla are new controls
				# target is still target
				# no more ancilla left, and the rest are dirty bits
				next_iter_bits = controls[(k*i):] + ancilla[:k] + [target] + ancilla[k:] + controls[:(k*i)] + dirty
				#rec_gate = MultiControlGate(n-m*i+m,0).on(*next_iter_bits)
				#yield from self.decompose_recursive(rec_gate, leave_toffoli=True)
				base_controls, base_target, base_ancilla, base_dirty = yield from self._prep_gates(next_iter_bits, n-k*i+k, m-k)
			return base_controls, base_target, base_ancilla, base_dirty

	def _decompose_(self, qubits):
		qubits = list(qubits)

		assert len(qubits) > self.control_size, f'MultiControlGate cannot be applied to fewer than {self.control_size + 1} bits'

		if len(qubits) == self.control_size + 1:
			cnx_inplace = CnXLinearGate(reg_size=len(qubits))
			yield cnx_inplace(*qubits)
		else:
			controls = qubits[:self.control_size]
			target = qubits[self.control_size]
			ancilla = qubits[(self.control_size+1):(self.control_size + self.ancilla_size+1)]
			dirty = qubits[(self.control_size+self.ancilla_size+1):]
			n = len(controls)
			m = len(ancilla)
			self._multi_control(n,m)
			base_controls, base_target, base_ancilla, base_dirty = yield from self._prep_gates(qubits,n,m)

			if len(base_controls) == 2:
				yield ops.CCX(base_controls[0], base_controls[1], target)
			elif len(base_controls) == 1:
				yield ops.CNOT(base_controls[0], target)
			else:
				if len(base_ancilla) == 0:
					dirty_gate = CnUHalfBorrowedGate(len(base_controls)+1)
					dirt = base_dirty + base_ancilla
					dirty_qubit_list = base_controls + [target] + dirt[:(len(base_controls)-2)]
					apply_dirty = dirty_gate.on(*dirty_qubit_list)
					yield apply_dirty

			yield (cirq.inverse(self._prep_gates(qubits,n,m)))


def generate_cnx_n_m(n, m):
    '''
        n: number of controls + target
        m: number of ancilla (clean)
    '''
    cmtg = MultiControlGate(control_size=n - 1, ancilla_size=m)
    c = reduce_circuit_or_op(
            cmtg(*cirq.LineQubit.range(cmtg.num_qubits()))
        )
    return c
