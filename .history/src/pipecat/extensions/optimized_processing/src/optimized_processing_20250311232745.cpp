#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>
#include <vector>
#include <string>

namespace py = pybind11;

#ifdef ENABLE_CUDA
    #include "optimized_processing_cuda.cu"
#endif

// Fast implementation of batched processing using C++
std::vector<float> process_batch(const std::vector<float>& input, int batch_size) {
    std::vector<float> output(input.size());
    
    // Optimize batch processing with parallel algorithm
    #pragma omp parallel for
    for (size_t i = 0; i < input.size(); i++) {
        output[i] = input[i] * 2.0f;  // Example operation
    }
    
    return output;
}

PYBIND11_MODULE(_optimized_processing, m) {
    m.doc() = "Optimized processing extensions for Pipecat";
    m.def("process_batch", &process_batch, "Fast batch processing implementation",
          py::arg("input"), py::arg("batch_size") = 32);
    
    #ifdef ENABLE_CUDA
        m.def("process_batch_cuda", &process_batch_cuda, "Fast batch processing implementation using CUDA",
              py::arg("input"), py::arg("batch_size") = 32);
    #endif
}
