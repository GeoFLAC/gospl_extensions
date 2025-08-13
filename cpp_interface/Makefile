# Makefile for gospl_extensions C++ interface
#
# This Makefile builds a shared library and C++ driver for interfacing
# with goSPL extensions through Python C API.

# Compiler settings
CXX = g++
CXXFLAGS = -std=c++14 -Wall -Wextra -fPIC -O3

# Python configuration (automatically detected)
PYTHON_VERSION := $(shell python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PYTHON_INCLUDE := $(shell python3 -c "import sys; print(f'-I{sys.prefix}/include/python{sys.version_info.major}.{sys.version_info.minor}')")
PYTHON_LIBS := $(shell python3-config --ldflags --embed 2>/dev/null || python3-config --ldflags)
NUMPY_INCLUDE := $(shell python3 -c "import numpy; print(f'-I{numpy.get_include()}')")

# Include and library flags
INCLUDES = $(PYTHON_INCLUDE) $(NUMPY_INCLUDE)
LIBS = $(PYTHON_LIBS)

# Source files
LIB_SOURCES = gospl_extensions.cpp
DRIVER_SOURCES = enhanced_model_driver.cpp  
TEST_SOURCES = test_interface.cpp

# Output files
LIB_NAME = libgospl_extensions.so
DRIVER_NAME = enhanced_model_driver
TEST_NAME = test_interface

# Default target
all: $(LIB_NAME) $(DRIVER_NAME) $(TEST_NAME) copy_python

# Build shared library
$(LIB_NAME): $(LIB_SOURCES) gospl_extensions.h
	@echo "Building shared library..."
	@echo "Python version: $(PYTHON_VERSION)"
	@echo "Python includes: $(PYTHON_INCLUDE)"
	@echo "NumPy includes: $(NUMPY_INCLUDE)"
	$(CXX) $(CXXFLAGS) $(INCLUDES) -shared -o $(LIB_NAME) $(LIB_SOURCES) $(LIBS)
	@echo "✅ Shared library built: $(LIB_NAME)"

# Build driver executable
$(DRIVER_NAME): $(DRIVER_SOURCES) $(LIB_NAME) gospl_extensions.h
	@echo "Building driver executable..."
	$(CXX) $(CXXFLAGS) $(INCLUDES) -o $(DRIVER_NAME) $(DRIVER_SOURCES) -L. -lgospl_extensions $(LIBS)
	@echo "✅ Driver built: $(DRIVER_NAME)"

# Build test executable
$(TEST_NAME): $(TEST_SOURCES) $(LIB_NAME) gospl_extensions.h
	@echo "Building test executable..."
	$(CXX) $(CXXFLAGS) $(INCLUDES) -o $(TEST_NAME) $(TEST_SOURCES) -L. -lgospl_extensions $(LIBS)
	@echo "✅ Test built: $(TEST_NAME)"

# Copy Python interface files
copy_python:
	@echo "Copying Python interface files..."
	@mkdir -p cpp_interface
	@cp gospl_python_interface.py cpp_interface/
	@touch cpp_interface/__init__.py
	@echo "✅ Python files copied"

# Test the interface
test: $(TEST_NAME) copy_python
	@echo "Running interface tests..."
	@export LD_LIBRARY_PATH=.:$$LD_LIBRARY_PATH && ./$(TEST_NAME)

# Test with actual goSPL (requires config file)
test-gospl: $(DRIVER_NAME) copy_python
	@if [ -f "../examples/input-escarpment.yml" ]; then \
		echo "Running goSPL test..."; \
		export LD_LIBRARY_PATH=.:$$LD_LIBRARY_PATH && ./$(DRIVER_NAME) ../examples/input-escarpment.yml; \
	else \
		echo "❌ Config file not found. Please ensure input-escarpment.yml exists in ../examples/"; \
	fi

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -f $(LIB_NAME) $(DRIVER_NAME) $(TEST_NAME)
	rm -rf cpp_interface
	@echo "✅ Cleaned"

# Install (optional)
install: $(LIB_NAME) $(DRIVER_NAME)
	@echo "Installing..."
	sudo cp $(LIB_NAME) /usr/local/lib/
	sudo cp gospl_extensions.h /usr/local/include/
	sudo cp $(DRIVER_NAME) /usr/local/bin/
	sudo ldconfig
	@echo "✅ Installed"

# Uninstall (optional)
uninstall:
	@echo "Uninstalling..."
	sudo rm -f /usr/local/lib/$(LIB_NAME)
	sudo rm -f /usr/local/include/gospl_extensions.h
	sudo rm -f /usr/local/bin/$(DRIVER_NAME)
	sudo ldconfig
	@echo "✅ Uninstalled"

# Debug information
debug-info:
	@echo "=== Build Configuration ==="
	@echo "CXX: $(CXX)"
	@echo "CXXFLAGS: $(CXXFLAGS)"
	@echo "Python version: $(PYTHON_VERSION)"
	@echo "Python include: $(PYTHON_INCLUDE)"
	@echo "NumPy include: $(NUMPY_INCLUDE)"
	@echo "Python libs: $(PYTHON_LIBS)"
	@echo "==========================="

# Help
help:
	@echo "gospl_extensions C++ Interface Build System"
	@echo ""
	@echo "Targets:"
	@echo "  all          - Build library, driver, and test (default)"
	@echo "  lib          - Build shared library only"
	@echo "  driver       - Build driver executable only"  
	@echo "  test         - Build and run interface tests"
	@echo "  test-gospl   - Run test with actual goSPL simulation"
	@echo "  clean        - Remove build artifacts"
	@echo "  install      - Install to system (requires sudo)"
	@echo "  uninstall    - Remove from system (requires sudo)"
	@echo "  debug-info   - Show build configuration"
	@echo "  help         - Show this help"
	@echo ""
	@echo "Usage examples:"
	@echo "  make                    # Build everything"
	@echo "  make test              # Run basic interface tests"
	@echo "  make test-gospl        # Run with actual goSPL (needs config)"
	@echo "  make clean             # Clean up"

# Individual targets
lib: $(LIB_NAME)
driver: $(DRIVER_NAME)
test-only: $(TEST_NAME)

.PHONY: all clean install uninstall test test-gospl copy_python debug-info help lib driver test-only
