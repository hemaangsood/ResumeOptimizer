import json
import hashlib
from typing import Dict, Any, Optional
from openai import OpenAI


class ModelHandler:
	"""Handles all model prompting, response parsing, and caching."""

	def __init__(self, client: OpenAI, model: str = "gpt-4o-mini", cache=None):
		"""
		Initialize ModelHandler.
		
		Args:
			client: OpenAI client instance
			model: Model name to use (default: gpt-4o-mini)
			cache: Optional cache instance (must support .get(key) and .set(key, value))
		"""
		self.client = client
		self.model = model
		self.cache = cache

	# -------------------- HASH --------------------
	def _hash(self, text: str) -> str:
		"""Generate SHA256 hash of text for cache key."""
		return hashlib.sha256(text.encode()).hexdigest()

	# -------------------- PROMPT HANDLING --------------------
	def prompt(
		self,
		prompt_text: str,
		use_json_mode: bool = False,
		cache_key: Optional[str] = None
	) -> str:
		"""
		Send a prompt to the model and return raw response text.
		
		Args:
			prompt_text: The prompt to send
			use_json_mode: Whether to enforce JSON output format
			cache_key: Optional custom cache key (defaults to hash of prompt_text)
		
		Returns:
			Raw response text from model
		"""
		key = cache_key or self._hash(prompt_text)
		# Generate cache key if not -1 (used to bypass cache when -1)
		if cache_key=="-1":
			key = None

		# Check cache first
		if self.cache and key:
			cached = self.cache.get(key)
			if cached:
				return cached

		# Build request kwargs
		kwargs:dict[str, Any] = {
			"model": self.model,
			"messages": [
				{"role": "system", "content": "You output only valid JSON." if use_json_mode else "You are a helpful assistant."},
				{"role": "user", "content": prompt_text}
			],
			"temperature": 0
		}

		if use_json_mode:
			kwargs["response_format"] = {"type": "json_object"}

		# Make API call
		response = self.client.chat.completions.create(**kwargs)
		content = response.choices[0].message.content

		# Cache the response
		if self.cache and key:
			self.cache.set(key, content)

		return content

	# -------------------- JSON PARSING --------------------
	@staticmethod
	def _clean_json_response(response_text: str) -> str:
		"""Remove code fences (```json ... ```) from response text."""
		text = response_text.strip()
		if text.startswith("```"):
			text = text[3:]
		if text.startswith("json"):
			text = text[4:]
		if text.endswith("```"):
			text = text[:-3]
		return text.strip()

	def prompt_for_json(
		self,
		prompt_text: str,
		cache_key: Optional[str] = None,
		use_cache: bool = True
	) -> Dict[str, Any]:
		"""
		Send a prompt and parse response as JSON.
		
		Args:
			prompt_text: The prompt to send
			cache_key: Optional custom cache key
			use_cache: Whether to use caching (default: True)
		Returns:
			Parsed JSON response as dictionary
			
		Raises:
			ValueError: If response is not valid JSON
		"""
		response_text = self.prompt(prompt_text, use_json_mode=True, cache_key=cache_key if use_cache else "-1")
		cleaned = self._clean_json_response(response_text)

		try:
			return json.loads(cleaned)
		except json.JSONDecodeError as e:
			raise ValueError(f"Model response is not valid JSON: {e}\nResponse: {cleaned}")
