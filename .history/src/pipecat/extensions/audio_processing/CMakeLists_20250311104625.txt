pybind11_add_module(audio_processing MODULE
    src/audio_processing.cpp
    src/resampler.cpp
    src/spectral_features.cpp
)

# Find system dependencies for audio processing
find_package(FFTW3 REQUIRED)
target_link_libraries(audio_processing PRIVATE FFTW3::FFTW3)

target_include_directories(audio_processing PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

# Set output directory to match Python package structure
set_target_properties(audio_processing PROPERTIES
    OUTPUT_NAME _audio_processing
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}"
)

# Install target if built standalone
install(TARGETS audio_processing DESTINATION "${CMAKE_CURRENT_SOURCE_DIR}")
