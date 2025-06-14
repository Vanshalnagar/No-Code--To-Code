# parser/validator.py
from .models import RawWorkflow
from pydantic import ValidationError
import logging

logger = logging.getLogger(__name__)

def validate_structure(raw_data: dict) -> RawWorkflow:
    try:
        return RawWorkflow(**raw_data)
    except ValidationError as e:
        logger.error(f"Validation failed: {str(e)}")
        logger.debug("Validation details:\n" + e.json(indent=2))
        raise ValueError("Workflow validation failed") from e
