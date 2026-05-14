pybind11_add_module(tracebacker MODULE
    src/tracebacker.cpp
    src/call_stack.cpp
    src/performance_tracking.cpp
)

target_include_directories(tracebacker PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

# Set output directory to match Python package structure
set_target_properties(tracebacker PROPERTIES
    OUTPUT_NAME _tracebacker
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}"
)

# Add OpenMP for parallel tracing
if(OpenMP_CXX_FOUND)
    target_link_libraries(tracebacker PRIVATE OpenMP::OpenMP_CXX)
endif()

# Install target if built standalone
install(TARGETS tracebacker DESTINATION "${CMAKE_CURRENT_SOURCE_DIR}")
