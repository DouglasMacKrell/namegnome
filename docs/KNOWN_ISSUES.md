# Known Issues

## Persistent mypy False Positive: MediaMetadata.year Assignment in tmdb.py

### Summary
A persistent mypy error was encountered in `src/namegnome/metadata/clients/tmdb.py`:

```
Incompatible types in assignment (expression has type "int", target has type "str")  [assignment]
```
This occurred on the line:
```python
media.year = year
```
where `media` is a `MediaMetadata` instance and `year` is an `int | None`.

### Investigation & Attempted Fixes
- All type annotations in `MediaMetadata` and its parents were correct.
- No duplicate or shadowed modules were found.
- `ignore_missing_imports` was removed from `.mypy.ini`.
- Targeted `# type: ignore[assignment]` did not suppress the error.
- The error did not appear in isolated tests or the model file, only in the main codebase.

### Resolution
Per [mypy documentation](https://mypy.readthedocs.io/en/stable/common_issues.html#spurious-errors-and-locally-silencing-the-checker), a `.pyi` stub file was created at `src/namegnome/metadata/clients/tmdb.pyi` to expose only the public interface. This resolved the error and allowed all pre-commit and CI checks to pass.

### References
- [mypy: Common issues and solutions](https://mypy.readthedocs.io/en/stable/common_issues.html#spurious-errors-and-locally-silencing-the-checker)

### Note for Future Maintainers
If the underlying cause is identified (e.g., a mypy bug or config issue), the stub file can be removed and the implementation type-checked directly. 