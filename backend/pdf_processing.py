"""Page-preserving extraction of searchable text and embedded raster images."""

from io import BytesIO

from pypdf import PdfReader


def extract_pdf_pages(pdf_bytes: bytes) -> list[dict]:
    """Return every PDF page with searchable text and its embedded JPEG/PNG images."""
    try:
        reader = PdfReader(BytesIO(pdf_bytes))
        pages = []
        total_pages = len(reader.pages)
        for page_number, page in enumerate(reader.pages, start=1):
            images = []
            unsupported_image = False
            try:
                for image in page.images:
                    data = image.data
                    if data.startswith(b"\xff\xd8\xff"):
                        mime_type = "image/jpeg"
                    elif data.startswith(b"\x89PNG\r\n\x1a\n"):
                        mime_type = "image/png"
                    else:
                        unsupported_image = True
                        continue
                    images.append({"bytes": data, "mime_type": mime_type})
            except Exception:
                # Some PDFs contain unsupported decorative XObjects. Continue
                # extracting text and other readable images from this page.
                unsupported_image = True
            text = (page.extract_text() or "").strip()
            # Only rasterize a page when no searchable text or supported image
            # was extracted. Re-rendering every text page that contains a
            # decorative vector/logo made long policies needlessly slow.
            if not text and (unsupported_image or not images):
                try:
                    import fitz

                    document = fitz.open(stream=pdf_bytes, filetype="pdf")
                    rendered = document.load_page(page_number - 1).get_pixmap(
                        matrix=fitz.Matrix(1.5, 1.5), alpha=False
                    )
                    images = [{"bytes": rendered.tobytes("png"), "mime_type": "image/png"}]
                    document.close()
                except ImportError as exc:
                    raise ValueError(
                        "This PDF contains scanned or unsupported page images; install PyMuPDF to read them."
                    ) from exc
                except Exception as exc:
                    raise ValueError(f"Could not render PDF page {page_number} for image reading.") from exc
            pages.append({
                "page": page_number,
                "page_count": total_pages,
                "text": text,
                "images": images,
            })
        return pages
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("Could not read this PDF. Check that it is not encrypted or damaged.") from exc
