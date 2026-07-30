"""Input records for use cases.

These are the contract between data-source adapters and use cases. They hold
only facts that are independent of any particular source, so a use case never
has to know which provider the data came from, nor how it was encoded.
"""

from yellowmind.application.dto.edition_record import EditionRecord
from yellowmind.application.dto.gc_standing_record import GcStandingRecord
from yellowmind.application.dto.stage_record import StageRecord
from yellowmind.application.dto.stage_result_record import StageResultRecord
from yellowmind.application.dto.startlist_record import StartlistRecord

__all__ = [
    "EditionRecord",
    "GcStandingRecord",
    "StageRecord",
    "StageResultRecord",
    "StartlistRecord",
]
