"""
حزمة إدارة الهياكل والصلاحيات — Management Package
"""
from .organization import GovernanceSystem
from .authority    import ApprovalMatrix
from .decisions    import DecisionEngine

__all__ = ["GovernanceSystem", "ApprovalMatrix", "DecisionEngine"]
