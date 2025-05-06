# Test Warning Fixes

## Summary of Fixed Warnings

We've fixed several deprecation warnings in the test suite:

1. **Updated Pydantic Validators**:
   - Replaced the deprecated `@validator` with the new `@field_validator` decorator in `src/schemas.py`
   - This addresses Pydantic v2 deprecation warnings

2. **Fixed SQLAlchemy Base Deprecation**:
   - Updated the import from `sqlalchemy.ext.declarative import declarative_base` to `sqlalchemy.orm import declarative_base` in `src/models.py`
   - This follows SQLAlchemy's recommended import path

3. **Fixed Path Parameter Examples**:
   - Replaced deprecated `example="value"` format with the new `examples={"name": {"value": "value"}}` format in `src/routers/offer_router.py`
   - This follows FastAPI's OpenAPI schema changes

4. **Updated datetime.utcnow() Usage**:
   - Replaced deprecated `datetime.utcnow()` with `datetime.now(UTC)` in `tests/test_order_router.py`
   - Added the necessary `UTC` import from the datetime module
   - This follows Python's timezone-aware datetime best practices

5. **Demonstrated Pydantic Config Updates**:
   - Added an example of replacing class-based Config with ConfigDict in `src/schemas.py`
   - Example: `model_config = ConfigDict(json_schema_extra={...})`

## Remaining Warnings

There are still some warnings that need to be addressed:

1. **Pydantic Class-based Config (8 instances)**:
   - Warning: `Support for class-based 'config' is deprecated, use ConfigDict instead`
   - These occur in other Pydantic models that still use the class Config approach
   - To fix: Convert all remaining class Config instances to model_config = ConfigDict()

2. **Passlib crypt Deprecation**:
   - Warning: `'crypt' is deprecated and slated for removal in Python 3.13`
   - This comes from a third-party library (passlib) that the project depends on
   - To fix: Wait for a passlib update or consider alternative password hashing libraries

3. **fastapi_sessions copy Method Deprecation**:
   - Warning: `The 'copy' method is deprecated; use 'model_copy' instead`
   - This comes from a third-party library (fastapi_sessions)
   - To fix: Wait for a library update or fork and modify the library

4. **Pytest Collection Warning** (in full test run):
   - Warning: `cannot collect 'test_app' because it is not a function`
   - This occurs when pytest tries to collect the FastAPI app as a test function
   - To fix: Rename variables or add pytest collection markers

5. **Starlette TestClient Cookie Deprecation** (in full test run):
   - Warning: `Setting per-request cookies=<...> is being deprecated`
   - This occurs in auth router tests
   - To fix: Set cookies directly on the client instance instead of per-request

## Next Steps

To fully eliminate all warnings:

1. Complete the conversion of all Pydantic models to use ConfigDict instead of class Config
2. Update test client cookie handling in auth router tests
3. Consider updating or replacing third-party libraries with deprecation warnings
4. Rename test_app variables to avoid pytest collection issues

## Benefits

Addressing these warnings:
- Prepares the codebase for future Python and library updates
- Follows best practices for timezone handling
- Updates to latest Pydantic v2 features
- Improves overall code maintainability 