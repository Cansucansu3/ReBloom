DEFAULT_MODEL_NAME = "ViT-B/32"


def get_device():
    import torch

    return "cuda" if torch.cuda.is_available() else "cpu"


def load_clip_model(model_name=DEFAULT_MODEL_NAME, device=None):
    try:
        import clip
    except ImportError as exc:
        raise RuntimeError(
            "CLIP is not installed. Install ai_service/requirements.txt first."
        ) from exc

    device = device or get_device()
    model, preprocess = clip.load(model_name, device=device)
    model.eval()
    return model, preprocess, device
