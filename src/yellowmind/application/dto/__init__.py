"""Input records for use cases.

These are the contract between data-source adapters and use cases. They hold
only facts that are independent of any particular source, so a use case never
has to know which provider the data came from, nor how it was encoded.
"""

from yellowmind.application.dto.edition_record import EditionRecord

__all__ = ["EditionRecord"]
