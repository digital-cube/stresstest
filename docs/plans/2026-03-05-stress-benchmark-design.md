# stress — VM Benchmark Tool Design

## Purpose

A simple Python benchmark tool that measures CPU, memory, and disk performance on a VM. Run it on two identical VMs and compare the results to see which one performs better.

## Architecture

Single Python script (`stress.py`) with three benchmark functions and a main runner.

```
stress.py
├── bench_cpu()       → multi-core math workload, returns ops/sec
├── bench_memory()    → large array read/write, returns MB/s
├── bench_disk()      → sequential + random I/O in temp dir, returns MB/s + IOPS
├── get_system_info() → CPU count, RAM, OS, Python version
└── main()            → runs all benchmarks, prints summary table
```

## CPU Benchmark

- Spawns one worker per CPU core using `multiprocessing`
- Each worker computes N primes via sieve
- Measures wall-clock time for completion
- Reports: total operations/sec, time taken

## Memory Benchmark

- Allocates a large `bytearray` (256MB)
- Sequential write: fill in chunks, measure throughput (MB/s)
- Sequential read: iterate and sum, measure throughput (MB/s)
- Reports: write MB/s, read MB/s

## Disk Benchmark

- Creates a temp directory
- Sequential: write/read a 256MB file in chunks → MB/s
- Random I/O: create and read many small 4KB files → IOPS
- Cleans up temp files after
- Reports: seq write MB/s, seq read MB/s, random IOPS

## Output

Rich terminal table showing system info and all benchmark results. Falls back to plain print if `rich` is not installed.

## Dependencies

- `rich` (terminal table formatting)
- All other functionality uses Python stdlib

## Constraints

- Quick run: ~30 seconds total
- Zero config: just run `python stress.py`
- If disk test fails (permissions), skip and note in output
