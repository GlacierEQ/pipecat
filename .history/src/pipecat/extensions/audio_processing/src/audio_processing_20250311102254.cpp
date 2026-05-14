#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <vector>
#include <cmath>

namespace py = pybind11;

// Optimized audio processing functions
py::array_t<float> apply_gain(py::array_t<float> audio, float gain) {
    auto r = audio.unchecked<1>();
    auto result = py::array_t<float>(r.shape(0));
    auto result_ptr = result.mutable_unchecked<1>();
    
    for (size_t i = 0; i < r.shape(0); i++) {
        result_ptr(i) = r(i) * gain;
    }
    
    return result;
}

PYBIND11_MODULE(_audio_processing, m) {
    m.doc() = "Optimized audio processing extensions for Pipecat";
    m.def("apply_gain", &apply_gain, "Apply gain to audio signal",
          py::arg("audio"), py::arg("gain") = 1.0f);
}
