import re


TOKEN_PATTERN = re.compile(r"\S+")


def chunk_pages(
	pages: list[dict[str, int | str]],
	chunk_size_tokens: int,
	overlap_tokens: int,
) -> list[dict[str, int | str]]:
	if chunk_size_tokens <= 0:
		raise ValueError("chunk_size_tokens must be > 0")
	if overlap_tokens < 0:
		raise ValueError("overlap_tokens must be >= 0")
	if overlap_tokens >= chunk_size_tokens:
		raise ValueError("overlap_tokens must be smaller than chunk_size_tokens")

	annotated_tokens: list[dict[str, int | str]] = []
	for page_item in pages:
		page_number = int(page_item["page"])
		page_text = str(page_item["text"])
		for match in TOKEN_PATTERN.finditer(page_text):
			annotated_tokens.append({"token": match.group(0), "page": page_number})

	if not annotated_tokens:
		return []

	chunks: list[dict[str, int | str]] = []
	start = 0
	chunk_index = 0

	while start < len(annotated_tokens):
		end = min(start + chunk_size_tokens, len(annotated_tokens))
		window = annotated_tokens[start:end]

		chunk_text = " ".join(str(item["token"]) for item in window)
		chunk_page = min(int(item["page"]) for item in window)

		chunks.append(
			{
				"chunk_index": chunk_index,
				"text": chunk_text,
				"page": chunk_page,
			}
		)

		if end >= len(annotated_tokens):
			break

		start = end - overlap_tokens
		chunk_index += 1

	return chunks
