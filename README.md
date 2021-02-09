# Quantum Circuit Benchmarks

Included are a set of quantum circuit benchmarks which produce [Cirq](https://github.com/quantumlib/cirq) or [Qiskit](https://github.com/Qiskit/qiskit) circuits.
These circuits are primarily useful for studying scalability as they can all be parameterized by size.


## Install

Install the latest version:
```bash
python3 -m pip install git+https://github.com/jmbaker94/quantumcircuitbenchmarks@master
```

Or install in development mode:
```bash
git clone https://github.com/jmbaker94/quantumcircuitbenchmarks
cd quantumcircuitbenchmarks
python3 -m pip install -e .
```

## Examples

```python
from quantumcircuitbenchmarks.cirq import generate_cnu_halfborrowed
generate_cnu_halfborrowed(8, to_toffoli=True)
```
```
0: ────────────────────────@───────────────────────────────────────@───────────────────
                           │                                       │
1: ────────────────────────@───────────────────────────────────────@───────────────────
                           │                                       │
2: ────────────────────@───┼───@───────────────────────────────@───┼───@───────────────
                       │   │   │                               │   │   │
3: ────────────────@───┼───┼───┼───@───────────────────────@───┼───┼───┼───@───────────
                   │   │   │   │   │                       │   │   │   │   │
4: ────────────@───┼───┼───┼───┼───┼───@───────────────@───┼───┼───┼───┼───┼───@───────
               │   │   │   │   │   │   │               │   │   │   │   │   │   │
5: ────────@───┼───┼───┼───┼───┼───┼───┼───@───────@───┼───┼───┼───┼───┼───┼───┼───@───
           │   │   │   │   │   │   │   │   │       │   │   │   │   │   │   │   │   │
6: ────@───┼───┼───┼───┼───┼───┼───┼───┼───┼───@───┼───┼───┼───┼───┼───┼───┼───┼───┼───
       │   │   │   │   │   │   │   │   │   │   │   │   │   │   │   │   │   │   │   │
7: ────X───┼───┼───┼───┼───┼───┼───┼───┼───┼───X───┼───┼───┼───┼───┼───┼───┼───┼───┼───
       │   │   │   │   │   │   │   │   │   │   │   │   │   │   │   │   │   │   │   │
8: ────┼───┼───┼───┼───@───X───@───┼───┼───┼───┼───┼───┼───┼───@───X───@───┼───┼───┼───
       │   │   │   │   │       │   │   │   │   │   │   │   │   │       │   │   │   │
9: ────┼───┼───┼───@───X───────X───@───┼───┼───┼───┼───┼───@───X───────X───@───┼───┼───
       │   │   │   │               │   │   │   │   │   │   │               │   │   │
10: ───┼───┼───@───X───────────────X───@───┼───┼───┼───@───X───────────────X───@───┼───
       │   │   │                       │   │   │   │   │                       │   │
11: ───┼───@───X───────────────────────X───@───┼───@───X───────────────────────X───@───
       │   │                               │   │   │                               │
12: ───@───X───────────────────────────────X───@───X───────────────────────────────X───
```
