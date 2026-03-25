from collections import deque
import time

from google import genai
from google.genai import types


class RetryableEmbeddingError(Exception):
	pass


class EmbeddingValidationError(Exception):
	pass


class GeminiEmbedder:
	def __init__(
		self,
		api_key: str,
		model: str,
		expected_dimension: int = 768,
		max_retries: int = 3,
		retry_base_delay_sec: float = 1.0,
		rate_limit_per_minute: int = 240,
	) -> None:
		if not api_key:
			raise ValueError("GEMINI_API_KEY is required")
		if max_retries < 1:
			raise ValueError("max_retries must be >= 1")
		if retry_base_delay_sec <= 0:
			raise ValueError("retry_base_delay_sec must be > 0")
		if rate_limit_per_minute <= 0:
			raise ValueError("rate_limit_per_minute must be > 0")

		self.model = model.removeprefix("models/")
		self.expected_dimension = expected_dimension
		self.max_retries = max_retries
		self.retry_base_delay_sec = retry_base_delay_sec
		self.rate_limit_per_minute = rate_limit_per_minute
		self._request_timestamps: deque[float] = deque()
		self.client = genai.Client(api_key=api_key)

	def _throttle(self) -> None:
		now = time.time()
		window = 60.0
		while self._request_timestamps and now - self._request_timestamps[0] >= window:
			self._request_timestamps.popleft()

		if len(self._request_timestamps) >= self.rate_limit_per_minute:
			sleep_for = window - (now - self._request_timestamps[0])
			if sleep_for > 0:
				time.sleep(sleep_for)

		self._request_timestamps.append(time.time())

	def _embed_contents(self, contents: str | list[str]):
		attempt = 0
		while True:
			try:
				self._throttle()
				return self.client.models.embed_content(
					model=self.model,
					contents=contents,
					config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"),
				)
			except Exception as exc:
				attempt += 1
				if attempt >= self.max_retries:
					raise RetryableEmbeddingError(
						f"Embedding provider failed after {self.max_retries} attempts: {exc}"
					) from exc
				time.sleep(self.retry_base_delay_sec * (2 ** (attempt - 1)))

	def _validate_vector(self, values: list[float]) -> list[float]:
		vector = [float(v) for v in values]
		if len(vector) != self.expected_dimension:
			raise EmbeddingValidationError(
				f"Embedding dimension mismatch: expected {self.expected_dimension}, got {len(vector)}"
			)
		return vector

	def embed_text(self, text: str) -> list[float]:
		result = self._embed_contents(text)

		embeddings = getattr(result, "embeddings", None)
		if not embeddings:
			raise EmbeddingValidationError("Gemini returned an empty embedding response.")

		values = getattr(embeddings[0], "values", None)
		if not values:
			raise EmbeddingValidationError("Gemini returned empty embedding values.")

		return self._validate_vector(values)

	def embed_texts(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
		if batch_size <= 0:
			raise ValueError("batch_size must be > 0")
		if not texts:
			return []

		all_vectors: list[list[float]] = []
		for start in range(0, len(texts), batch_size):
			batch = texts[start : start + batch_size]
			result = self._embed_contents(batch)
			embeddings = getattr(result, "embeddings", None)
			if not embeddings:
				raise EmbeddingValidationError("Gemini returned an empty embedding response.")
			if len(embeddings) != len(batch):
				raise EmbeddingValidationError(
					f"Embedding count mismatch: expected {len(batch)}, got {len(embeddings)}"
				)

			for embedding in embeddings:
				values = getattr(embedding, "values", None)
				if not values:
					raise EmbeddingValidationError("Gemini returned empty embedding values.")
				all_vectors.append(self._validate_vector(values))

		return all_vectors
