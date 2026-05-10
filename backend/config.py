import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class EnvironmentConfigurationError(Exception):
    """Raised when a required environment variable is missing."""
    pass

# Base paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

# Raw Data Paths
RAW_EXPRESSION_DIR = DATA_DIR / "raw" / "expression"
RAW_CLINICAL_DIR = DATA_DIR / "raw" / "clinical"
RAW_MUTATION_DIR = DATA_DIR / "raw" / "mutation"
HGNC_REFERENCE_FILE = DATA_DIR / "raw" / "hgnc_approved_symbols.txt"

# Processed Data Paths
PROCESSED_EXPRESSION_DIR = DATA_DIR / "processed" / "expression"
PROCESSED_CLINICAL_DIR = DATA_DIR / "processed" / "clinical"
PROCESSED_MUTATION_DIR = DATA_DIR / "processed" / "mutation"

# Output Paths
CACHE_DIR = BASE_DIR / "cache"
REPORTS_DIR = BASE_DIR / "reports"
LOGS_DIR = BASE_DIR / "logs"

# Ensure output paths exist
CACHE_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Supported Cancers
SUPPORTED_CANCERS = {
    "Breast Invasive Carcinoma": "BRCA",
    "Lung Adenocarcinoma": "LUAD",
    "Colon Adenocarcinoma": "COAD"
}

# Statistical Thresholds
SIGNIFICANCE_THRESHOLD = 0.05
DEFAULT_SPLIT_STRATEGY = "median"
MIN_TUMOR_SAMPLES = 50
MIN_NORMAL_SAMPLES = 10
MIN_SURVIVAL_GROUP_SIZE = 20

# AI Configuration
OPENROUTER_API_BASE_URL = os.getenv("OPENROUTER_API_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
AI_MODEL_NAME = os.getenv("AI_MODEL_NAME", "openai/gpt-3.5-turbo")
AI_MAX_TOKENS = int(os.getenv("AI_MAX_TOKENS", "150"))
AI_TEMPERATURE = float(os.getenv("AI_TEMPERATURE", "0.2"))

# Warn if OPENROUTER_API_KEY is missing or is the placeholder value
import logging as _logging
_placeholder_key = OPENROUTER_API_KEY in [None, "", "your_openrouter_api_key"]
if _placeholder_key:
    _logging.warning(
        "OPENROUTER_API_KEY is not set or is a placeholder. "
        "AI interpretation will use a fallback template. "
        "Set a valid key in backend/.env to enable live AI summaries."
    )

# Cache Configuration
CACHE_TTL_HOURS = float(os.getenv("CACHE_TTL_HOURS", "24.0"))
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "True").lower() in ["true", "1", "yes"]
