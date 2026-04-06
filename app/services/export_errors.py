from __future__ import annotations


class ExportError(Exception):
    """Base class for export-related failures."""


class RendererSelectionError(ExportError):
    pass


class RenderExecutionError(ExportError):
    pass


class ArtifactStorageError(ExportError):
    pass


class ArtifactIntegrityError(ExportError):
    pass


class ArtifactDeliveryError(ExportError):
    pass


class ArtifactAccessDeniedError(ArtifactDeliveryError):
    pass


class ArtifactNotFoundError(ArtifactDeliveryError):
    pass
