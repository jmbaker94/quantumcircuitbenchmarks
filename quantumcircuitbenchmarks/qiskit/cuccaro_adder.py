import qiskit

def cuccaro_adder(c, cin, a, b, cout):
    def _maj(reg):
        c.cx(reg[2], reg[1])
        c.cx(reg[2], reg[0])
        c.ccx(reg[0], reg[1], reg[2])
        
    def _uma_parallel(reg):
        c.x(reg[1])
        c.cx(reg[0], reg[1])
        c.toffoli(reg[0], reg[1], reg[2])
        c.x(reg[1])
        c.cx(reg[2], reg[0])
        c.cx(reg[2], reg[1])
        
    _maj([cin, b[0], a[0]])
    
    for i in range(1, len(b)):
        _maj([a[i-1], b[i], a[i]])
        
    c.cx(a[-1], cout)
    
    for i in reversed(range(1, len(b))):
        _uma_parallel([a[i-1], b[i], a[i]])

    _uma_parallel([cin, b[0], a[0]])


def generate_cuccaro_adder(n):
    '''
        n: total size of circuit (each register is (n-2) / 2 sized)
    '''
    if n % 2 != 0:
        raise ValueError('Odd number of qubits')
        
    c = qiskit.circuit.QuantumCircuit(n)
        
    qs = list(range(n))
    cin = qs[0]
    cout = qs[-1]
    a = qs[1:int(n / 2)]
    b = qs[int(n / 2):-1]
    cuccaro_adder(c, cin, a, b, cout)
    return c
