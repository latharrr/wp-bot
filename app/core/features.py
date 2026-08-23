"""The set of dashboard features a super_admin can grant to a 'user' account. Keep this in sync
with the router-level require_feature(...) dependencies in each route module (app/api/deps.py)
and dashboard/lib/features.ts on the frontend."""
AVAILABLE_FEATURES = ["connection", "groups", "keyword_search", "csv_scoring", "export_log"]
