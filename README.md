# Simulation Log Parser

EDA Log Analysis & Rule-Based Classification Engine

---

## Overview

This project parses simulation logs and classifies each test run into:

- Infrastructure Crash
- Liveness Failure
- Functional Failure
- Success

It extracts semantic signals from unstructured logs using regular expressions and applies a priority-based rule engine to determine failure intent.

---

## Architecture

### 1. Signal Detection Layer
Uses compiled regex patterns to detect:
- Fatal errors
- Multi-driven nets
- Timing violations
- Simulation completion states
- Explicit run boundaries

### 2. Log Parsing Engine
- Supports explicit and implicit run modes
- Tracks error counts
- Maintains per-run signal states

### 3. Rule Engine
Priority-based classification:

1. Infrastructure Crash
2. Liveness Failure
3. Functional Failure
4. Success

---

## Tech Stack

- Python 3
- Standard Library (re module)

---

## Usage

```bash
python3 log_parser.py
