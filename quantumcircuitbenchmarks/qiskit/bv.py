import qiskit

def bernstein_vazirani(c, register, hidden_bit_string):
    '''
        Applies BV circuit on register of c with hidden_bit_string codeword
    '''
    assert len(register) == len(hidden_bit_string) + 1
    
    c.x(register[-1])
    
    for q in register:
        c.h(q)
        
    for i in range(len(hidden_bit_string)):
        if hidden_bit_string[i] == 1:
            c.cx(register[i], register[-1])
            
    for q in register:
        c.h(q)
        
def generate_bv(bitstring):
    c = qiskit.circuit.QuantumCircuit(len(bitstring) + 1)
    qs = list(range(len(bitstring) + 1))
    
    bernstein_vazirani(c, qs, bitstring)
    return c