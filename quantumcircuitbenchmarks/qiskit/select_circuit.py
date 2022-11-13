import qiskit
import numpy as np
import random
from itertools import product
            
def generate_select_circuit(n, select_nums=None):
    # N controls, N + N - 2 + 1 total qubits = n => N = (n + 1) / 2
    
    do_select_space = n - 1
    ancilla_space = (do_select_space + 1) // 2 - 1
    set_space = (do_select_space + 1) // 2

    qs = list(range(ancilla_space+set_space+1))
    set_qs = qs[:set_space]
    ancilla_qs = qs[set_space:set_space+ancilla_space]
    final_q = qs[set_space+ancilla_space]
    circuit = qiskit.circuit.QuantumCircuit(n)
    bitstrings = ["".join(p) for p in product("01", repeat=set_space)]
    previous = None
    for i in range(2**set_space):
        if select_nums != None and i not in select_nums:
            continue
        if previous == None:
            # set for the first number
            for index, c in enumerate(bitstrings[i]):
                if c == "0":
                    circuit.x(set_qs[index])
            circuit.ccx(set_qs[0], set_qs[1], ancilla_qs[0])
            for index, q in enumerate(set_qs[2:], 2):
                circuit.ccx(q, ancilla_qs[index-2], ancilla_qs[index-1])
            for index, c in enumerate(bitstrings[i]):
                if c == "0":
                    circuit.x(set_qs[index])
        else:
            # Perform an increment here
            prev_bitstring = bitstrings[previous]
            current_bitstring = bitstrings[i]
            loc = 0
            for c1, c2 in zip(prev_bitstring, current_bitstring):
                if c1 == c2:
                    loc += 1
                    continue
                break

            curr_loc = len(set_qs) - 1
            for q in reversed(set_qs[loc+1:]):
                if prev_bitstring[curr_loc] == "0":
                    circuit.x(set_qs[curr_loc])
                circuit.ccx(q, ancilla_qs[curr_loc-2], ancilla_qs[curr_loc-1])
                if prev_bitstring[curr_loc] == "0":
                    circuit.x(set_qs[curr_loc])
                curr_loc -= 1
                if curr_loc == 1:
                    break

            if loc > 1:
                circuit.cx(set_qs[loc], ancilla_qs[loc-1])
                curr_loc = loc + 1
            else:
                if loc == 0:
                    if prev_bitstring[1] != current_bitstring[1]:
                        circuit.cx(set_qs[0], ancilla_qs[0])
                        circuit.cx(set_qs[1], ancilla_qs[0])
                        if current_bitstring[0] == current_bitstring[1]:
                            circuit.x(ancilla_qs[0])
                    else:
                        circuit.cx(set_qs[0], ancilla_qs[0])
                    curr_loc = loc + 2
                elif loc == 1:
                    circuit.cx(set_qs[1], ancilla_qs[0])
                    curr_loc = loc + 1

            for index, q in enumerate(set_qs[curr_loc:], curr_loc):
                if current_bitstring[index] == "0":
                    circuit.x(set_qs[index])
                circuit.ccx(q, ancilla_qs[index-2], ancilla_qs[index-1])
                if current_bitstring[index] == "0":
                    circuit.x(set_qs[index])
        r = random.randint(0, 2)
        if r == 0:
            circuit.cx(ancilla_qs[-1], final_q)
        elif r == 1:
            circuit.cz(ancilla_qs[-1], final_q)
        elif r == 2:
            circuit.cy(ancilla_qs[-1], final_q)
        previous = i

    # unset the last qubit
    for index, c in enumerate(bitstrings[previous]):
        if c == "0":
            circuit.x(set_qs[index])
    index = len(set_qs) - 1
    for q in reversed(set_qs[2:]):
        circuit.ccx(q, ancilla_qs[index-2], ancilla_qs[index-1])
        index -= 1
    circuit.ccx(set_qs[0], set_qs[1], ancilla_qs[0])
    for index, c in enumerate(bitstrings[previous]):
        if c == "0":
            circuit.x(set_qs[index])
    return circuit