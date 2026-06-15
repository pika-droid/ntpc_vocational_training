import torch
from ultralytics import YOLO

def main():
    print("PyTorch version:", torch.__version__)
    print("CUDA Available:", torch.cuda.is_available())
    if torch.cuda.is_available():
        print("GPU:", torch.cuda.get_device_name(0))

    # Load the checkpoint (relative to the notebooks directory)
    checkpoint_path = '../runs/detect/ntpc_ppe/stage2_crop_det-2/weights/last.pt'
    print(f"Loading checkpoint from: {checkpoint_path}")
    
    model = YOLO(checkpoint_path)

    # Resume training with 2 workers to avoid Windows deadlock
    print("Starting training resume...")
    model.train(resume=True, workers=2)

if __name__ == '__main__':
    main()
