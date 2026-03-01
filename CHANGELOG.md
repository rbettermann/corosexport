# Changelog

## [0.1.2] - 2025-03-01

### Fixed
- Activity list pagination - now correctly iterates over all pages instead of only the first page ([#2](https://github.com/rbettermann/corosexport/pull/2))

## [0.1.1] - 2025-02-22

### Added
- PyPI publishing workflow for automated releases

## [0.1.0] - 2025-02-17

### Added
- Initial release of Corosexport
- Command-line tool (`coros-backup`) for backing up Coros activities
- Python library API for programmatic access
- Authentication with Coros Training Hub
- Export activities in multiple formats: FIT, TCX, GPX, KML, CSV
- Incremental backup support with state tracking
- Activity metadata export as JSON
- Support for Python 3.9+
- Cross-platform support (macOS, Linux, Windows)
- Configurable backup directory and export formats
- Verbose logging option for debugging
- Email and password authentication
