# Testing guide

Install development dependencies from the repository root:

```sh
python -m pip install -r requirements-dev.txt
```

Run the complete test suite:

```sh
PYTHONPATH=backend pytest -q
```

The tests cover parser extraction and warning validation, valid and invalid
batch uploads, response ordering, and the OCR integration boundary. CI runs
the same command on every push and pull request.
