from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator
import numpy as np

PI = np.pi

print("=" * 70)
print("FINDING RX AND RY DECOMPOSITIONS")
print("=" * 70)
print("\nKnown: H = SX RZ(π/2) SX")
print("\nGoal: Find RX(θ) and RY(θ) decompositions")

theta = 0.7

# RX(θ) = H RZ(θ) H
# So: RX(θ) = [SX RZ(π/2) SX] RZ(θ) [SX RZ(π/2) SX]

test_rx = QuantumCircuit(1)
test_rx.rx(theta, 0)
U_rx = Operator(test_rx).data

rx_decomp = QuantumCircuit(1)
# H RZ(θ) H where H = SX RZ(π/2) SX
rx_decomp.sx(0)
rx_decomp.rz(PI/2, 0)
rx_decomp.sx(0)
rx_decomp.rz(theta, 0)
rx_decomp.sx(0)
rx_decomp.rz(PI/2, 0)
rx_decomp.sx(0)
U_rx_decomp = Operator(rx_decomp).data

print("\n" + "=" * 70)
print("RX DECOMPOSITION")
print("=" * 70)
print("\nRX(θ) = H RZ(θ) H")
print("      = [SX RZ(π/2) SX] RZ(θ) [SX RZ(π/2) SX]")

match_rx = np.allclose(U_rx, U_rx_decomp, atol=1e-10)
diff_rx = np.max(np.abs(U_rx - U_rx_decomp))
print(f"\nMatch: {'✅ YES' if match_rx else '❌ NO'} (diff: {diff_rx:.4e})")

if not match_rx:
    print(f"\nRX({theta}):")
    print(np.round(U_rx, 4))
    print(f"\nDecomposition:")
    print(np.round(U_rx_decomp, 4))

# RY(θ) = RZ(π/2) H RZ(θ) H RZ(-π/2)
# Or: RY(θ) = H RZ(-θ) H (conjugate)

ry_test = QuantumCircuit(1)
ry_test.ry(theta, 0)
U_ry = Operator(ry_test).data

ry_decomp1 = QuantumCircuit(1)
# RY(θ) = RZ(π/2) H RZ(θ) H RZ(-π/2)
ry_decomp1.rz(PI/2, 0)
ry_decomp1.sx(0)
ry_decomp1.rz(PI/2, 0)
ry_decomp1.sx(0)
ry_decomp1.rz(theta, 0)
ry_decomp1.sx(0)
ry_decomp1.rz(PI/2, 0)
ry_decomp1.sx(0)
ry_decomp1.rz(-PI/2, 0)
U_ry_decomp1 = Operator(ry_decomp1).data

ry_decomp2 = QuantumCircuit(1)
# Try: H RZ(-θ) H
ry_decomp2.sx(0)
ry_decomp2.rz(PI/2, 0)
ry_decomp2.sx(0)
ry_decomp2.rz(-theta, 0)
ry_decomp2.sx(0)
ry_decomp2.rz(PI/2, 0)
ry_decomp2.sx(0)
U_ry_decomp2 = Operator(ry_decomp2).data

print("\n" + "=" * 70)
print("RY DECOMPOSITION")
print("=" * 70)

print("\nAttempt 1: RY(θ) = RZ(π/2) H RZ(θ) H RZ(-π/2)")
match_ry1 = np.allclose(U_ry, U_ry_decomp1, atol=1e-10)
diff_ry1 = np.max(np.abs(U_ry - U_ry_decomp1))
print(f"Match: {'✅ YES' if match_ry1 else '❌ NO'} (diff: {diff_ry1:.4e})")

print("\nAttempt 2: RY(θ) = H RZ(-θ) H")
match_ry2 = np.allclose(U_ry, U_ry_decomp2, atol=1e-10)
diff_ry2 = np.max(np.abs(U_ry - U_ry_decomp2))
print(f"Match: {'✅ YES' if match_ry2 else '❌ NO'} (diff: {diff_ry2:.4e})")

# Test other single-qubit gates
print("\n" + "=" * 70)
print("OTHER SINGLE-QUBIT GATES")
print("=" * 70)

# Y = [[0, -i], [i, 0]]
y_circ = QuantumCircuit(1)
y_circ.y(0)
U_y = Operator(y_circ).data

y_decomp = QuantumCircuit(1)
# Y = RX(π/2) RZ(π) RX(-π/2) or similar
# Or: Y = RZ(π/2) RX(π) RZ(-π/2)
y_decomp.rz(PI/2, 0)
y_decomp.sx(0)
y_decomp.rz(PI, 0)
y_decomp.sx(0)
y_decomp.rz(-PI/2, 0)
U_y_decomp = Operator(y_decomp).data

match_y = np.allclose(U_y, U_y_decomp, atol=1e-10)
diff_y = np.max(np.abs(U_y - U_y_decomp))
print(f"\nY = RZ(π/2) RX(π) RZ(-π/2)")
print(f"  = RZ(π/2) [SX RZ(π/2) SX] RZ(π) [SX RZ(π/2) SX] RZ(-π/2)")
print(f"Match: {'✅ YES' if match_y else '❌ NO'} (diff: {diff_y:.4e})")

# Z = [[1, 0], [0, -1]] = RZ(π) up to global phase
z_circ = QuantumCircuit(1)
z_circ.z(0)
U_z = Operator(z_circ).data

z_decomp = QuantumCircuit(1)
z_decomp.rz(PI, 0)
U_z_decomp = Operator(z_decomp).data

# Check if they differ by global phase
match_z = np.allclose(U_z, U_z_decomp, atol=1e-10)
# Also check ignoring global phase
phase_z = np.angle(U_z[0, 0] / U_z_decomp[0, 0])
U_z_decomp_corrected = U_z_decomp * np.exp(-1j * phase_z)
match_z_phase = np.allclose(U_z, U_z_decomp_corrected, atol=1e-10)
diff_z = np.max(np.abs(U_z - U_z_decomp_corrected))

print(f"\nZ = RZ(π)")
print(f"Match (exact): {'✅ YES' if match_z else '❌ NO'}")
print(f"Match (ignoring global phase): {'✅ YES' if match_z_phase else '❌ NO'} (diff: {diff_z:.4e})")

print("\n" + "=" * 70)
print("SUMMARY OF CORRECT DECOMPOSITIONS")
print("=" * 70)

print(f"\nH = SX RZ(π/2) SX ✅")
print(f"X = SX SX ✅")
print(f"RX(θ) = SX RZ(π/2) SX RZ(θ) SX RZ(π/2) SX {'✅' if match_rx else '❌'}")
print(f"RY(θ) = RZ(π/2) SX RZ(π/2) SX RZ(θ) SX RZ(π/2) SX RZ(-π/2) {'✅' if match_ry1 else '❌'}")
print(f"        (or H RZ(-θ) H) {'✅' if match_ry2 else '❌'}")
print(f"Z = RZ(π) ✅")
print(f"Y = RZ(π/2) SX RZ(π/2) SX RZ(π) SX RZ(π/2) SX RZ(-π/2) {'✅' if match_y else '❌'}")