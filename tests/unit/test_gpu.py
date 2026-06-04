"""Unit tests for GPUCollector"""

import pytest
from unittest.mock import patch, MagicMock
from collectors.gpu import GPUCollector
from tests.mocks.mock_process import NVIDIA_SMI_OUTPUTS


class TestGPUCollector:
    """Test GPUCollector functionality"""
    
    def test_nvidia_smi_detection(self):
        """Test NVIDIA GPU detection"""
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = NVIDIA_SMI_OUTPUTS["version"]
            mock_run.return_value = mock_result
            
            collector = GPUCollector()
            assert collector._has_nvidia_smi is True
    
    def test_nvidia_smi_not_available(self):
        """Test behavior when NVIDIA GPU is not available"""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("nvidia-smi not found")
            
            collector = GPUCollector()
            assert collector._has_nvidia_smi is False
    
    def test_collect_no_gpu(self):
        """Test collect when no GPU is available"""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("nvidia-smi not found")
            
            collector = GPUCollector()
            result = collector.collect()
            
            assert "gpu_status" in result
            assert "GPU Unavailable" in result["gpu_status"]
    
    def test_collect_single_gpu(self):
        """Test collect with single GPU"""
        with patch("subprocess.run") as mock_run:
            # First call: check nvidia-smi version
            def mock_run_side_effect(args, **kwargs):
                if args == ["nvidia-smi", "--version"]:
                    result = MagicMock()
                    result.returncode = 0
                    result.stdout = NVIDIA_SMI_OUTPUTS["version"]
                    return result
                elif "--query-gpu=" in " ".join(args):
                    result = MagicMock()
                    result.returncode = 0
                    result.stdout = "0, NVIDIA GeForce RTX 4090, 8192, 24576, 80, 65"
                    return result
                return MagicMock(returncode=0, stdout="")
            
            mock_run.side_effect = mock_run_side_effect
            
            collector = GPUCollector()
            result = collector.collect()
            
            assert "gpu_0_status" in result
            status = result["gpu_0_status"]
            assert "NVIDIA GeForce RTX 4090" in status
            assert "Mem:" in status
            assert "Util:" in status
            assert "Temp:" in status
    
    def test_collect_multiple_gpus(self):
        """Test collect with multiple GPUs"""
        with patch("subprocess.run") as mock_run:
            def mock_run_side_effect(args, **kwargs):
                if args == ["nvidia-smi", "--version"]:
                    result = MagicMock()
                    result.returncode = 0
                    result.stdout = NVIDIA_SMI_OUTPUTS["version"]
                    return result
                elif "--query-gpu=" in " ".join(args):
                    result = MagicMock()
                    result.returncode = 0
                    result.stdout = "0, NVIDIA GeForce RTX 4090, 8192, 24576, 80, 65\n1, NVIDIA GeForce RTX 3080, 4096, 10240, 20, 55"
                    return result
                return MagicMock(returncode=0, stdout="")
            
            mock_run.side_effect = mock_run_side_effect
            
            collector = GPUCollector()
            result = collector.collect()
            
            assert "gpu_0_status" in result
            assert "gpu_1_status" in result
    
    def test_get_gpu_info(self):
        """Test GPU info retrieval"""
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = NVIDIA_SMI_OUTPUTS["version"]
            mock_run.return_value = mock_result
            
            def mock_run_side_effect(args, **kwargs):
                if args == ["nvidia-smi", "--version"]:
                    return mock_result
                elif "--query-gpu=" in " ".join(args):
                    result = MagicMock()
                    result.returncode = 0
                    result.stdout = "0, NVIDIA GeForce RTX 4090, 8192, 24576, 80, 65"
                    return result
                return mock_result
            
            mock_run.side_effect = mock_run_side_effect
            
            collector = GPUCollector()
            gpus = collector._get_gpu_info()
            
            assert len(gpus) == 1
            assert gpus[0]["index"] == 0
            assert gpus[0]["name"] == "NVIDIA GeForce RTX 4090"
            assert gpus[0]["mem_used"] == 8192
            assert gpus[0]["mem_total"] == 24576
            assert gpus[0]["utilization"] == 80
            assert gpus[0]["temperature"] == 65
    
    def test_process_monitoring(self):
        """Test process monitoring"""
        with patch("subprocess.run") as mock_run:
            def mock_run_side_effect(args, **kwargs):
                if args == ["nvidia-smi", "--version"]:
                    result = MagicMock()
                    result.returncode = 0
                    result.stdout = NVIDIA_SMI_OUTPUTS["version"]
                    return result
                elif "--query-compute-apps=" in " ".join(args):
                    result = MagicMock()
                    result.returncode = 0
                    result.stdout = "1234, python, 8192"
                    return result
                return MagicMock(returncode=0, stdout="")
            
            mock_run.side_effect = mock_run_side_effect
            
            collector = GPUCollector()
            processes = collector._get_gpu_processes()
            
            assert len(processes) == 1
            assert processes[0]["pid"] == 1234
            assert processes[0]["name"] == "python"
