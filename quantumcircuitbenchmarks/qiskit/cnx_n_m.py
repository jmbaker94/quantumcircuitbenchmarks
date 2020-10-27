from collections import defaultdict

def string_to_gate(circuit, s):
    if s[0] == 'toffoli':
        circuit.toffoli(s[1], s[2], s[3])
    if s[0] == 'cx':
        circuit.cx(s[1], s[2])
    if s[0] == 'cnx_log_depth':
        cnx_log_depth(circuit, *s[1:])
    if s[0] == 'cnx_half_dirty':
        cnx_halfdirty(circuit, *s[1:])
        
from .cnx_halfdirty import *
from .cnx_logdepth import *
from .cnx_inplace import *

D = defaultdict(int)
C = defaultdict(int)

def multicontrolgate(circuit, controls, target, clean_ancilla, dirty_ancilla):
    
    def _multi_control(N,M):
        # Scheme 2 seems to get compressed a lot in practice and decrease the
        # Toff depth a lot on consecutive layers of dirty bit trick
        def _compute(n,m):
            if n <= 1: # base
                return 0
            if n == 2: # cases
                C[n,m] = 2
                return 1
            if m == 0: # dirty bit trick will be stored here
                # never need to double it, because scheme 2 makes sure it's only done in the middle
                C[n,m] = -1 * n
                return 4*n-8
            if m >= n-2:
                C[n,m] = 2
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
                scheme2_cost = 2*(4*i-8) + D[n-i*splits+splits,m-splits]
            else:
                i = int(np.floor(upper))
                scheme2_cost = 2*(4*i-8) + D[n-i*splits+splits,m-splits]
            if i < 3: # This case will always be better to do other strats
                scheme2_cost = D[n,0]

            # See if it was already computed
            if (n,m) in D.keys():
                return D[n,m]

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
                if cost + D[n_prime, m_prime] < curr_min:
                    # save strategy in computing
                    C[n,m] = i
                    curr_min = cost + D[n_prime, m_prime]
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
                C[n,m] = -1 * i
                curr_min = 2*(4*i-8) + D[n-i*splits+splits,m-splits]
            return curr_min

        if (N,M) not in D.keys():
            for n in range(1,N+1):
                for m in range(0,M+1):
                    d = _compute(n,m)
                    D[n, m] = d
     
    def _prep_gates(qubits, n, m):
        controls = qubits[:n]
        target = qubits[n]
        ancilla = qubits[(n+1):(n + m + 1)]
        dirty = qubits[(n+m+1):]
        Depth, Construction = D, C

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
                        cnx_log_depth(circuit, controls[cstart:cend], ancilla[aend], ancilla[astart:aend])
                        
                        to_reverse.append(('cnx_log_depth', controls[cstart:cend], ancilla[aend], ancilla[astart:aend]))
                        
                        new_controls.append(ancilla[aend])
                        uncomputed_ancilla.extend(ancilla[astart:aend])
                        # need to invert the log gate to get ancilla back too
                        #log_gate.invert()
                    a = a - k * (i-j-1)
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
                base_controls, base_target, base_ancilla, base_dirty = _prep_gates(next_iter_bits, n-covered+new_c, m-new_c)

            else: # Scheme 2 at this layer
                i = abs(Construction[n,m])
                # dirty_gate = CnUHalfBorrowedGate(i+1)
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
                    
                    cnx_halfdirty(circuit, controls[cstart:cend], ancilla[c], dirt[dstart:dend])
                    
                    to_reverse.append(('cnx_half_dirty', controls[cstart:cend], ancilla[c], dirt[dstart:dend]))
                    
                # recursive call
                # the after the uncovered + written ancilla are new controls
                # target is still target
                # no more ancilla left, and the rest are dirty bits
                next_iter_bits = controls[(k*i):] + ancilla[:k] + [target] + ancilla[k:] + controls[:(k*i)] + dirty
                #rec_gate = MultiControlGate(n-m*i+m,0).on(*next_iter_bits)
                #yield from self.decompose_recursive(rec_gate, leave_toffoli=True)
                base_controls, base_target, base_ancilla, base_dirty = _prep_gates(next_iter_bits, n-k*i+k, m-k)
            return base_controls, base_target, base_ancilla, base_dirty
    
    if len(clean_ancilla) == 0:
        cnx_inplace(circuit, controls, target)
    else:
        ancilla = clean_ancilla
        n = len(controls)
        m = len(ancilla)
        _multi_control(n,m)
        
        to_reverse = []
        
        qubits = list(controls) + [target] + list(clean_ancilla) + list(dirty_ancilla)
        base_controls, base_target, base_ancilla, base_dirty = _prep_gates(qubits,n,m)

        if len(base_controls) == 2:
            circuit.toffoli(base_controls[0], base_controls[1], target)
        elif len(base_controls) == 1:
            circuit.cx(base_controls[0], target)
        else:
            if len(base_ancilla) == 0:
                dirt = base_dirty + base_ancilla                
                cnx_halfdirty(circuit, base_controls, target, dirt[:(len(base_controls)-2)])

        for gate in reversed(to_reverse):
            string_to_gate(circuit, gate)

            
def multicontrolgate_stop_early(circuit, controls, target, clean_ancilla, dirty_ancilla, max_n):

    def _multi_control(N,M):
        # Scheme 2 seems to get compressed a lot in practice and decrease the
        # Toff depth a lot on consecutive layers of dirty bit trick
        def _compute(n,m):
            if n <= max_n:
                return 1 # attempt at new base
            if n <= 1: # base
                return 0
            if n == 2: # cases
                C[n,m] = 2
                return 1
            if m == 0: # dirty bit trick will be stored here
                # never need to double it, because scheme 2 makes sure it's only done in the middle
                C[n,m] = -1 * n
                return 4*n-8
            if m >= n-2:
                C[n,m] = 2
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
                scheme2_cost = 2*(4*i-8) + D[n-i*splits+splits,m-splits]
            else:
                i = int(np.floor(upper))
                scheme2_cost = 2*(4*i-8) + D[n-i*splits+splits,m-splits]
            if i < 3: # This case will always be better to do other strats
                scheme2_cost = D[n,0]

            # See if it was already computed
            if (n,m) in D.keys():
                return D[n,m]

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
                if cost + D[n_prime, m_prime] < curr_min:
                    # save strategy in computing
                    C[n,m] = i
                    curr_min = cost + D[n_prime, m_prime]
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
                C[n,m] = -1 * i
                curr_min = 2*(4*i-8) + D[n-i*splits+splits,m-splits]
            return curr_min

        if (N,M) not in D.keys():
            for n in range(1,N+1):
                for m in range(0,M+1):
                    d = _compute(n,m)
                    D[n, m] = d
     
    def _prep_gates(qubits, n, m):
        controls = qubits[:n]
        target = qubits[n]
        ancilla = qubits[(n+1):(n + m + 1)]
        dirty = qubits[(n+m+1):]
        Depth, Construction = D, C

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
                        if len(controls[cstart:cend]) <= max_n:
                            circuit.mct(controls[cstart:cend], ancilla[aend])
                        else:
                            cnx_log_depth(circuit, controls[cstart:cend], ancilla[aend], ancilla[astart:aend])
                        
                        to_reverse.append(('cnx_log_depth', controls[cstart:cend], ancilla[aend], ancilla[astart:aend]))
                        
                        new_controls.append(ancilla[aend])
                        uncomputed_ancilla.extend(ancilla[astart:aend])
                        # need to invert the log gate to get ancilla back too
                        #log_gate.invert()
                    a = a - k * (i-j-1)
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
                base_controls, base_target, base_ancilla, base_dirty = _prep_gates(next_iter_bits, n-covered+new_c, m-new_c)

            else: # Scheme 2 at this layer
                i = abs(Construction[n,m])
                # dirty_gate = CnUHalfBorrowedGate(i+1)
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
                    
                    if len(controls[cstart:cend]) <= max_n:
                        circuit.mct(controls[cstart:cend], ancilla[c])
                    else:
                        cnx_halfdirty(circuit, controls[cstart:cend], ancilla[c], dirt[dstart:dend])
                    # cnx_halfdirty(circuit, controls[cstart:cend], ancilla[c], dirt[dstart:dend])
                    to_reverse.append(('cnx_half_dirty', controls[cstart:cend], ancilla[c], dirt[dstart:dend]))
                    
                # recursive call
                # the after the uncovered + written ancilla are new controls
                # target is still target
                # no more ancilla left, and the rest are dirty bits
                next_iter_bits = controls[(k*i):] + ancilla[:k] + [target] + ancilla[k:] + controls[:(k*i)] + dirty
                #rec_gate = MultiControlGate(n-m*i+m,0).on(*next_iter_bits)
                #yield from self.decompose_recursive(rec_gate, leave_toffoli=True)
                base_controls, base_target, base_ancilla, base_dirty = _prep_gates(next_iter_bits, n-k*i+k, m-k)
            return base_controls, base_target, base_ancilla, base_dirty
    
    if len(controls) < max_n:
        circuit.mct(controls, target)
    elif len(clean_ancilla) == 0:
        cnx_inplace(circuit, controls, target)
    else:
        ancilla = clean_ancilla
        n = len(controls)
        m = len(ancilla)
        _multi_control(n,m)
        
        to_reverse = []
        
        qubits = list(controls) + [target] + list(clean_ancilla) + list(dirty_ancilla)
        base_controls, base_target, base_ancilla, base_dirty = _prep_gates(qubits,n,m)
        if len(base_controls) == 2:
            circuit.toffoli(base_controls[0], base_controls[1], target)
        elif len(base_controls) == 1:
            circuit.cx(base_controls[0], target)
        else:
            if len(base_ancilla) == 0:
                if target[0] in base_controls:
                    base_controls.remove(target[0])
#                 print(base_controls, target)
                if len(base_controls) <= max_n:
                    circuit.mct(base_controls, target)
                else:
                    dirt = base_dirty + base_ancilla
                    cnx_halfdirty(circuit, base_controls, target, dirt[:(len(base_controls)-2)])
        for gate in reversed(to_reverse):
            if len(gate[1]) <= max_n:
                circuit.mct(gate[1], gate[2])
            else:
                string_to_gate(circuit, gate)
                
def acnx_n_m_maxn(circuit, controls, target, ancilla, max_n):
    for control in controls:
        circuit.x(control)
    multicontrolgate_stop_early(circuit, controls, [target], ancilla, [], max_n)
    for control in controls:
        circuit.x(control)
            
def generate_cnx_n_m(n, m):
    qs = list(range(n + m))
    c = qiskit.circuit.QuantumCircuit(n + m)
    
    multicontrolgate(c, qs[:n], [qs[n]], qs[n:], [])
    return c
                
    
def generate_cnx_n_m_maxn(n, m, max_n):
    qs = list(range(n + m))
    c = qiskit.circuit.QuantumCircuit(n + m)
    
    multicontrolgate_stop_early(c, qs[:n], [qs[n]], qs[n:], [], max_n)
    return c


                