"""
Vision Service Module

This module handles image processing using LLaMA vision model.
"""

import base64
from io import BytesIO
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

import requests
import torch
from PIL import Image
from transformers import AutoModelForCausalLM, AutoProcessor

from core.config import settings
from utils.logger import get_logger

logger = get_logger(__name__)

class VisionService:
    """Service for image processing using LLaMA vision model."""
    
    def __init__(self):
        """Initialize the vision service."""
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {self.device}")
        
        # Load vision model and processor
        self.model = self._load_model()
        self.processor = AutoProcessor.from_pretrained(
            settings.VISION_MODEL_ID,
            token=settings.HF_ACCESS_TOKEN
        )
    
    def _load_model(self) -> AutoModelForCausalLM:
        """Load the vision model."""
        try:
            model = AutoModelForCausalLM.from_pretrained(
                settings.VISION_MODEL_ID,
                token=settings.HF_ACCESS_TOKEN,
                torch_dtype=torch.float16,
                device_map="auto"
            )
            return model
        except Exception as e:
            logger.error(f"Error loading vision model: {str(e)}")
            raise
    
    async def process_image(
        self,
        image_source: str,
        tasks: Optional[List[str]] = None
    ) -> Dict[str, str]:
        """
        Process an image for various tasks.
        
        Args:
            image_source: URL or base64 string of the image
            tasks: List of tasks to perform (e.g., ["describe", "identify_logo"])
        
        Returns:
            Dictionary mapping tasks to their results
        """
        try:
            # Load image
            image = await self._load_image(image_source)
            if not image:
                return {"error": "Failed to load image"}
            
            # Process image with default tasks if none specified
            if not tasks:
                tasks = ["describe"]
            
            results = {}
            for task in tasks:
                result = await self._process_task(image, task)
                results[task] = result
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            return {"error": str(e)}
    
    async def _load_image(self, image_source: str) -> Optional[Image.Image]:
        """Load image from URL or base64 string."""
        try:
            if self._is_url(image_source):
                return await self._load_image_from_url(image_source)
            elif self._is_base64(image_source):
                return self._load_image_from_base64(image_source)
            else:
                raise ValueError("Invalid image source format")
        except Exception as e:
            logger.error(f"Error loading image: {str(e)}")
            return None
    
    def _is_url(self, source: str) -> bool:
        """Check if source is a URL."""
        try:
            result = urlparse(source)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    def _is_base64(self, source: str) -> bool:
        """Check if source is a base64 string."""
        try:
            # Remove data URL prefix if present
            if source.startswith("data:image"):
                source = source.split(",")[1]
            base64.b64decode(source)
            return True
        except Exception:
            return False
    
    async def _load_image_from_url(self, url: str) -> Image.Image:
        """Load image from URL."""
        try:
            response = requests.get(url, timeout=settings.DEFAULT_TIMEOUT)
            response.raise_for_status()
            return Image.open(BytesIO(response.content))
        except Exception as e:
            logger.error(f"Error loading image from URL: {str(e)}")
            raise
    
    def _load_image_from_base64(self, base64_string: str) -> Image.Image:
        """Load image from base64 string."""
        try:
            # Remove data URL prefix if present
            if base64_string.startswith("data:image"):
                base64_string = base64_string.split(",")[1]
            
            image_data = base64.b64decode(base64_string)
            return Image.open(BytesIO(image_data))
        except Exception as e:
            logger.error(f"Error loading image from base64: {str(e)}")
            raise
    
    async def _process_task(
        self,
        image: Image.Image,
        task: str
    ) -> str:
        """Process a single vision task."""
        try:
            # Prepare prompt based on task
            prompt = self._get_task_prompt(task)
            
            # Prepare inputs
            inputs = self.processor(
                images=image,
                text=prompt,
                return_tensors="pt"
            ).to(self.device, torch.float16)
            
            # Generate response
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=100,
                do_sample=True,
                temperature=0.7,
                top_p=0.95
            )
            
            # Decode and clean response
            response = self.processor.batch_decode(
                outputs,
                skip_special_tokens=True
            )[0]
            
            return self._clean_response(response)
            
        except Exception as e:
            logger.error(f"Error processing task {task}: {str(e)}")
            return f"Error: {str(e)}"
    
    def _get_task_prompt(self, task: str) -> str:
        """Get prompt for specific vision task."""
        prompts = {
            "describe": "Describe this image in detail.",
            "identify_logo": "What company or brand logo appears in this image?",
            "extract_text": "What text appears in this image?",
            "analyze_style": "Describe the visual style and design elements of this image.",
            "identify_objects": "List the main objects and elements visible in this image."
        }
        return prompts.get(task, "Describe this image.")
    
    def _clean_response(self, response: str) -> str:
        """Clean and format model response."""
        # Remove any system prompts or artifacts
        response = response.split("[/INST]")[-1].strip()
        
        # Remove any trailing special tokens
        response = response.split("<|endoftext|>")[0].strip()
        
        return response
    
    async def find_similar_images(
        self,
        image_source: str,
        max_results: int = 5
    ) -> List[Tuple[str, float]]:
        """
        Find similar images based on visual features.
        Not implemented yet - placeholder for future feature.
        """
        logger.warning("find_similar_images not implemented yet")
        return [] 