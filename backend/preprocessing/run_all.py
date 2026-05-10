import argparse
import sys
from backend.utils.logger import StructuredLogger
from backend.preprocessing.preprocess_expression import preprocess_expression
from backend.preprocessing.preprocess_clinical import preprocess_clinical
from backend.preprocessing.preprocess_mutation import preprocess_mutation

logger = StructuredLogger(__name__)

def run_all(force: bool = False):
    logger.info("Starting preprocessing orchestrator", metadata={"force": force})
    
    try:
        # 1 & 2. Expression
        preprocess_expression(force=force)
        
        # 3. Clinical
        preprocess_clinical(force=force)
        
        # 4. Mutation
        preprocess_mutation(force=force)
        
        logger.info("All preprocessing completed successfully")
        return True
    except Exception as e:
        logger.error("Preprocessing failed", exc_info=True)
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run all preprocessing scripts.")
    parser.add_argument("--force", action="store_true", help="Force rerun of all preprocessing.")
    args = parser.parse_args()
    
    success = run_all(force=args.force)
    if not success:
        sys.exit(1)
