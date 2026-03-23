"""Import all models so SQLAlchemy registers them on Base.metadata."""
from strata_api.db.models.building import Building  # noqa: F401
from strata_api.db.models.entrance import Entrance  # noqa: F401
from strata_api.db.models.unit import Unit  # noqa: F401
from strata_api.db.models.pipeline_run import PipelineRun  # noqa: F401
from strata_api.db.models.listing import (  # noqa: F401
    Listing, ListingUnitMatch, ListingHistory, ListingImage, ListingDocument,
)
