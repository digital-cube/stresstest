#!/usr/bin/env python3
"""stress — simple VM benchmark tool."""

import multiprocessing
import os
import platform
import shutil
import tempfile
import time
import urllib.request
import urllib.error


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


def bench_network():
    """Network benchmark — download/upload speed and latency via Cloudflare."""
    base_url = "https://speed.cloudflare.com"
    headers = {"User-Agent": "stress-bench/1.0"}
    try:
        # Latency — time to first byte on a tiny request
        req = urllib.request.Request(
            f"{base_url}/__down?bytes=1", headers=headers
        )
        start = time.perf_counter()
        urllib.request.urlopen(req, timeout=10)
        latency = (time.perf_counter() - start) * 1000  # ms

        # Download — fetch 10 MB
        down_bytes = 10 * 1024 * 1024
        req = urllib.request.Request(
            f"{base_url}/__down?bytes={down_bytes}", headers=headers
        )
        start = time.perf_counter()
        resp = urllib.request.urlopen(req, timeout=30)
        _ = resp.read()
        down_elapsed = time.perf_counter() - start
        down_mbps = (down_bytes * 8) / (down_elapsed * 1_000_000)

        # Upload — send 5 MB
        up_bytes = 5 * 1024 * 1024
        payload = os.urandom(up_bytes)
        req = urllib.request.Request(
            f"{base_url}/__up",
            data=payload,
            headers={**headers, "Content-Type": "application/octet-stream"},
        )
        start = time.perf_counter()
        urllib.request.urlopen(req, timeout=30)
        up_elapsed = time.perf_counter() - start
        up_mbps = (up_bytes * 8) / (up_elapsed * 1_000_000)

        return {
            "latency_ms": round(latency, 1),
            "download_mbps": round(down_mbps, 1),
            "upload_mbps": round(up_mbps, 1),
        }
    except (urllib.error.URLError, OSError) as e:
        return {
            "latency_ms": 0,
            "download_mbps": 0,
            "upload_mbps": 0,
            "error": str(e),
        }


def print_results(info, cpu, memory, disk, network):
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

        table.add_row("", "", "")
        if network.get("error"):
            table.add_row("Network", "ERROR", network["error"])
        else:
            table.add_row("Net Download", "Mbps", f"{network['download_mbps']:,.1f}")
            table.add_row("Net Upload", "Mbps", f"{network['upload_mbps']:,.1f}")
            table.add_row("Net Latency", "ms", f"{network['latency_ms']:,.1f}")

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
        if network.get("error"):
            print(f"  {'Network':<14} {'ERROR':<12} {network['error']}")
        else:
            print(f"  {'Net Download':<14} {'Mbps':<12} {network['download_mbps']:>10,.1f}")
            print(f"  {'Net Upload':<14} {'Mbps':<12} {network['upload_mbps']:>10,.1f}")
            print(f"  {'Net Latency':<14} {'ms':<12} {network['latency_ms']:>10,.1f}")
        print(f"  {'='*38}\n")


def main():
    """Run all benchmarks and display results."""
    info = get_system_info()
    print(f"Running stress benchmark on {info['hostname']}...")
    cpu = bench_cpu()
    memory = bench_memory()
    disk = bench_disk()
    network = bench_network()
    print_results(info, cpu, memory, disk, network)


if __name__ == "__main__":
    main()
