# parser/plugin_loader.py
import logging

logger = logging.getLogger(__name__)

# Plugin registry would be populated from external sources
PLUGIN_REGISTRY = {
    "gmailOAuth2": lambda cred: {"token": "mock_token"},
    "googlePalmApi": lambda cred: {"api_key": "mock_key"},
}

def resolve_credentials(credentials: dict) -> dict:
    resolved = {}
    for cred_type, cred_data in credentials.items():
        if cred_type in PLUGIN_REGISTRY:
            try:
                resolved[cred_type] = PLUGIN_REGISTRY[cred_type](cred_data)
            except Exception as e:
                logger.error(f"Credential resolution failed for {cred_type}: {str(e)}")
                raise
        else:
            logger.warning(f"No resolver for credential type: {cred_type}")
            resolved[cred_type] = cred_data  # Pass through raw data
    return resolved
