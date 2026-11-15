# SDSMCLF v1.0 — Secure Direct Smart Meter Credit Loading Framework

**Proof-of-Concept Prototype & Empirical Simulation Suite**  
**Author:** Wales Benjamin Nwelih (`2025/B/MIT/0839`)  
**Programme:** Master of Information Technology (Cybersecurity Specialisation), MIVA Open University  
**Supervisor:** Dr. Gbenga Atanda  
**Case Study:** Ibadan Electricity Distribution Company (IBEDC), Nigeria  

---

## Overview

This repository houses the proof-of-concept simulation prototype and automated empirical evaluation suite for the **Secure Direct Smart Meter Credit Loading Framework (SDSMCLF v1.0)**.

While Nigerian electricity consumers can purchase prepaid electricity via mobile banking and digital payment channels, credit activation still relies on manually typing 20-digit Standard Transfer Specification (STS) tokens into physical meters. **SDSMCLF v1.0** eliminates this manual last-mile bottleneck by introducing a **five-layer, zero-trust API reference architecture and IT governance model** that connects payment gateways, utility billing platforms, and registered smart meters.

---

## Key Architectural & Security Features

* **RESTful Credit Orchestration (`POST /api/v1/smart-meter/load-credit`):** Automates end-to-end credit delivery immediately upon payment gateway confirmation.
* **JWT / OAuth 2.0 Bearer Authentication (`HS256`):** Blocks unauthenticated or expired requests at the API Gateway boundary (`401 Unauthorized`).
* **Transaction Idempotency Lock:** Tracks processed `transactionID` values to prevent duplicate replay crediting (`409 Conflict`).
* **Customer-to-Meter Ownership Binding:** Validates active customer status, meter registration, and account linkage prior to credit dispatch (`403 Forbidden` / `404 Not Found`).
* **Immutable Audit Logging & CSV Export:** Records every transaction attempt, validation check, outcome, and execution latency in milliseconds.

---

## Repository Structure

```text
MIT8212-Simu/
├── app.py                  # Flask REST API, JWT middleware, validation engine & meter simulator
├── test_sdsmclf.py         # Automated 100-request functional, security & latency benchmark suite
├── index.html              # Interactive seminar presentation dashboard with live CSV audit export
├── requirements.txt        # Python package dependencies
└── README.md               # Project documentation and setup instructions
```

---

## Setup & Installation

### 1. Prerequisites
* Python 3.10 or higher
* `pip` package manager

### 2. Clone the Repository & Install Dependencies
```bash
git clone https://github.com
cd MIT8212-Simu
pip install Flask PyJWT
```

*(Alternatively, create a `requirements.txt` containing `Flask>=3.0.0` and `PyJWT>=2.8.0`, then run `pip install -r requirements.txt`.)*

---

## Running the Prototype & Empirical Benchmarks

### 1. Run the Automated 100-Request Evaluation Suite
Execute `test_sdsmclf.py` to reproduce the empirical functional, security, and latency results reported in **Chapter 4 (Tables 32A & 32B)**:

```bash
python test_sdsmclf.py
```

**Test Workload Breakdown ($N = 100$ Requests):**
* **TC-01 (70 requests):** Valid JWT, confirmed payment, active registered meter (`SM4509876`) $\rightarrow$ `200 OK`
* **TC-02 (8 requests):** Unregistered `meterID` (`SM0000000`) $\rightarrow$ `404 Not Found`
* **TC-03 (8 requests):** Duplicate `transactionID` replay attack $\rightarrow$ `409 Conflict`
* **TC-04 (7 requests):** Missing or expired JWT Bearer token $\rightarrow$ `401 Unauthorized`
* **TC-05 (7 requests):** Unconfirmed payment (`paymentStatus: "PENDING"`) $\rightarrow$ `400 Bad Request`

### 2. Start the Live API Server
```bash
python app.py
```
The API server starts on `http://127.0.0.1:5000`.

### 3. Launch the Interactive Seminar Dashboard
Open `index.html` in any modern web browser to execute interactive simulated top-up transactions, inspect step-by-step security handshakes, and export audit logs to `.csv`.

---

## Sample API Request & Response

### Request
```http
POST /api/v1/smart-meter/load-credit HTTP/1.1
Host: 127.0.0.1:5000
Authorization: Bearer <VALID_HS256_JWT_TOKEN>
Content-Type: application/json

{
  "transactionID": "TXN900123",
  "customerID": "IB001245",
  "meterID": "SM4509876",
  "amount": 5000,
  "paymentStatus": "CONFIRMED"
}
```

### Response (`200 OK`)
```json
{
  "status": "SUCCESS",
  "message": "Electricity credit loaded successfully",
  "transactionID": "TXN900123",
  "meterID": "SM4509876",
  "newBalance": 6200.0,
  "processingLatencyMs": 1.42,
  "timestamp": "2026-11-15T21:00:00+00:00"
}
```

---

## Disclaimer
This software is an academic proof-of-concept developed for the Master of Information Technology (MIT) degree at MIVA Open University. It simulates payment gateway callbacks and smart meter memory states in a controlled environment and is not connected to live IBEDC production infrastructure.
