import torch
if torch.backends.mps.is_available():
    device = torch.device("mps")
    print("Metal GPU is available.")
else:
    device = torch.device("cpu")
    print("Metal GPU not available, using CPU.")