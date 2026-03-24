from pathlib import Path

import fitz


def extract_text_by_page(pdf_path: Path) -> list[dict[str, int | str]]:
	pages: list[dict[str, int | str]] = []

	with fitz.open(pdf_path) as document:
		for page_number, page in enumerate(document, start=1):
			text = page.get_text("text").strip()
			if text:
				pages.append({"page": page_number, "text": text})

	if not pages:
		raise ValueError("No extractable text found in PDF.")

	return pages
