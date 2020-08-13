import qiskit

def cnx_halfdirty(circuit, controls, target, ancilla):
    if len(controls) == 2:
        circuit.toffoli(controls[0], controls[1], target)
    elif len(controls) == 1:
        circuit.cx(controls[0], target)
    else:
        bits = []
        bits.append(controls[0])
        
        for i in range(1, len(controls) - 1):
            bits.append(controls[i])
            bits.append(ancilla[i-1])
        bits.append(controls[-1])
        bits.append(target)
        
        for i in range(len(bits) - 1, 0, -2):
            circuit.toffoli(bits[i-2], bits[i-1], bits[i])
        
        for i in range(4, len(bits) - 2, 2):
            circuit.toffoli(bits[i-2], bits[i-1], bits[i])
            
        for i in range(len(bits) - 1, 0, -2):
            circuit.toffoli(bits[i-2], bits[i-1], bits[i])
            
        for i in range(4, len(bits) - 2, 2):
            circuit.toffoli(bits[i-2], bits[i-1], bits[i])

def generate_cnx_halfdirty(n):
    c = qiskit.circuit.QuantumCircuit(n)
    
    qs = range(n)
    
    assert (n + 3) % 2 == 0
    
    reg_len = int((n + 3)  / 2)
    cnx_halfdirty(c, qs[:reg_len -1], qs[reg_len -1], qs[reg_len:])
    return c