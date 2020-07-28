import cirq

def keep(op):
    return len(op.qubits) == 2 or len(op.qubits) == 1


def reduce_circuit_or_op(circuit, to_toffoli=False):
    return cirq.Circuit(cirq.decompose(circuit, keep=keep), strategy=cirq.InsertStrategy.EARLIEST)
