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
