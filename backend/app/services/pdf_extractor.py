# `Path` represents the location of the uploaded PDF.
from pathlib import Path

# PdfReader opens a PDF and reads its pages.
from pypdf import PdfReader

# PdfReadError is raised when a file is damaged or is not a valid PDF.
from pypdf.errors import PdfReadError


def extract_pages_from_pdf(
    file_path: Path,
) -> list[dict[str, int | str]]:
    """
    Extract readable text from every page of a PDF.

    The result keeps the page number with its text so that the RAG
    system can provide page-level citations later.

    Example result:
    [
        {"page_number": 1, "text": "Text from page one..."},
        {"page_number": 2, "text": "Text from page two..."},
    ]
    """

    try:
        # Open and read the PDF from its stored location.
        reader = PdfReader(str(file_path))

    except PdfReadError as error:
        # Convert the library error into a simpler application error.
        raise ValueError("The uploaded file is not a readable PDF") from error

    # Password-protected PDFs are not supported in this version.
    if reader.is_encrypted:
        raise ValueError("Password-protected PDFs are not supported")

    # Store the extracted page number and text together.
    extracted_pages: list[dict[str, int | str]] = []

    # Page numbering begins at 1 because that is what users see in PDF readers.
    for page_number, page in enumerate(reader.pages, start=1):

        # Some PDF pages contain images but no selectable text.
        # In that case, extract_text() may return None.
        page_text = page.extract_text() or ""

        # Remove unnecessary spaces around the extracted text.
        page_text = page_text.strip()

        # Store only pages that contain readable text.
        if page_text:
            extracted_pages.append(
                {
                    "page_number": page_number,
                    "text": page_text,
                }
            )

    # A scanned PDF may contain only page images and no extractable text.
    # OCR support can be added later for those documents.
    if not extracted_pages:
        raise ValueError(
            "No readable text was found in the PDF"
        )

    return extracted_pages