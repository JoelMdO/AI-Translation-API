# Test: translation structural segment response

## Overview

Added regression coverage for successful translations containing structural HTML
segments without text.

## Reason for change

The service previously returned status 500 when Pydantic validated image or separator
segments whose data correctly omitted `text`.

## Affected function

- `TranslationService.translate()`

## Original coverage

No active test exercised the current `translation_service.py` response contract with
mixed translated and structural segments.

## New coverage

The test mocks only translation I/O, calls the real service and response schemas, checks
for status 200, verifies that image metadata is retained, and verifies that separator
text is represented as `None`.

## Result

The test failed with status 500 before the implementation and passes after the fix.
