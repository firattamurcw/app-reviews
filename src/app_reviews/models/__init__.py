"""The package's data types, one module per group.

Not a re-export surface: import these from ``app_reviews``, which is the whole
public API. Inside the package, import the module that defines the type:

- ``types``: ``Store``, ``Source``, ``ErrorKind``, ``StopReason``, ``Sort``
- ``config``: ``RetryConfig`` and the credential models
- ``review`` / ``page`` / ``result``: what a fetch produces
- ``country``: the storefront enum
- ``metadata``: ``AppMetadata``
"""
