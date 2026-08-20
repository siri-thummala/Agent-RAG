# This type describes one page returned by our PDF extractor.
# Each page contains a page number and its extracted text.
ExtractedPage = dict[str, int | str]

# This type describes one smaller piece of a PDF page.
TextChunk = dict[str, int | str]


def chunk_pages(
    extracted_pages: list[ExtractedPage],
    chunk_size: int = 200,
    overlap: int = 40,
) -> list[TextChunk]:
    """
    Split extracted PDF pages into smaller, overlapping text chunks.

    `chunk_size=200` means each chunk contains up to 200 words.

    `overlap=40` means the final 40 words of one chunk are repeated
    at the beginning of the next chunk. This helps preserve context
    when an important sentence crosses a chunk boundary.
    """

    # Prevent invalid settings that could create an endless loop.
    if chunk_size <= 0:
        raise ValueError("Chunk size must be greater than zero")

    if overlap < 0:
        raise ValueError("Overlap cannot be negative")

    if overlap >= chunk_size:
        raise ValueError("Overlap must be smaller than chunk size")

    # Store all chunks produced from all PDF pages.
    chunks: list[TextChunk] = []

    # Process each extracted PDF page separately.
    # Keeping pages separate preserves page-level citations.
    for page in extracted_pages:

        # Read the page number and text produced by pdf_extractor.py.
        page_number = int(page["page_number"])
        page_text = str(page["text"]).strip()

        # Skip pages that contain no usable text.
        if not page_text:
            continue

        # Split the page text into individual words.
        words = page_text.split()

        # The first chunk begins at the first word.
        start = 0

        # Number chunks separately within each page.
        chunk_index = 0

        while start < len(words):

            # Decide where this chunk ends.
            end = min(start + chunk_size, len(words))

            # Join the selected words back into readable text.
            chunk_text = " ".join(words[start:end]).strip()

            if chunk_text:
                chunks.append(
                    {
                        "page_number": page_number,
                        "chunk_index": chunk_index,
                        "text": chunk_text,
                    }
                )

                chunk_index += 1

            # Stop after processing the final words on the page.
            if end == len(words):
                break

            # Move forward while repeating some words for context.
            start = end - overlap

    # The PDF extractor should already prevent this,
    # but this check keeps the chunker safe when used independently.
    if not chunks:
        raise ValueError("No text chunks could be created")

    return chunks