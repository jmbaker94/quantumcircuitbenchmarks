import cirq
import numpy as np

from .toffoli_any_ancilla import MultiControlGate
from .util import reduce_circuit_or_op

class GroverIntegerSearch(cirq.Gate):
    def __init__(self, N, m, val, num_rounds=None):
        assert 0 <= val < 2 ** N, "Give a valid integer to search for."

        self.N = N
        self.m = m

        self.vals = [int(i) for i in list(bin(val))[2:][::-1]]

        if num_rounds is None:
            self.num_rounds = int(np.round(np.pi * 2 ** (self.N/2-2), 0))
        else:
            self.num_rounds = num_rounds

    def num_qubits(self):
        return self.N + self.m

    def _decompose_(self, qubits):

        qubits = list(qubits)
        controls = qubits[:self.N]
        ancilla = qubits[self.N:]

        toffoli = MultiControlGate(control_size=len(controls) - 1, ancilla_size=len(ancilla))

        def oracle():
            yield cirq.H(controls[-1])
            for i, v in enumerate(self.vals):
                if not v:
                    yield cirq.X(controls[i])

            yield toffoli(*controls, *ancilla)

            for i, v in enumerate(self.vals):
                if not v:
                    yield cirq.X(controls[i])
            yield cirq.H(controls[-1])

        def diffusion():
            for control in controls:
                yield cirq.H(control)
                yield cirq.X(control)

            yield cirq.H(controls[-1])

            yield toffoli(*controls, *ancilla)

            yield cirq.H(controls[-1])

            for control in controls:
                yield cirq.X(control)
                yield cirq.H(control)

        # Initialize
        for control in controls:
            yield cirq.H(control)

        for _ in range(self.num_rounds):
            yield oracle()
            yield diffusion()


def generate_grover_integer_search_circuit(n, m, val, num_rounds=None,
                                           to_toffoli=False):
    '''
        n: register size
        m: number of ancilla (clean)
        val: which val to search for
        num_rounds: none if do optimal
    '''
    gate = GroverIntegerSearch(N=n, m=m, val=val, num_rounds=num_rounds)
    c = reduce_circuit_or_op(
            gate(*cirq.LineQubit.range(gate.num_qubits())),
            to_toffoli=to_toffoli,
        )
    return c
