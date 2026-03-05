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
