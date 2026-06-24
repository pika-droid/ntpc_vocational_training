# backend/device_config.py
import torch

def get_optimal_inference_config():
    """
    Analyzes the available CPU/GPU resources and returns optimal inference settings.
    
    Returns:
        dict containing:
            - 'device': str ('cuda', 'mps', or 'cpu')
            - 'half': bool (True if FP16 is supported and recommended, False otherwise)
            - 'gpu_name': str or None
            - 'vram_gb': float or None
            - 'compute_capability': tuple or None
    """
    config = {
        'device': 'cpu',
        'half': False,
        'gpu_name': None,
        'vram_gb': None,
        'compute_capability': None
    }
    
    # 1. Check for CUDA (NVIDIA GPU)
    if torch.cuda.is_available():
        config['device'] = 'cuda'
        try:
            device_idx = 0
            gpu_name = torch.cuda.get_device_name(device_idx)
            config['gpu_name'] = gpu_name
            
            # Get VRAM in GB
            properties = torch.cuda.get_device_properties(device_idx)
            vram_gb = properties.total_memory / (1024 ** 3)
            config['vram_gb'] = round(vram_gb, 2)
            
            # Get Compute Capability
            cap = torch.cuda.get_device_capability(device_idx)
            config['compute_capability'] = cap
            
            # FP16 (half precision) is fully supported and hardware-accelerated (via Tensor Cores)
            # on Volta (7.0), Turing (7.5), Ampere (8.0, 8.6), Ada Lovelace (8.9), Hopper (9.0), etc.
            # On Pascal (6.0, 6.1) or older, FP16 execution can actually be slower than FP32.
            if cap[0] >= 7:
                config['half'] = True
                print(f"[DeviceConfig] Detected NVIDIA GPU: {gpu_name} (Compute Capability {cap[0]}.{cap[1]}, {vram_gb:.2f} GB VRAM).")
                print("[DeviceConfig] Hardware supports native FP16. Enabling FP16 (half=True) optimizations.")
            else:
                config['half'] = False
                print(f"[DeviceConfig] Detected NVIDIA GPU: {gpu_name} (Compute Capability {cap[0]}.{cap[1]} < 7.0, {vram_gb:.2f} GB VRAM).")
                print("[DeviceConfig] Compute Capability is below 7.0. Running in FP32 (half=False) mode for better compatibility and performance.")
        except Exception as e:
            config['half'] = False
            print(f"[DeviceConfig] Error querying GPU properties: {e}. Defaulting to FP32 (half=False).")
            
    # 2. Check for MPS (Apple Silicon) if applicable
    elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        config['device'] = 'mps'
        config['half'] = False  # MPS has mixed support for FP16, FP32 is much safer
        print("[DeviceConfig] Detected Apple Silicon (MPS). Running in FP32 (half=False).")
        
    # 3. Fallback to CPU
    else:
        config['device'] = 'cpu'
        config['half'] = False
        print("[DeviceConfig] No GPU found or CUDA is not available. Running on CPU.")
        print("[DeviceConfig] Disabling FP16 (half=False) to avoid unsupported PyTorch CPU operators.")
        
    return config

if __name__ == '__main__':
    # Print the auto-detected configuration when run directly
    import json
    opt_config = get_optimal_inference_config()
    print("\nOptimal configuration:")
    print(json.dumps(opt_config, indent=2))
