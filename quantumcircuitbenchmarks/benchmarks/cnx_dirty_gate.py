from cirq.ops import gate_features
from cirq import ops
import cirq
import numpy as np
import math

from .cnu_halfborrowed_gate import CnUHalfBorrowedGate
from .util import reduce_circuit_or_op

# requires n-2 clean ancilla for a register_size of n
class CnXDirtyGate(ops.Gate):
    def __init__(self, num_controls, num_ancilla):
        self.n = num_controls

        self._num_qubits = self.n + 1 + num_ancilla

    def num_qubits(self):
        return self._num_qubits

    def __pow__(self, exponent):
        if exponent == 1:
            return self
        elif exponent == -1:
            return self
        else:
            return NotImplemented

    def _circuit_diagram_info_(self, args):
        return cirq.protocols.CircuitDiagramInfo(
            ('@',) * self.n  + ('X',) + ('D',) * (args.known_qubit_count-self.n-1))

    def _decompose_(self, qubits):

        def find_dirty(groups, g):
            d = []
            for f in groups:
                for e in f:
                    if e not in g and e not in d:
                        d.append(e)
                        if len(d) == len(g) - 3:
                            return d
            return d

        assert len(qubits) >= self.n + 1, f'Invalid application of a {self.n} control gate to {len(qubits)}'


        qubits = list(qubits)
        controls = qubits[:self.n]
        target = qubits[self.n]
        ancilla = qubits[self.n+1:]

        m = len(ancilla)
        assert m > 0, f'If 0 ancilla are provided, please use a cnx_inplace gate instead.'

        if len(controls) == 2:
            yield ops.CCX(controls[0], controls[1], target)
        elif len(controls) == 1:
            yield ops.CNOT(controls[0], target)
        else:
            if len(ancilla) > self.n - 2:
                half_borrowed_gate = CnUHalfBorrowedGate(register_size=self.n+1)
                yield half_borrowed_gate(*controls, target, *ancilla[:self.n - 2])
            else:
                # Group the controls into m + 1 groups, do as many toffoli's as possible then start filling until can't be done
                groups = [[] for _ in range(m + 1)]

                #for i in range(1, m):
                #    groups[i].append(ancilla[i-1])

                groups[0].append(controls[0])
                for i in range(m + 1):
                    groups[i].append(controls[i+1])

                i = m+2
                which_group = -1
                while i < len(controls):
                    if which_group == 0:
                        groups[0].append(controls[i])
                        i += 1
                        which_group = -1
                    else:
                        g = groups[-1]
                        free = sum([len(gg) if gg != g else 0 for gg in groups]) + len(ancilla) - 1
                        while len(g) + 1 < free + 2:
                            g.append(controls[i])
                            i += 1
                            if i >= len(controls):
                                break
                        if i >= len(controls):
                            break
                        which_group = 0

                for i in range(m + 1):
                    if i != 0:
                        groups[i].insert(0, groups[i-1][-1])
                    if i < m:
                        groups[i].append(ancilla.pop(0))
                    else:
                        groups[i].append(target)

                def forward(groups):
                    for g in reversed(groups):
                        if len(g) == 3:
                            yield ops.CCX(*g)
                        elif len(g) == 2:
                            yield ops.CNOT(*g)
                        else:
                            half_borrowed_gate = CnUHalfBorrowedGate(register_size=len(g))
                            yield half_borrowed_gate(*g, *find_dirty(groups, g))

                def backward(groups):
                    for g in groups[1:-1]:
                        if len(g) == 3:
                            yield ops.CCX(*g)
                        elif len(g) == 2:
                            yield ops.CNOT(*g)
                        else:
                            half_borrowed_gate = CnUHalfBorrowedGate(register_size=len(g))
                            yield half_borrowed_gate(*g, *find_dirty(groups, g))

                yield forward(groups)
                yield backward(groups)
                yield forward(groups)
                yield backward(groups)


class OrDirtyGate(cirq.Gate):
    def __init__(self, num_controls, num_ancilla):
        self.n = num_controls

        self._num_qubits = self.n + 1 + num_ancilla

    def num_qubits(self):
        return self._num_qubits

    def _decompose_(self, qubits):
        qubits = list(qubits)

        controls = qubits[:self.n]
        target = qubits[self.n]
        ancilla = qubits[self.n+1:]

        cnx = CnXDirtyGate(num_controls=self.n, num_ancilla=len(ancilla))


        for q in controls:
            yield cirq.X(q)

        yield cnx(*controls, target, *ancilla)

        for q in controls:
            yield cirq.X(q)
        yield cirq.X(target)


def generate_dirty_multicontrol(n, m, to_toffoli=False):
    """
        n: number of controls + target
        m: number of ancilla
    """
    cmtg = CnXDirtyGate(num_controls=n-1, num_ancilla=m)
    c = reduce_circuit_or_op(
            cmtg(*cirq.LineQubit.range(cmtg.num_qubits())),
            to_toffoli=False,
        )
    return c
