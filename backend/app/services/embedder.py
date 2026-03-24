import google.generativeai as genai


class GeminiEmbedder:
	def __init__(self, api_key: str, model: str, expected_dimension: int = 768) -> None:
		if not api_key:
			raise ValueError("GEMINI_API_KEY is required")

		self.model = model
		self.expected_dimension = expected_dimension
		genai.configure(api_key=api_key)

	def embed_text(self, text: str) -> list[float]:
		result = genai.embed_content(
			model=self.model,
			content=text,
			task_type="retrieval_document",
		)

		embedding = None
		if isinstance(result, dict):
			embedding = result.get("embedding")
		else:
			embedding = getattr(result, "embedding", None)

		if not embedding:
			raise RuntimeError("Gemini returned an empty embedding.")

		vector = [float(v) for v in embedding]
		if len(vector) != self.expected_dimension:
			raise ValueError(
				f"Embedding dimension mismatch: expected {self.expected_dimension}, got {len(vector)}"
			)

		return vector

	def embed_texts(self, texts: list[str]) -> list[list[float]]:
		return [self.embed_text(text) for text in texts]
