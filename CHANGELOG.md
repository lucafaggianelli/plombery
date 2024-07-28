# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased]

### Added
- Link to REST API docs in settings menu
- Add download task data button in data view dialog (close #46)
- Add `python-socketio` dependency
- Add support to Pydantic's `SecretStr` input types (by @flashdagger)

### Fixed
- Improve task data visualization (#257)
- Check data file paths before accessing them
- Fixed boolean parameter input when default is True (by @flashdagger)
- Fix connection with non sqlite db (#392) (by @PierrickBrun)

### Changed
- Migrated plain websocket to SocketIO for improved communication stability
- (internal): pipeline HTTP run url is now `/pipelines/{pipeline_id}/run`
- (internal): updated frontend dependencies

### Removed
- Removed python `websockets` dependency

## [0.4.1] - 2023-10-11

### Fixed
- No pipelines message appearing when pipelines where there
- Fix the traceback info dialog (fix #229)

## [0.4.0] - 2023-10-06
### Added
- Navigate to run page after running manually a pipeline or trigger (#71)
- Add `ky` frontend dependency as HTTP fetch library
- Spin the running icon in the status badge
- Add a live logs indicator to the logs viewer
- Add duration timer to run page
- Automatic scroll lock for the log stream
- Show UTC datetime when hovering a datetime
- Implement Dark mode and theme switcher
- Create a settings menu (#157)
- (docs): added recipe SSL certificate check
- (docs): document pipelines and tasks (#110)
- Improve manual run form
- (docs): add codespaces config to run demo
- Add `allowed_origins` configuration to explicitly set CORS headers
- Add HTML template for email notifications (#52)
- Add in-app messages for new users to get started (#38)
- Use skeleton loaders during data fetch

### Fixed
- Sometimes logs are appended to an existing logs files of previous runs (#131)
- During a pipeline run, logs are streamed to any pipeline run page bug (#130)
- Check task function signature before calling it (#154)
- Fix link arrow decoration in scrolling containers
- Fix table sticky headers
- Show absolute URL in trigger run hook (#82)
- Re-implement dialog to fix several bugs (#81)
- Validate parameters in pipeline run endpoint
- Derive correct WebSocket scheme from the HTTP URL scheme
- Fix context in sync tasks functions (#153)
- Show validation errors in manual run form dialog (#192)

### Changed
- Migrate tremor to v3
- Update frontend deps
- (breaking) updated FastAPI to v0.103 (#144)
- updated authlib for compatibility with fastapi
- (internal): refactored FastAPI backend (#159)
- (breaking): auth redirect url is now `/auth/redirect`
- (breaking): all auth endpoints are prefixed with `/auth`
- (breaking): `pipelines/`, `runs/` and `ws/` endpoints now have trailing slashes
- (breaking): updated pydantic to v2
- (breaking): `Trigger.params` accepts a `BaseModel` instance, not a dict
- (breaking): By default CORS headers allow_origins is set to `*`

### Removed
- Remove `server_url` configuration as unused

## [0.3.2] - 2023-06-20
### Added
- Add next fire time to pipelines and triggers (#27)
- show run time in runs list (#129)

### Changed
- Save times with UTC timezone (#132)

### Fixed
- change taskrun duration from positive to non-negative (#128)
- specify button type when in form to avoid submit (#133)
- Fix the run pipeline dialog open/close logic
- Show pipeline name in runs list (#127)

[Unreleased]: https://github.com/lucafaggianelli/mario-pype/compare/v0.4.1...HEAD
[0.4.1]: https://github.com/lucafaggianelli/mario-pype/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/lucafaggianelli/mario-pype/compare/v0.3.2...v0.4.0
[0.3.2]: https://github.com/lucafaggianelli/plombery.git/releases/tag/v0.3.2
