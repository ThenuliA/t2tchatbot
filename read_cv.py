from pathlib import Path
import atexit
import signal

import requests

from scrape_data import extract_pdf_text_from_bytes, clean_extracted_text


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_CV_SOURCE = "test_cv.pdf"
TEMP_CV_FILE = BASE_DIR / "temp_cv.txt"

_registered_temp_file: Path | None = None


def fetch_pdf(source: str = DEFAULT_CV_SOURCE) -> bytes:
	"""
	Fetch CV PDF bytes.
	For now this defaults to local `test_cv.pdf` inside the final/ directory.
	Accepts either a local path or an HTTP/HTTPS URL.
	"""
	source = source.strip()

	if source.startswith(("http://", "https://")):
		response = requests.get(source, timeout=15)
		response.raise_for_status()
		return response.content

	local_path = Path(source)
	if not local_path.is_absolute():
		local_path = BASE_DIR / source

	if not local_path.exists():
		raise FileNotFoundError(f"PDF source not found: {local_path}")

	return local_path.read_bytes()


def read_cv_text(pdf_bytes: bytes) -> str:
	"""Convert CV PDF bytes into cleaned, legible text."""
	text = extract_pdf_text_from_bytes(pdf_bytes)
	return clean_extracted_text(text)


def write_temp_cv_text(cv_text: str, target_file: Path = TEMP_CV_FILE) -> Path:
	"""Write CV text to temp file and return the file path."""
	global _registered_temp_file

	target_file.parent.mkdir(parents=True, exist_ok=True)
	with open(target_file, "w", encoding="utf-8") as file:
		file.write("===CV TEXT===\n")
		file.write(cv_text.strip())
		file.write("\n")

	_registered_temp_file = target_file
	return target_file


def cleanup_temp_file(path: Path | None = None):
	"""Delete temp CV file if it exists."""
	target = path or _registered_temp_file or TEMP_CV_FILE
	try:
		if target.exists():
			target.unlink()
			print(f"Deleted temp file: {target}")
	except Exception as error:
		print(f"Could not delete temp file '{target}': {error}")


def _handle_exit_signal(signum, frame):
	cleanup_temp_file()
	raise SystemExit(0)


def main():
	atexit.register(cleanup_temp_file)
	signal.signal(signal.SIGINT, _handle_exit_signal)
	if hasattr(signal, "SIGTERM"):
		signal.signal(signal.SIGTERM, _handle_exit_signal)

	print("Fetching CV PDF...")
	pdf_bytes = fetch_pdf()

	print("Extracting text from CV...")
	cv_text = read_cv_text(pdf_bytes)
	if not cv_text:
		raise ValueError("No readable text found in test_cv.pdf")

	temp_file = write_temp_cv_text(cv_text)
	print(f"Created temp file: {temp_file}")
	# just print the first line to see whether it works or not
	try:
		with open(temp_file, "r", encoding="utf-8") as f:
			print(f.readline().strip())
	except FileNotFoundError:
		print("Temp file not found for reading first line.")

	print("Close the opened file to auto-delete it and exit.")
	cleanup_temp_file(temp_file)


if __name__ == "__main__":
	main()
