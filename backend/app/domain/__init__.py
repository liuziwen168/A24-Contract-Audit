ROLES = {"user", "legalReviewer", "riskReviewer", "admin"}
USER_STATUSES = {"active", "disabled"}
CONTRACT_TYPES = {"purchase", "sales", "nda", "outsourcing", "labor", "other"}
CONTRACT_STATUSES = {"uploaded", "reviewing", "reviewed", "failed", "deleted"}
REVIEW_STATUSES = {"pending", "processing", "completed", "failed", "cancelled"}
REVIEW_STAGES = {"aiReview", "legalReview", "riskReview", "completed"}
REVIEW_MODES = {"full", "rulesOnly"}
RISK_LEVELS = {"high", "medium", "low"}
WARNING_STATUSES = {
    "pendingLegal",
    "pendingRisk",
    "active",
    "processing",
    "closed",
    "withdrawn",
    "waived",
}
RISK_TYPES = {
    "unlimitedLiability",
    "excessiveLiquidatedDamages",
    "unilateralTermination",
    "unfairPaymentTerms",
    "unfavorableJurisdiction",
    "missingDisputeResolution",
    "overbroadConfidentiality",
    "missingConfidentiality",
    "missingPerformanceTerm",
    "ambiguousAcceptance",
    "intellectualPropertyUnclear",
    "forceMajeureMissing",
}
