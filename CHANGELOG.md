# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-08-09

### Added
- Initial implementation of `DataDrivenTectonics` extension
- Comprehensive test suite with pytest integration
- Basic and advanced usage examples
- Proper Python packaging with pyproject.toml
- CSV data loading example
- Time-dependent velocity field demonstration
- Standalone test runner for environments without pytest
- Complete documentation and usage examples
- **Conda environment requirement**: Must activate `gospl` conda environment

### Requirements
- **Conda Environment**: The `gospl` conda environment must be activated before using this extension
- goSPL installation with Fortran extensions available in the conda environment

### Features
- K-nearest neighbor velocity interpolation with inverse distance weighting
- Support for both semi-Lagrangian and finite-volume advection schemes
- Robust handling of edge cases (coincident nodes, empty data)
- Time-dependent velocity field support
- MPI-safe implementation
- Configurable interpolation parameters (k, power)

### Documentation
- Comprehensive README with installation and usage instructions
- Example scripts with detailed comments
- Test coverage documentation
- Project structure overview
- Contributing guidelines
