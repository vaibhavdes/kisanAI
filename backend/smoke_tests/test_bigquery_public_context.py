from common import print_ok, require_package

require_package("google.cloud.bigquery", "pip install -r requirements.txt")

from app.models.schemas import GovernmentDataContextRequest
from app.services.bigquery_public_data_service import BigQueryPublicDataService


context = BigQueryPublicDataService().build_context(
    GovernmentDataContextRequest(
        state="Andhra Pradesh",
        district="Guntur",
        crop="chilli",
        season="kharif",
        month=7,
    )
)

print_ok(
    "BigQuery public-data context queried. "
    f"Missing sources: {', '.join(context.missing_sources) or 'none'}"
)
