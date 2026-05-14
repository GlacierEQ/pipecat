pybind11_add_module(optimized_processing MODULE
    src/optimized_processing.cpp
    src/batch_processor.cpp
    src/parallel_executor.cpp
)

target_include_directories(optimized_processing PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

# Enable CUDA if available
find_package(CUDA REQUIRED)
if (CUDA_FOUND)
    cuda_add_library(optimized_processing_cuda SHARED src/optimized_processing_cuda.cu)
    target_link_libraries(optimized_processing PRIVATE optimized_processing_cuda)
    target_compile_definitions(optimized_processing PRIVATE "ENABLE_CUDA")
    set_source_files_properties(src/optimized_processing_cuda.cu PROPERTIES CUDA_SEPARABLE_COMPILATION ON)
    
    # Add CUDA flags
    set_target_properties(optimized_processing_cuda PROPERTIES
        CUDA_STANDARD 17
        CUDA_STANDARD_REQUIRED ON
        CUDA_ARCHITECTURES "75;80;86" # Adjust based on target GPUs
    )
    
    # Link CUDA runtime
    target_link_libraries(optimized_processing PRIVATE CUDA::cudart)
endif()

# Set output directory to match Python package structure
set_target_properties(optimized_processing PROPERTIES
    OUTPUT_NAME _optimized_processing
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}"
)

# Install target if built standalone
install(TARGETS optimized_processing DESTINATION "${CMAKE_CURRENT_SOURCE_DIR}")
