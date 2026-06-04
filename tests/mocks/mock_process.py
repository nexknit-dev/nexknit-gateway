"""Mock subprocess module for testing"""

from unittest.mock import MagicMock, patch
import subprocess


class MockCompletedProcess:
    """Mock subprocess.CompletedProcess"""
    
    def __init__(self, stdout="", stderr="", returncode=0):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


class MockSubprocessModule:
    """Mock subprocess module"""
    
    def __init__(self):
        self._run_results = {}
        self._run_error = None
    
    def run(self, args, **kwargs):
        """Mock subprocess.run"""
        cmd_key = tuple(args) if isinstance(args, list) else args
        
        if self._run_error:
            raise self._run_error
        
        if cmd_key in self._run_results:
            return self._run_results[cmd_key]
        
        # Default behavior
        return MockCompletedProcess(stdout="", stderr="", returncode=0)
    
    def set_run_result(self, args, stdout="", stderr="", returncode=0):
        """Set expected result for a specific command"""
        cmd_key = tuple(args) if isinstance(args, list) else args
        self._run_results[cmd_key] = MockCompletedProcess(stdout, stderr, returncode)
    
    def set_run_error(self, error):
        """Set error to raise when running commands"""
        self._run_error = error
    
    def reset(self):
        """Reset mock state"""
        self._run_results = {}
        self._run_error = None


def patch_subprocess():
    """Create a patch for subprocess module"""
    mock_module = MockSubprocessModule()
    patcher = patch("subprocess.run", mock_module.run)
    return patcher, mock_module


# Predefined nvidia-smi outputs for testing
NVIDIA_SMI_OUTPUTS = {
    "single_gpu": """NVIDIA-SMI 535.104.05   Driver Version: 535.104.05   CUDA Version: 12.2

+---------------------------------------------------------------------------------------+
| NVIDIA-SMI 535.104.05   Driver Version: 535.104.05   CUDA Version: 12.2                |
|-----------------------------------------+----------------------+----------------------+
| GPU  Name                  Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
| Fan  Temp  Perf            Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |
|                                         |                      |               MIG M. |
|=========================================+======================+======================|
|   0  NVIDIA GeForce RTX 4090         On | 00000000:01:00.0  On |                  N/A |
|  50%   65C    P2              250W / 450W|   8192MiB / 24576MiB |     80%      Default |
+-----------------------------------------+----------------------+----------------------+

+---------------------------------------------------------------------------------------+
| Processes:                                                                            |
|  GPU   GI   CI        PID   Type   Process name                            GPU Memory |
|        ID   ID                                                             Usage      |
|=======================================================================================|
|    0   N/A  N/A      1234      C   python                                   8192MiB |
+---------------------------------------------------------------------------------------+
""",
    "multi_gpu": """NVIDIA-SMI 535.104.05   Driver Version: 535.104.05   CUDA Version: 12.2

+---------------------------------------------------------------------------------------+
| NVIDIA-SMI 535.104.05   Driver Version: 535.104.05   CUDA Version: 12.2                |
|-----------------------------------------+----------------------+----------------------+
| GPU  Name                  Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
| Fan  Temp  Perf            Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |
|                                         |                      |               MIG M. |
|=========================================+======================+======================|
|   0  NVIDIA GeForce RTX 4090         On | 00000000:01:00.0  On |                  N/A |
|  50%   65C    P2              250W / 450W|   8192MiB / 24576MiB |     80%      Default |
|-----------------------------------------+----------------------+----------------------+
|   1  NVIDIA GeForce RTX 3080         On | 00000000:02:00.0 Off |                  N/A |
|  40%   55C    P0              100W / 320W|   4096MiB / 10240MiB |     20%      Default |
+-----------------------------------------+----------------------+----------------------+

+---------------------------------------------------------------------------------------+
| Processes:                                                                            |
|  GPU   GI   CI        PID   Type   Process name                            GPU Memory |
|        ID   ID                                                             Usage      |
|=======================================================================================|
|    0   N/A  N/A      1234      C   python                                   8192MiB |
|    1   N/A  N/A      5678      C   torchrun                                  4096MiB |
+---------------------------------------------------------------------------------------+
""",
    "no_gpu": "NVIDIA-SMI has failed because it couldn't communicate with the NVIDIA driver.",
    "version": "NVIDIA-SMI 535.104.05   Driver Version: 535.104.05   CUDA Version: 12.2"
}
