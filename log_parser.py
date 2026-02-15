import re

# -------------------------
# 1. SIGNAL DEFINITIONS
# -------------------------

SIGNAL_PATTERNS = {
    "START_SIMULATION": re.compile(r"(starting|running)\s+simulation", re.IGNORECASE),
    "RUN_START": re.compile(r"running\s+test\s*:", re.IGNORECASE),
    "ERROR_LINE": re.compile(r"^\s*error\b", re.IGNORECASE),
    "FATAL_LINE": re.compile(r"\bfatal\b|\bsegmentation\s+fault\b", re.IGNORECASE),
    "COMPLETE_SUCCESS": re.compile(r"completed\s+successfully", re.IGNORECASE),
    "COMPLETE_ERROR": re.compile(r"completed\s+with\s+errors", re.IGNORECASE),
    "MULTI_DRIVEN_NET": re.compile(r"\b(multi[-\s]?driven\s+net|multiple\s+drivers|more\s+than\s+one\s+driver)\b", re.IGNORECASE),
    "TIMING_VIOLATION": re.compile(r"(setup|hold)\s+violation", re.IGNORECASE),
}

# def detect_signal(line):
#     signals = []
#     for name, pat in SIGNAL_PATTERNS.items():
#         if pat.search(line):
#             signals.append(name)
#     return signals

# Above function can also be written using list comprehension:
def detect_signals(line):
    return [name for name, pat in SIGNAL_PATTERNS.items() if pat.search(line)]


# -------------------------
# 2. RUN OBJECT
# -------------------------

def new_run(run_id):
    return {
        "run_id": run_id,
        "signals": set(),
        "error_count": 0,
        "multi_driven_count": 0
    }


# -------------------------
# 3. PARSER (FACT COLLECTION)
# -------------------------

def parse_log(file_path):
    with open(file_path, "r") as f:
        lines = list(f)

    # Phase 0: Detect whether log has explicit test runs
    has_explicit_runs = any("RUN_START" in detect_signals(line) for line in lines)

    runs = []
    current_run = None
    run_id = 0

    for line in lines:
        signals = detect_signals(line)

        # Ignore pure simulation start noise
        if "START_SIMULATION" in signals and "RUN_START" not in signals:
            continue

        # -------- Explicit RUN boundary --------
        if "RUN_START" in signals:
            if current_run:
                runs.append(current_run)
            run_id += 1
            current_run = new_run(run_id)
            current_run["signals"].add("RUN_START")
            continue

        # -------- Implicit single-run mode --------
        if not has_explicit_runs:
            if not current_run:
                run_id += 1
                current_run = new_run(run_id)

        # If we are in explicit-run mode and no run started yet, ignore preamble
        if has_explicit_runs and not current_run:
            continue

        # -------- Collect semantic facts --------
        for sig in signals:
            current_run["signals"].add(sig)

            if sig == "ERROR_LINE":
                current_run["error_count"] += 1

            if sig == "MULTI_DRIVEN_NET":
                current_run["multi_driven_count"] += 1

    if current_run:
        runs.append(current_run)

    return runs


# -------------------------
# 4. RULE ENGINE (INTENT)
# -------------------------

# Priority: Infrastructure > Liveness > Functional > Success
RULES = [
    # Infrastructure crash
    (lambda s, e, m: "FATAL_LINE" in s, "INFRASTRUCTURE_CRASH"),

    # Liveness failure (started but no completion, no fatal)
    (lambda s, e, m: "COMPLETE_SUCCESS" not in s and
                     "COMPLETE_ERROR" not in s and
                     "FATAL_LINE" not in s,
     "LIVENESS_FAILURE"),

    # Functional failure
    (lambda s, e, m: "COMPLETE_ERROR" in s or
                     ("COMPLETE_SUCCESS" in s and e > 0) or
                     m > 0,
     "FUNCTIONAL_FAILURE"),

    # Success
    (lambda s, e, m: "COMPLETE_SUCCESS" in s and e == 0 and m == 0,
     "SUCCESS"),
]

def classify_run(run):
    s = run["signals"]
    e = run["error_count"]
    m = run["multi_driven_count"]

    for condition, outcome in RULES:
        if condition(s, e, m):
            return outcome
    return "UNKNOWN"


# -------------------------
# 5. DRIVER
# -------------------------

def main():
    runs = parse_log("log file")

    for r in runs:
        outcome = classify_run(r)
        print(
            f"Run {r['run_id']} | "
            f"Outcome: {outcome} | "
            f"Errors: {r['error_count']} | "
            f"Multi-driven nets: {r['multi_driven_count']} | "
            f"Signals: {sorted(r['signals'])}"
        )

if __name__ == "__main__":
    main()

# NOTE: Completion detection currently limited to known Vivado phrases
