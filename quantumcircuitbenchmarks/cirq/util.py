import cirq

def reduce_circuit_or_op(circuit, to_toffoli=False):
    if to_toffoli:
        def keep(op):
            return (len(op.qubits) == 2 or len(op.qubits) == 1
                    or (op.gate == cirq.CCX or op.gate == cirq.CCZ))
    else:
        def keep(op):
            return len(op.qubits) == 2 or len(op.qubits) == 1
    return cirq.Circuit(cirq.decompose(circuit, keep=keep),
                        strategy=cirq.InsertStrategy.EARLIEST)
