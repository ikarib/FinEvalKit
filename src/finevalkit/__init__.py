"""FinEvalKit: audit-ready evaluation for financial-document AI."""

from .evaluation import evaluate_answer
from .pipeline import run_demo

__all__ = ["evaluate_answer", "run_demo"]
__version__ = "0.3.0"
