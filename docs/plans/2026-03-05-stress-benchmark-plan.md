# stress — VM Benchmark Tool Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a single-script Python benchmark tool that measures CPU, memory, and disk performance so two VMs can be compared.

**Architecture:** One file `stress.py` with pure-function benchmarks for CPU (multiprocessing prime sieve), memory (bytearray throughput), and disk (sequential + random I/O). A `main()` orchestrator runs all three and prints a `rich` table. Falls back to plain print if `rich` is missing.

**Tech Stack:** Python 3.13, stdlib (`multiprocessing`, `time`, `os`, `tempfile`, `shutil`, `platform`, `psutil`-free), `rich` for output.

---

### Task 1: Project scaffold — git init, requirements, and skeleton

**Files:**
- Create: `stress.py`
- Create: `requirements.txt`
- Create: `.gitignore`

**Step 1: Create `.gitignore`**

```
__pycache__/
*.pyc
.venv/
.envrc
```

**Step 2: Create `requirements.txt`**

```
rich
```

**Step 3: Install dependencies**

Run: `pip install -r requirements.txt`

**Step 4: Create `stress.py` skeleton**

```python
#!/usr/bin/env python3
"""stress — simple VM benchmark tool."""

import multiprocessing
import os
import platform
import shutil
import tempfile
import time


def get_system_info():
    """Return dict with system information."""
    mem_bytes = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
    return {
        "hostname": platform.node(),
        "os": f"{platform.system()} {platform.release()}",
        "cpu_count": multiprocessing.cpu_count(),
        "ram_gb": round(mem_bytes / (1024**3), 1),
        "python": platform.python_version(),
    }


def bench_cpu():
    """CPU benchmark — returns dict with results."""
    pass


def bench_memory():
    """Memory benchmark — returns dict with results."""
    pass


def bench_disk():
    """Disk benchmark — returns dict with results."""
    pass


def print_results(info, cpu, memory, disk):
    """Print benchmark results as a formatted table."""
    pass


def main():
    """Run all benchmarks and display results."""
    info = get_system_info()
    print(f"Running stress benchmark on {info['hostname']}...")
    cpu = bench_cpu()
    memory = bench_memory()
    disk = bench_disk()
    print_results(info, cpu, memory, disk)


if __name__ == "__main__":
    main()
```

**Step 5: Verify script runs without error**

Run: `python stress.py`
Expected: Prints "Running stress benchmark on ..." then exits (functions return None for now).

**Step 6: Initialize git and commit**

```bash
git init
git add .gitignore requirements.txt stress.py docs/
git commit -m "feat: project scaffold with benchmark skeleton"
```

---

### Task 2: Implement CPU benchmark

**Files:**
- Modify: `stress.py` — `bench_cpu()` function

**Step 1: Write CPU benchmark test**

Create `test_stress.py`:

```python
"""Tests for stress benchmarks."""

from stress import bench_cpu, get_system_info


def test_get_system_info():
    info = get_system_info()
    assert "hostname" in info
    assert "cpu_count" in info
    assert info["cpu_count"] > 0
    assert info["ram_gb"] > 0


def test_bench_cpu_returns_results():
    result = bench_cpu()
    assert "ops_per_sec" in result
    assert "elapsed_sec" in result
    assert result["ops_per_sec"] > 0
    assert result["elapsed_sec"] > 0
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest test_stress.py -v`
Expected: `test_bench_cpu_returns_results` FAILS (returns None)

**Step 3: Implement `bench_cpu()`**

Replace the `bench_cpu` function in `stress.py`:

```python
def _cpu_worker(_):
    """Compute primes up to N using sieve of Eratosthenes."""
    n = 50_000
    sieve = bytearray([1]) * (n + 1)
    sieve[0] = sieve[1] = 0
    for i in range(2, int(n**0.5) + 1):
        if sieve[i]:
            sieve[i * i : n + 1 : i] = bytearray(len(sieve[i * i : n + 1 : i]))
    return sum(sieve)


def bench_cpu():
    """CPU benchmark — multi-core prime sieve."""
    num_cores = multiprocessing.cpu_count()
    iterations = num_cores * 4  # 4 rounds per core

    start = time.perf_counter()
    with multiprocessing.Pool(num_cores) as pool:
        pool.map(_cpu_worker, range(iterations))
    elapsed = time.perf_counter() - start

    return {
        "ops_per_sec": round(iterations / elapsed, 1),
        "elapsed_sec": round(elapsed, 2),
        "cores_used": num_cores,
    }
```

**Step 4: Run tests to verify they pass**

Run: `python -m pytest test_stress.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add stress.py test_stress.py
git commit -m "feat: implement CPU benchmark (multi-core prime sieve)"
```

---

### Task 3: Implement memory benchmark

**Files:**
- Modify: `stress.py` — `bench_memory()` function
- Modify: `test_stress.py` — add memory tests

**Step 1: Write memory benchmark test**

Add to `test_stress.py`:

```python
from stress import bench_memory


def test_bench_memory_returns_results():
    result = bench_memory()
    assert "write_mb_per_sec" in result
    assert "read_mb_per_sec" in result
    assert result["write_mb_per_sec"] > 0
    assert result["read_mb_per_sec"] > 0
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest test_stress.py::test_bench_memory_returns_results -v`
Expected: FAIL

**Step 3: Implement `bench_memory()`**

Replace in `stress.py`:

```python
def bench_memory():
    """Memory benchmark — sequential write/read throughput."""
    size = 256 * 1024 * 1024  # 256 MB
    chunk = 1024 * 1024  # 1 MB chunks
    buf = bytearray(size)

    # Sequential write
    data = b"\xaa" * chunk
    start = time.perf_counter()
    for offset in range(0, size, chunk):
        buf[offset : offset + chunk] = data
    write_elapsed = time.perf_counter() - start

    # Sequential read
    start = time.perf_counter()
    total = 0
    mv = memoryview(buf)
    for offset in range(0, size, chunk):
        total += sum(mv[offset : offset + chunk])
    read_elapsed = time.perf_counter() - start

    size_mb = size / (1024 * 1024)
    return {
        "write_mb_per_sec": round(size_mb / write_elapsed, 1),
        "read_mb_per_sec": round(size_mb / read_elapsed, 1),
        "size_mb": int(size_mb),
    }
```

**Step 4: Run tests to verify they pass**

Run: `python -m pytest test_stress.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add stress.py test_stress.py
git commit -m "feat: implement memory benchmark (256MB sequential r/w)"
```

---

### Task 4: Implement disk benchmark

**Files:**
- Modify: `stress.py` — `bench_disk()` function
- Modify: `test_stress.py` — add disk tests

**Step 1: Write disk benchmark test**

Add to `test_stress.py`:

```python
from stress import bench_disk


def test_bench_disk_returns_results():
    result = bench_disk()
    assert "seq_write_mb_per_sec" in result
    assert "seq_read_mb_per_sec" in result
    assert "random_iops" in result
    assert result["seq_write_mb_per_sec"] > 0
    assert result["seq_read_mb_per_sec"] > 0
    assert result["random_iops"] > 0
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest test_stress.py::test_bench_disk_returns_results -v`
Expected: FAIL

**Step 3: Implement `bench_disk()`**

Replace in `stress.py`:

```python
def bench_disk():
    """Disk benchmark — sequential and random I/O."""
    tmp_dir = tempfile.mkdtemp(prefix="stress_")
    try:
        file_path = os.path.join(tmp_dir, "benchmark.dat")
        size = 256 * 1024 * 1024  # 256 MB
        chunk = 1024 * 1024  # 1 MB

        # Sequential write
        data = os.urandom(chunk)
        start = time.perf_counter()
        with open(file_path, "wb") as f:
            for _ in range(size // chunk):
                f.write(data)
            f.flush()
            os.fsync(f.fileno())
        seq_write_elapsed = time.perf_counter() - start

        # Sequential read
        start = time.perf_counter()
        with open(file_path, "rb") as f:
            while f.read(chunk):
                pass
        seq_read_elapsed = time.perf_counter() - start

        os.remove(file_path)

        # Random I/O — small files
        num_files = 1000
        small_data = os.urandom(4096)
        start = time.perf_counter()
        for i in range(num_files):
            p = os.path.join(tmp_dir, f"f{i}")
            with open(p, "wb") as f:
                f.write(small_data)
        for i in range(num_files):
            p = os.path.join(tmp_dir, f"f{i}")
            with open(p, "rb") as f:
                f.read()
        random_elapsed = time.perf_counter() - start

        size_mb = size / (1024 * 1024)
        # Total file ops: 1000 writes + 1000 reads = 2000
        total_ops = num_files * 2
        return {
            "seq_write_mb_per_sec": round(size_mb / seq_write_elapsed, 1),
            "seq_read_mb_per_sec": round(size_mb / seq_read_elapsed, 1),
            "random_iops": round(total_ops / random_elapsed, 1),
        }
    except OSError as e:
        return {
            "seq_write_mb_per_sec": 0,
            "seq_read_mb_per_sec": 0,
            "random_iops": 0,
            "error": str(e),
        }
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
```

**Step 4: Run tests to verify they pass**

Run: `python -m pytest test_stress.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add stress.py test_stress.py
git commit -m "feat: implement disk benchmark (seq + random I/O)"
```

---

### Task 5: Implement output formatting with rich

**Files:**
- Modify: `stress.py` — `print_results()` function

**Step 1: Implement `print_results()`**

Replace in `stress.py`:

```python
def print_results(info, cpu, memory, disk):
    """Print benchmark results as a formatted table."""
    try:
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel

        console = Console()

        header = (
            f"[bold]Host:[/] {info['hostname']}  "
            f"[bold]CPUs:[/] {info['cpu_count']}  "
            f"[bold]RAM:[/] {info['ram_gb']} GB  "
            f"[bold]OS:[/] {info['os']}  "
            f"[bold]Python:[/] {info['python']}"
        )
        console.print(Panel(header, title="[bold]stress — VM Benchmark[/]"))

        table = Table(show_header=True, header_style="bold")
        table.add_column("Test", style="cyan", width=14)
        table.add_column("Metric", width=12)
        table.add_column("Result", justify="right", style="green")

        table.add_row("CPU", "ops/sec", f"{cpu['ops_per_sec']:,.1f}")
        table.add_row("CPU", "time (s)", f"{cpu['elapsed_sec']}")
        table.add_row("CPU", "cores", f"{cpu['cores_used']}")
        table.add_row("", "", "")
        table.add_row("Memory Write", "MB/s", f"{memory['write_mb_per_sec']:,.1f}")
        table.add_row("Memory Read", "MB/s", f"{memory['read_mb_per_sec']:,.1f}")
        table.add_row("", "", "")

        if disk.get("error"):
            table.add_row("Disk", "ERROR", disk["error"])
        else:
            table.add_row("Disk Seq W", "MB/s", f"{disk['seq_write_mb_per_sec']:,.1f}")
            table.add_row("Disk Seq R", "MB/s", f"{disk['seq_read_mb_per_sec']:,.1f}")
            table.add_row("Disk Random", "IOPS", f"{disk['random_iops']:,.1f}")

        console.print(table)

    except ImportError:
        # Fallback: plain text
        print(f"\n{'='*45}")
        print(f"  stress — VM Benchmark")
        print(f"  Host: {info['hostname']}  CPUs: {info['cpu_count']}  RAM: {info['ram_gb']} GB")
        print(f"{'='*45}")
        print(f"  {'Test':<14} {'Metric':<12} {'Result':>10}")
        print(f"  {'-'*38}")
        print(f"  {'CPU':<14} {'ops/sec':<12} {cpu['ops_per_sec']:>10,.1f}")
        print(f"  {'CPU':<14} {'time (s)':<12} {cpu['elapsed_sec']:>10}")
        print(f"  {'CPU':<14} {'cores':<12} {cpu['cores_used']:>10}")
        print(f"  {'Mem Write':<14} {'MB/s':<12} {memory['write_mb_per_sec']:>10,.1f}")
        print(f"  {'Mem Read':<14} {'MB/s':<12} {memory['read_mb_per_sec']:>10,.1f}")
        if disk.get("error"):
            print(f"  {'Disk':<14} {'ERROR':<12} {disk['error']}")
        else:
            print(f"  {'Disk Seq W':<14} {'MB/s':<12} {disk['seq_write_mb_per_sec']:>10,.1f}")
            print(f"  {'Disk Seq R':<14} {'MB/s':<12} {disk['seq_read_mb_per_sec']:>10,.1f}")
            print(f"  {'Disk Random':<14} {'IOPS':<12} {disk['random_iops']:>10,.1f}")
        print(f"  {'='*38}\n")
```

**Step 2: Run the full script end-to-end**

Run: `python stress.py`
Expected: See system info panel + results table with real numbers. Should complete in ~30 seconds.

**Step 3: Run all tests**

Run: `python -m pytest test_stress.py -v`
Expected: All PASS

**Step 4: Commit**

```bash
git add stress.py
git commit -m "feat: add rich table output with plain-text fallback"
```

---

### Task 6: Final polish and verification

**Step 1: Run end-to-end on this machine**

Run: `python stress.py`
Expected: Full table with all benchmarks, completes in ~30 seconds.

**Step 2: Test plain-text fallback**

Run: `python -c "import stress; stress.print_results(stress.get_system_info(), {'ops_per_sec':1,'elapsed_sec':1,'cores_used':1}, {'write_mb_per_sec':1,'read_mb_per_sec':1,'size_mb':1}, {'seq_write_mb_per_sec':1,'seq_read_mb_per_sec':1,'random_iops':1})"`
Expected: Should print the table (rich or fallback).

**Step 3: Run full test suite**

Run: `python -m pytest test_stress.py -v`
Expected: All PASS

**Step 4: Final commit**

```bash
git add -A
git commit -m "chore: finalize stress benchmark tool"
```
