


https://github.com/user-attachments/assets/ba1cf45d-0100-4bb3-bafa-757a1b29a2f8



<img width="1920" height="1258" alt="image" src="https://github.com/user-attachments/assets/d984cf84-95dd-4da3-bea8-5becd1c793b1" />

QCal is a hardware-aware quantum circuit optimization and benchmarking platform built with Qiskit and IBM Quantum Runtime.

It enables researchers and industry users to:

- Upload OpenQASM quantum circuits
- Analyze structural properties
- Optimize routing strategies
- Incorporate qubit calibration data
- Benchmark simulator vs hardware performance
- Track performance metrics through a web interface

---

# How QCal Works

## 1️⃣ Upload Circuit

Users upload an OpenQASM2 quantum circuit file.

The system:
- Loads the circuit
- Prepares it for analysis and execution

---

## 2️⃣ Analyze

The circuit is analyzed to extract:

- Circuit depth
- Gate count
- Two-qubit gate usage
- Logical qubit layout

This establishes a logical reference before hardware mapping.

---

## 3️⃣ Select Hardware

Users select an IBM Quantum backend.

QCal retrieves:

- Backend topology
- Native gate set
- Calibration properties
- Coupling map

This enables hardware-aware transpilation.

---

## 4️⃣ Transpile

Routing and mapping strategies are applied:

- Naive mapping
- SABRE
- Dynamic routing
- Calibration-aware mapping

Logical-to-physical qubit embeddings are automated.

---

## 5️⃣ Optimize & Benchmark

Each candidate circuit is validated and benchmarked using:

- Unitary equivalence checks
- Statevector probability comparison
- Classical fidelity computation
- Hardware execution via IBM Runtime Sampler
- Depth and gate count tracking
- Runtime measurement

Only logically equivalent circuits proceed to hardware benchmarking. This checks can be found under QCalibrate/backend/app/tests/ . You should set up your IBM_runtime account and upload your circuits. 

---

## 6️⃣ Export

Results are exported as structured CSV files containing:

- Circuit name
- Optimization level
- Circuit depth
- Gate count
- Classical fidelity
- Wall-clock runtime
- Backend runtime (if available)

Optimized circuits can also be exported as OpenQASM2 files.

---

# Architecture

QCal consists of:

- **Frontend:** React + TypeScript + Chakra UI  
- **Backend:** FastAPI (Python)  
- **Quantum Engine:** Qiskit + IBM Quantum Runtime  
- **Data Output:** CSV-based benchmarking reports  
---

# Installation
---

# Prerequisites

- Python 3.12+
- Node.js 18+
- Git
- IBM Quantum account (for hardware execution only)

---
## 1️⃣ Clone the Repository

```bash
git clone https://github.com/Maroto1401/QCalibration.git
cd QCalibration
```

---

## 2️⃣ Backend Setup (FastAPI)

### Create a Virtual Environment

```bash
python3 -m venv venv
```

### Activate the Virtual Environment

macOS / Linux:
```bash
source venv/bin/activate
```

Windows:
```bash
venv\Scripts\activate
```

### Install Backend Dependencies

```bash
pip install --upgrade pip
pip install -r backend/requirements.txt
```
---

## 3️⃣ Frontend Setup (React + TypeScript + Mantine UI)

Navigate to the frontend directory:

```bash
cd frontend
```

Install frontend dependencies:

```bash
npm install
```
```bash
npm start
```

---

## Installation Complete

You are now ready to run the backend and frontend servers.
Refer to the "Running the Application" section for execution instructions.

