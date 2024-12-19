"""
LLM Service Module

This module handles interactions with the LLaMA language model for text processing.
"""

import json
from typing import Any, Dict, List, Optional

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, Pipeline, pipeline

from core.config import settings
from utils.logger import get_logger

logger = get_logger(__name__)

class LLMService:
    """Service for interacting with LLaMA models."""
    
    def __init__(self):
        """Initialize the LLM service."""
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {self.device}")
        
        # Load text model
        self.text_model = self._load_model(settings.TEXT_MODEL_ID)
        self.tokenizer = AutoTokenizer.from_pretrained(
            settings.TEXT_MODEL_ID,
            token=settings.HF_ACCESS_TOKEN
        )
        
        # Create pipeline for text generation
        self.pipe = pipeline(
            "text-generation",
            model=self.text_model,
            tokenizer=self.tokenizer,
            device=self.device,
            max_length=2048,
            do_sample=True,
            temperature=0.7,
            top_p=0.95
        )
    
    def _load_model(self, model_id: str) -> AutoModelForCausalLM:
        """Load a model from Hugging Face."""
        try:
            model = AutoModelForCausalLM.from_pretrained(
                model_id,
                token=settings.HF_ACCESS_TOKEN,
                torch_dtype=torch.float16,
                device_map="auto"
            )
            return model
        except Exception as e:
            logger.error(f"Error loading model {model_id}: {str(e)}")
            raise
    
    async def parse_instructions(self, instructions: str) -> List[str]:
        """Parse natural language instructions to identify fields to extract."""
        prompt = f"""Given the following content gathering instructions, identify and list the specific fields that need to be extracted or generated. Format the output as a JSON array of field names.

Instructions: {instructions}

Output format example: ["title", "description", "author"]

Fields to extract:"""
        
        try:
            response = await self._generate_text(prompt)
            fields = json.loads(response)
            return fields
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing fields from response: {str(e)}")
            return []
    
    async def generate_content(
        self,
        field: str,
        context: Optional[str] = None,
        item_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate content for a specific field using available context."""
        # Build prompt based on field and context
        prompt = self._build_generation_prompt(field, context, item_data)
        
        try:
            return await self._generate_text(prompt)
        except Exception as e:
            logger.error(f"Error generating content for field {field}: {str(e)}")
            return ""
    
    def _build_generation_prompt(
        self,
        field: str,
        context: Optional[str] = None,
        item_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build a prompt for content generation."""
        prompt_parts = [
            f"Generate content for the field '{field}'.",
            "The content should be concise, accurate, and professional."
        ]
        
        if context:
            prompt_parts.append(f"\nContext information:\n{context}")
        
        if item_data:
            item_context = "\nRelated item data:\n"
            item_context += "\n".join(
                f"- {k}: {v}" for k, v in item_data.items() if k != field
            )
            prompt_parts.append(item_context)
        
        prompt_parts.append(f"\nGenerated {field}:")
        return "\n".join(prompt_parts)
    
    async def _generate_text(self, prompt: str) -> str:
        """Generate text using the LLM pipeline."""
        try:
            # Add system prompt and format
            full_prompt = f"""<s>[INST] <<SYS>>
You are a helpful AI assistant that provides accurate and concise responses.
<</SYS>>

{prompt}[/INST]
"""
            
            # Generate response
            response = self.pipe(
                full_prompt,
                max_new_tokens=500,
                pad_token_id=self.tokenizer.eos_token_id
            )
            
            # Extract and clean generated text
            generated_text = response[0]["generated_text"]
            # Remove the prompt and instruction tokens
            generated_text = generated_text.split("[/INST]")[-1].strip()
            
            return generated_text
            
        except Exception as e:
            logger.error(f"Error in text generation: {str(e)}")
            raise 