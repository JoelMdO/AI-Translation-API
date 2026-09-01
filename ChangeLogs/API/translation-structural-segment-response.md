# Translation structural segment response fix

## Overview

Updated the translation response contract so structural HTML segments can be returned
without a `text` value. This prevents valid image and separator translations from being
converted into HTTP 500 responses by Pydantic validation.

## Need for change

`translate_html_content()` returns text segments as well as structural segments such as
`img` and `hr`. Structural segments contain metadata rather than translated text, but
`TranslatedSegment.text` was required.

## Affected files and functions

- `app/schemas/translation.py`: `TranslatedSegment`, `TranslatedText`, and
  `TranslationResponse`.
- `app/services/translation_service.py`: `TranslationService.translate()`.
- `tests/test_translation_response_contract.py`: structural-segment regression test.

## Original code

```python
class TranslatedSegment(BaseModel):
    id: int
    tag: str | None = None
    text: str
```

The service passed a raw dictionary directly to `TranslationResponse` and did not log the
validation exception before returning status 500.

## New code

`text` is optional for structural segments, and the schema preserves `src`, `alt`, and
`href` metadata. The service normalizes the translated fields through `TranslatedText`
before building `TranslationResponse` and logs unexpected failures.

## Test report

`tests/test_translation_response_contract.py` reproduces the former 500 with a mixed
paragraph, image, and separator result. The test passes after the schema correction.
