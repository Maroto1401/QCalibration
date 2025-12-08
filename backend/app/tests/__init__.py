"""Simple runner to generate a random circuit and save QASM in ./output.

This script is intentionally minimal so you can run it from the
`backend/app/tests` directory with `python3 __init__.py`.

It creates a 4-qubit circuit with depth 10 (default) and writes
`output/circuit.qasm` relative to this file.
"""

import json
from pathlib import Path
import random

try:
	from qiskit import QuantumCircuit
except Exception as e:
	raise RuntimeError("Qiskit is required to run this script. Install it in the backend environment.") from e


def create_random_circuit(num_qubits: int = 4, depth: int = 10, seed: int | None = None) -> QuantumCircuit:
	if seed is not None:
		random.seed(seed)
	qc = QuantumCircuit(num_qubits)
	single_gates = ["h", "x", "y", "z", "rx", "ry", "rz"]
	for _ in range(depth):
		for q in range(num_qubits):
			gate = random.choice(single_gates)
			if gate == "h":
				qc.h(q)
			elif gate == "x":
				qc.x(q)
			elif gate == "y":
				qc.y(q)
			elif gate == "z":
				qc.z(q)
			elif gate == "rx":
				qc.rx(random.uniform(0, 2 * 3.14159), q)
			elif gate == "ry":
				qc.ry(random.uniform(0, 2 * 3.14159), q)
			elif gate == "rz":
				qc.rz(random.uniform(0, 2 * 3.14159), q)
		# add some CXs
		pairs = list(range(num_qubits))
		random.shuffle(pairs)
		num_pairs = random.randint(0, max(1, num_qubits // 2))
		for i in range(num_pairs):
			a = pairs[2 * i]
			b = pairs[2 * i + 1]
			if random.random() < 0.5:
				qc.cx(a, b)
			else:
				qc.cx(b, a)
	return qc


def qc_to_simple_json(qc: QuantumCircuit) -> dict:
	qubit_map = {q: i for i, q in enumerate(qc.qubits)}
	gates = []
	for instr, qargs, cargs in qc.data:
		qubit_indices = [qubit_map.get(q, None) for q in qargs]
		params = []
		for p in instr.params:
			try:
				params.append(float(p))
			except Exception:
				params.append(str(p))
		gates.append({"name": instr.name, "qubits": qubit_indices, "params": params})
	return {"num_qubits": len(qc.qubits), "gates": gates}


def main():
	qc = create_random_circuit(num_qubits=4, depth=10, seed=42)
	base = Path(__file__).parent
	out_dir = base / "output"
	out_dir.mkdir(parents=True, exist_ok=True)

	qasm_path = out_dir / "circuit.qasm"
	json_path = out_dir / "circuit.json"

	# Export to OpenQASM. Some Qiskit installs may not expose QuantumCircuit.qasm().
	def _format_param(p):
		try:
			return str(float(p))
		except Exception:
			return str(p)

	def _export_qasm_fallback(qc):
		# Basic OpenQASM 2.0 exporter for a small subset of gates used in tests.
		lines = ["OPENQASM 2.0;", 'include \"qelib1.inc\";']
		num_q = len(qc.qubits)
		lines.append(f"qreg q[{num_q}];")
		# add classical register only if measurements present
		has_measure = any(instr.name == 'measure' for instr, _, _ in qc.data)
		if has_measure:
			lines.append(f"creg c[{num_q}];")

		qubit_map = {q: i for i, q in enumerate(qc.qubits)}

		for instr, qargs, cargs in qc.data:
			name = instr.name
			q_inds = [qubit_map.get(q) for q in qargs]
			if name in ("h", "x", "y", "z") and len(q_inds) == 1:
				lines.append(f"{name} q[{q_inds[0]}];")
			elif name in ("rx", "ry", "rz") and len(q_inds) == 1:
				param = instr.params[0] if instr.params else 0
				lines.append(f"{name}({ _format_param(param) }) q[{q_inds[0]}];")
			elif name in ("cx", "cx1", "cnot") and len(q_inds) >= 2:
				lines.append(f"cx q[{q_inds[0]}],q[{q_inds[1]}];")
			elif name == "measure" and len(q_inds) == 1:
				# measure q[i] -> c[j]
				# cargs may contain ClassicalRegister bits; fallback map by index
				lines.append(f"measure q[{q_inds[0]}] -> c[{q_inds[0]}];")
			else:
				# unknown gate: attempt generic rendering
				params = ",".join(_format_param(p) for p in instr.params) if instr.params else ""
				qlist = ",".join(f"q[{i}]" for i in q_inds)
				if params:
					lines.append(f"{name}({params}) {qlist};")
				else:
					lines.append(f"{name} {qlist};")

		return "\n".join(lines) + "\n"

	try:
		qasm_text = qc.qasm()
	except AttributeError:
		qasm_text = _export_qasm_fallback(qc)
	with open(qasm_path, "w", encoding="utf-8") as f:
		f.write(qasm_text)

	with open(json_path, "w", encoding="utf-8") as f:
		json.dump(qc_to_simple_json(qc), f, indent=2)

	print("Wrote:", qasm_path)
	print("Wrote:", json_path)


if __name__ == "__main__":
	main()
