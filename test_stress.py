"""Tests for stress benchmarks."""

from stress import bench_cpu, bench_disk, bench_memory, bench_network, get_system_info


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


def test_bench_memory_returns_results():
    result = bench_memory()
    assert "write_mb_per_sec" in result
    assert "read_mb_per_sec" in result
    assert result["write_mb_per_sec"] > 0
    assert result["read_mb_per_sec"] > 0


def test_bench_disk_returns_results():
    result = bench_disk()
    assert "seq_write_mb_per_sec" in result
    assert "seq_read_mb_per_sec" in result
    assert "random_iops" in result
    assert result["seq_write_mb_per_sec"] > 0
    assert result["seq_read_mb_per_sec"] > 0
    assert result["random_iops"] > 0


def test_bench_network_returns_results():
    result = bench_network()
    assert "download_mbps" in result
    assert "upload_mbps" in result
    assert "latency_ms" in result
    if "error" not in result:
        assert result["download_mbps"] > 0
        assert result["upload_mbps"] > 0
        assert result["latency_ms"] > 0
