# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## Unreleased

### Added
- Navigate to run page after running manually a pipeline or trigger (#71)
- Add `ky` frontend dependency as HTTP fetch library
- Spin the running icon in the status badge

### Fixed
- Sometimes logs are appended to an existing logs files of previous runs (#131)
- During a pipeline run, logs are streamed to any pipeline run page bug (#130)

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

[0.3.2]: https://github.com/lucafaggianelli/plombery.git/releases/tag/v0.3.2
