pybind11_add_module(optimized_processing MODULE
    src/optimized_processing.cpp
    src/batch_processor.cpp
    src/parallel_executor.cpp
)

target_include_directories(optimized_processing PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

# Set output directory to match Python package structure
set_target_properties(optimized_processing PROPERTIES
    OUTPUT_NAME _optimized_processing
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}"
)

# Install target if built standalone
install(TARGETS optimized_processing DESTINATION "${CMAKE_CURRENT_SOURCE_DIR}")
