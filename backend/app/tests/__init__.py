from qiskit import QuantumCircuit, transpile
from qiskit.circuit.library import HGate, TGate, SGate, CXGate

# Hardware-native Marrakesh basis
native_basis = ['cz', 'id', 'rx', 'rz', 'rzz', 'sx', 'x']

# Logical circuit with named gates
logical_circuit = QuantumCircuit(3)
logical_circuit.append(HGate(), [0])
logical_circuit.append(CXGate(), [0, 1])
logical_circuit.append(TGate(), [1])
logical_circuit.append(CXGate(), [1, 2])
logical_circuit.append(SGate(), [2])
logical_circuit.append(HGate(), [1])

# Function to show how each logical gate maps to native gates
def logical_to_native(gate, qubits):
    # Make a tiny circuit with just this gate
    temp_circ = QuantumCircuit(3)
    temp_circ.append(gate, qubits)
    # Transpile to Marrakesh native gates
    temp_transpiled = transpile(temp_circ, basis_gates=native_basis, optimization_level=0)
    # List instructions as names and parameters
    instrs = []
    for instr_obj in temp_transpiled.data:
        g = instr_obj.operation
        qs = [temp_transpiled.qubits.index(q) for q in instr_obj.qubits]
        params = [float(p) for p in g.params] if g.params else []
        instrs.append((g.name, qs, params))
    return instrs

# Iterate over original logical gates
for i, instr_obj in enumerate(logical_circuit.data):
    gate = instr_obj.operation
    qubits = [logical_circuit.qubits.index(q) for q in instr_obj.qubits]
    native_seq = logical_to_native(gate, qubits)
    print(f"{i:02d}: Logical gate {gate.name} on qubits {qubits} → native sequence:")
    for name, qs, params in native_seq:
        print(f"      {name} on {qs} params {params}")
    print("-"*50)
