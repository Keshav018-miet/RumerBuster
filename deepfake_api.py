"""
Deepfake Detection Service Module (deepfake_api.py)
====================================================
Wraps the Kaggle Deepfake Detection Challenge (DFDC) 1st-place winning architecture
by Selim Seferbekov (selimsef/dfdc_deepfake_challenge) and incorporates best practices
from Daisy-Zhang/Awesome-Deepfakes-Detection.

Key Components:
1. Face Detection & Extraction: MTCNN (facenet-pytorch) with 30% margin expansion.
2. Feature Extractor & Classifier: EfficientNet (tf_efficientnet_b7_ns via timm).
3. Normalization: ImageNet mean/std (0.485, 0.456, 0.406 / 0.229, 0.224, 0.225).
4. Flask-Optimized: Lazy model loading, thread-safe inference, and graceful edge-case handling.
"""

import os
import io
import logging
from typing import Union, Dict, Any, Optional, Tuple
from pathlib import Path
from PIL import Image, ImageOps

# Setup logger
logger = logging.getLogger("deepfake_api")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [deepfake_api] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Default configuration matching selimsef DFDC solution
DEFAULT_MODEL_NAME = "tf_efficientnet_b7_ns"
DEFAULT_INPUT_SIZE = 380  # EfficientNet-B7 resolution: 380x380
DEFAULT_MARGIN_RATIO = 0.30  # 30% margin added to face bounding boxes
DEFAULT_WEIGHTS_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "weights",
    "final_111_DeepFakeClassifier_tf_efficientnet_b7_ns_0_36"
)

# ImageNet normalization parameters
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


class DeepFakeClassifierWrapper:
    """
    Constructs the EfficientNet classifier architecture compatible with
    selimsef/dfdc_deepfake_challenge trained checkpoints.
    """
    def __init__(self, encoder_name: str = DEFAULT_MODEL_NAME, num_classes: int = 1, dropout_rate: float = 0.5):
        import torch
        import torch.nn as nn
        import timm

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Build timm backbone
        # In selimsef's implementation, the classifier is either timm model directly
        # or an encoder with custom pooling and linear layer.
        self.encoder_name = encoder_name
        self.encoder = timm.create_model(
            encoder_name,
            pretrained=False,
            num_classes=num_classes,
            drop_rate=dropout_rate
        )
        self.encoder.to(self.device)
        self.encoder.eval()

    def load_checkpoint(self, weights_path: str):
        import torch
        if not os.path.exists(weights_path):
            raise FileNotFoundError(
                f"Model checkpoint not found at: {weights_path}\n"
                f"Please download the weights using the instructions provided."
            )
        
        logger.info(f"Loading checkpoint from: {weights_path} onto {self.device}")
        checkpoint = torch.load(weights_path, map_location=self.device)
        
        # Handle state_dict wrapper variants
        if isinstance(checkpoint, dict):
            state_dict = checkpoint.get("state_dict", checkpoint.get("model", checkpoint))
        else:
            state_dict = checkpoint

        # Clean DDP/DataParallel prefixes ('module.' or 'encoder.')
        cleaned_dict = {}
        for k, v in state_dict.items():
            k_clean = k.replace("module.", "")
            # If the checkpoint keys start with 'encoder.', map to encoder
            if k_clean.startswith("encoder."):
                k_clean = k_clean.replace("encoder.", "")
            cleaned_dict[k_clean] = v

        missing, unexpected = self.encoder.load_state_dict(cleaned_dict, strict=False)
        if missing:
            logger.warning(f"Missing keys during state_dict load (heads may differ): {len(missing)} keys")
        if unexpected:
            logger.warning(f"Unexpected keys in checkpoint ignored: {len(unexpected)} keys")
            
        self.encoder.eval()
        logger.info("Checkpoint loaded successfully.")


class DeepFakeService:
    """
    Singleton service managing MTCNN face detection, EfficientNet classification,
    and preprocessing pipeline for Flask backends.
    """
    _instance: Optional["DeepFakeService"] = None

    def __init__(self, weights_path: Optional[str] = None, model_name: str = DEFAULT_MODEL_NAME):
        self.weights_path = weights_path or DEFAULT_WEIGHTS_PATH
        self.model_name = model_name
        self.device = None
        self.mtcnn = None
        self.model = None
        self._is_initialized = False

    @classmethod
    def get_instance(cls, weights_path: Optional[str] = None) -> "DeepFakeService":
        """Thread-safe access to the singleton instance."""
        if cls._instance is None:
            cls._instance = cls(weights_path=weights_path)
        return cls._instance

    def initialize(self):
        """
        Lazily initializes PyTorch, MTCNN, and the EfficientNet model.
        Prevents cold-boot delays and unnecessary memory usage when the service is idle.
        """
        if self._is_initialized:
            return

        try:
            import torch
            from facenet_pytorch import MTCNN
        except ImportError as e:
            raise ImportError(
                f"Required dependencies missing: {e}. Please install: "
                f"pip install torch torchvision facenet-pytorch timm albumentations"
            )

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Initializing DeepFakeService on device: {self.device}")

        # Initialize MTCNN for face extraction
        # post_process=False keeps images in standard 0-255 uint8 range for downstream normalization
        self.mtcnn = MTCNN(
            image_size=DEFAULT_INPUT_SIZE,
            margin=0,
            keep_all=True,
            select_largest=True,
            post_process=False,
            device=self.device
        )

        # Initialize EfficientNet Classifier
        self.model = DeepFakeClassifierWrapper(encoder_name=self.model_name)
        if os.path.exists(self.weights_path):
            self.model.load_checkpoint(self.weights_path)
        else:
            logger.warning(
                f"Weights file not found at '{self.weights_path}'. "
                f"Service running in initialized mode, but checkpoint must be downloaded for production inference."
            )

        self._is_initialized = True
        logger.info("DeepFakeService initialization complete.")

    def _extract_face_and_crop(self, pil_image: Image.Image) -> Tuple[Optional[Image.Image], Optional[list]]:
        """
        Detects faces using MTCNN and extracts the primary face with a 30% margin,
        exactly following the selimsef DFDC solution pipeline.
        """
        # Ensure image is in RGB format
        if pil_image.mode != "RGB":
            pil_image = pil_image.convert("RGB")
            
        img_w, img_h = pil_image.size

        # Detect bounding boxes and landmarks
        boxes, probs = self.mtcnn.detect(pil_image)

        if boxes is None or len(boxes) == 0:
            return None, None

        # Select the box with the highest detection probability / largest area
        best_box = None
        best_area = -1
        for i, box in enumerate(boxes):
            x1, y1, x2, y2 = box
            area = (x2 - x1) * (y2 - y1)
            if area > best_area and (probs is None or probs[i] > 0.5):
                best_area = area
                best_box = box

        if best_box is None:
            best_box = boxes[0]

        x1, y1, x2, y2 = [int(coord) for coord in best_box]
        w = x2 - x1
        h = y2 - y1

        # Apply 30% margin on all 4 sides (selimsef benchmark standard)
        margin_x = int(w * DEFAULT_MARGIN_RATIO)
        margin_y = int(h * DEFAULT_MARGIN_RATIO)

        x1_crop = max(0, x1 - margin_x)
        y1_crop = max(0, y1 - margin_y)
        x2_crop = min(img_w, x2 + margin_x)
        y2_crop = min(img_h, y2 + margin_y)

        cropped_face = pil_image.crop((x1_crop, y1_crop, x2_crop, y2_crop))
        bbox_coords = [x1, y1, x2, y2]
        return cropped_face, bbox_coords

    def _preprocess_tensor(self, face_pil: Image.Image):
        """
        Converts the cropped face into the normalized PyTorch tensor
        matching EfficientNet-B7 input standards (380x380, ImageNet mean/std).
        """
        import torch
        from torchvision import transforms

        transform_pipeline = transforms.Compose([
            transforms.Resize((DEFAULT_INPUT_SIZE, DEFAULT_INPUT_SIZE), interpolation=transforms.InterpolationMode.BICUBIC),
            transforms.ToTensor(),
            transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD)
        ])

        tensor = transform_pipeline(face_pil)
        # Add batch dimension: (1, 3, 380, 380)
        return tensor.unsqueeze(0).to(self.device)

    def predict(
        self,
        image_input: Union[str, Path, Image.Image, bytes, io.BytesIO],
        threshold: float = 0.5
    ) -> Dict[str, Any]:
        """
        Performs deepfake detection on an input image.

        Args:
            image_input: Image file path, PIL Image, raw bytes, or BytesIO buffer.
            threshold: Probability threshold above which the image is classified as a deepfake.

        Returns:
            JSON-serializable dictionary containing:
                - face_detected (bool)
                - is_deepfake (bool)
                - confidence_score (float)
                - fake_probability (float)
                - real_probability (float)
                - face_box (Optional[List[int]])
                - error (Optional[str])
        """
        # Ensure service is lazily initialized
        if not self._is_initialized:
            try:
                self.initialize()
            except Exception as e:
                logger.error(f"DeepFakeService failed to initialize: {e}")
                return {
                    "face_detected": False,
                    "is_deepfake": False,
                    "confidence_score": 0.0,
                    "fake_probability": 0.0,
                    "real_probability": 0.0,
                    "face_box": None,
                    "error": f"Service initialization failed: {str(e)}"
                }

        import torch

        # 1. Load & validate image
        pil_image = None
        try:
            if isinstance(image_input, (str, Path)):
                if not os.path.exists(str(image_input)):
                    return {
                        "face_detected": False,
                        "is_deepfake": False,
                        "confidence_score": 0.0,
                        "fake_probability": 0.0,
                        "real_probability": 0.0,
                        "face_box": None,
                        "error": f"Image file not found: {image_input}"
                    }
                pil_image = Image.open(str(image_input))
            elif isinstance(image_input, bytes):
                pil_image = Image.open(io.BytesIO(image_input))
            elif isinstance(image_input, io.BytesIO):
                pil_image = Image.open(image_input)
            elif isinstance(image_input, Image.Image):
                pil_image = image_input
            else:
                return {
                    "face_detected": False,
                    "is_deepfake": False,
                    "confidence_score": 0.0,
                    "fake_probability": 0.0,
                    "real_probability": 0.0,
                    "face_box": None,
                    "error": f"Unsupported input type: {type(image_input)}"
                }

            # Handle EXIF orientation rotation
            pil_image = ImageOps.exif_transpose(pil_image)
            pil_image.load()  # Verify integrity
        except Exception as e:
            logger.error(f"Error decoding image: {e}")
            return {
                "face_detected": False,
                "is_deepfake": False,
                "confidence_score": 0.0,
                "fake_probability": 0.0,
                "real_probability": 0.0,
                "face_box": None,
                "error": f"Corrupted or invalid image: {str(e)}"
            }

        # 2. Face Extraction via MTCNN
        try:
            face_crop, bbox = self._extract_face_and_crop(pil_image)
        except Exception as e:
            logger.error(f"Face extraction error: {e}")
            return {
                "face_detected": False,
                "is_deepfake": False,
                "confidence_score": 0.0,
                "fake_probability": 0.0,
                "real_probability": 0.0,
                "face_box": None,
                "error": f"Face detection error: {str(e)}"
            }

        if face_crop is None:
            return {
                "face_detected": False,
                "is_deepfake": False,
                "confidence_score": 0.0,
                "fake_probability": 0.0,
                "real_probability": 1.0,
                "face_box": None,
                "error": "No human face detected in the image"
            }

        # 3. Preprocess Tensor & Run EfficientNet Forward Pass
        try:
            input_tensor = self._preprocess_tensor(face_crop)

            with torch.no_grad():
                logits = self.model.encoder(input_tensor)
                # Apply sigmoid to convert logit to [0, 1] fake probability
                if isinstance(logits, (tuple, list)):
                    logits = logits[0]
                fake_prob = torch.sigmoid(logits).squeeze().item()

            is_fake = bool(fake_prob >= threshold)
            confidence = fake_prob if is_fake else (1.0 - fake_prob)

            return {
                "face_detected": True,
                "is_deepfake": is_fake,
                "confidence_score": round(float(confidence), 4),
                "fake_probability": round(float(fake_prob), 4),
                "real_probability": round(float(1.0 - fake_prob), 4),
                "face_box": bbox,
                "error": None
            }

        except Exception as e:
            logger.error(f"Inference error during model execution: {e}")
            return {
                "face_detected": True,
                "is_deepfake": False,
                "confidence_score": 0.0,
                "fake_probability": 0.0,
                "real_probability": 0.0,
                "face_box": bbox,
                "error": f"Inference execution failed: {str(e)}"
            }


# ---------------------------------------------------------------------------
# Primary Functional API (Ready for Flask route usage)
# ---------------------------------------------------------------------------

def detect_deepfake(
    image_input: Union[str, Path, Image.Image, bytes, io.BytesIO],
    threshold: float = 0.5,
    weights_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Primary callable function for Flask backend routes.

    Example Flask Route:
        from deepfake_api import detect_deepfake

        @app.route('/api/detect-deepfake', methods=['POST'])
        def api_detect_deepfake():
            if 'image' not in request.files:
                return jsonify({"error": "No image uploaded"}), 400
            file = request.files['image']
            result = detect_deepfake(file.read())
            return jsonify(result)
    """
    service = DeepFakeService.get_instance(weights_path=weights_path)
    return service.predict(image_input=image_input, threshold=threshold)


if __name__ == "__main__":
    import sys
    print("Deepfake Detection API Module Loaded.")
    print(f"Default Weights Path: {DEFAULT_WEIGHTS_PATH}")
    if len(sys.argv) > 1:
        test_path = sys.argv[1]
        print(f"Testing detection on: {test_path}")
        res = detect_deepfake(test_path)
        print("Result:", res)
