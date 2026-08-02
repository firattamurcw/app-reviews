"""The store-agnostic engine: the connection pool, the page-walk ladder, the
protocols the store modules satisfy.

Nothing here knows about the App Store or Google Play; that lives in
``app_reviews.appstore`` and ``app_reviews.googleplay``. Internal; import from
``app_reviews`` instead.
"""
