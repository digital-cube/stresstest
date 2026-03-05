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
