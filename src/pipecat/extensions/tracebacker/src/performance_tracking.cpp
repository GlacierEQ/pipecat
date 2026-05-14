#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>
#include <unordered_map>
#include <string>
#include <chrono>
#include <mutex>
#include <vector>
#include <algorithm>
#include <numeric>
#include <limits>

namespace py = pybind11;

class PerformanceTracker {
private:
    struct FunctionStats {
        std::string name;
        uint64_t call_count = 0;
        double total_time = 0.0;
        double min_time = std::numeric_limits<double>::max();
        double max_time = 0.0;
        std::vector<double> samples;
        bool collecting_samples = false;
        size_t max_samples = 100;
    };
    
    std::unordered_map<std::string, FunctionStats> stats;
    std::mutex stats_mutex;
    bool enabled = true;
    
public:
    PerformanceTracker() = default;
    
    void enable() {
        enabled = true;
    }
    
    void disable() {
        enabled = false;
    }
    
    bool is_enabled() const {
        return enabled;
    }
    
    void record_function_call(const std::string& name, double execution_time) {
        if (!enabled) return;
        
        std::lock_guard<std::mutex> lock(stats_mutex);
        
        auto& func_stats = stats[name];
        func_stats.name = name;
        func_stats.call_count++;
        func_stats.total_time += execution_time;
        func_stats.min_time = std::min(func_stats.min_time, execution_time);
        func_stats.max_time = std::max(func_stats.max_time, execution_time);
        
        if (func_stats.collecting_samples) {
            func_stats.samples.push_back(execution_time);
            if (func_stats.samples.size() > func_stats.max_samples) {
                func_stats.samples.erase(func_stats.samples.begin());
            }
        }
    }
    
    void enable_sampling(const std::string& name, size_t max_samples = 100) {
        std::lock_guard<std::mutex> lock(stats_mutex);
        
        auto& func_stats = stats[name];
        func_stats.collecting_samples = true;
        func_stats.max_samples = max_samples;
        func_stats.samples.reserve(max_samples);
    }
    
    void disable_sampling(const std::string& name) {
        std::lock_guard<std::mutex> lock(stats_mutex);
        
        auto it = stats.find(name);
        if (it != stats.end()) {
            it->second.collecting_samples = false;
        }
    }
    
    py::dict get_stats() const {
        std::lock_guard<std::mutex> lock(stats_mutex);
        
        py::dict result;
        
        for (const auto& [name, func_stats] : stats) {
            py::dict stat_dict;
            stat_dict["name"] = func_stats.name;
            stat_dict["call_count"] = func_stats.call_count;
            stat_dict["total_time"] = func_stats.total_time;
            stat_dict["min_time"] = func_stats.min_time == std::numeric_limits<double>::max() ? 0.0 : func_stats.min_time;
            stat_dict["max_time"] = func_stats.max_time;
            
            if (func_stats.call_count > 0) {
                stat_dict["avg_time"] = func_stats.total_time / func_stats.call_count;
            } else {
                stat_dict["avg_time"] = 0.0;
            }
            
            if (func_stats.collecting_samples && !func_stats.samples.empty()) {
                stat_dict["samples"] = func_stats.samples;
                
                // Calculate percentiles
                if (func_stats.samples.size() >= 2) {
                    std::vector<double> sorted_samples = func_stats.samples;
                    std::sort(sorted_samples.begin(), sorted_samples.end());
                    
                    size_t p50_idx = sorted_samples.size() / 2;
                    size_t p90_idx = sorted_samples.size() * 9 / 10;
                    size_t p95_idx = sorted_samples.size() * 95 / 100;
                    size_t p99_idx = sorted_samples.size() * 99 / 100;
                    
                    stat_dict["p50"] = sorted_samples[p50_idx];
                    stat_dict["p90"] = sorted_samples[p90_idx];
                    stat_dict["p95"] = sorted_samples[p95_idx];
                    stat_dict["p99"] = sorted_samples[p99_idx];
                }
            }
            
            result[py::str(name)] = stat_dict;
        }
        
        return result;
    }
    
    void clear_stats() {
        std::lock_guard<std::mutex> lock(stats_mutex);
        stats.clear();
    }
    
    void clear_stats_for(const std::string& name) {
        std::lock_guard<std::mutex> lock(stats_mutex);
        stats.erase(name);
    }
    
    // Calculate simple moving average for a function
    py::array_t<double> calculate_moving_average(const std::string& name, size_t window_size = 5) {
        std::lock_guard<std::mutex> lock(stats_mutex);
        
        auto it = stats.find(name);
        if (it == stats.end() || it->second.samples.size() < window_size) {
            return py::array_t<double>(0);
        }
        
        const auto& samples = it->second.samples;
        size_t result_size = samples.size() - window_size + 1;
        auto result = py::array_t<double>(result_size);
        auto result_ptr = result.mutable_data();
        
        for (size_t i = 0; i < result_size; ++i) {
            double sum = 0.0;
            for (size_t j = 0; j < window_size; ++j) {
                sum += samples[i + j];
            }
            result_ptr[i] = sum / window_size;
        }
        
        return result;
    }
};

// Global instance for easy access from Python
static PerformanceTracker global_tracker;

void init_performance_tracking(py::module& m) {
    // Bind the PerformanceTracker class
    py::class_<PerformanceTracker>(m, "PerformanceTracker")
        .def(py::init<>())
        .def("enable", &PerformanceTracker::enable)
        .def("disable", &PerformanceTracker::disable)
        .def("is_enabled", &PerformanceTracker::is_enabled)
        .def("record_function_call", &PerformanceTracker::record_function_call,
             py::arg("name"), py::arg("execution_time"))
        .def("enable_sampling", &PerformanceTracker::enable_sampling,
             py::arg("name"), py::arg("max_samples") = 100)
        .def("disable_sampling", &PerformanceTracker::disable_sampling,
             py::arg("name"))
        .def("get_stats", &PerformanceTracker::get_stats)
        .def("clear_stats", &PerformanceTracker::clear_stats)
        .def("clear_stats_for", &PerformanceTracker::clear_stats_for,
             py::arg("name"))
        .def("calculate_moving_average", &PerformanceTracker::calculate_moving_average,
             py::arg("name"), py::arg("window_size") = 5);
    
    // Add functions to access the global instance
    m.def("enable_tracking", []() { global_tracker.enable(); },
          "Enable global performance tracking");
    m.def("disable_tracking", []() { global_tracker.disable(); },
          "Disable global performance tracking");
    m.def("is_tracking_enabled", []() { return global_tracker.is_enabled(); },
          "Check if global performance tracking is enabled");
    m.def("record_function", 
          [](const std::string& name, double execution_time) {
              global_tracker.record_function_call(name, execution_time);
          },
          "Record a function call with execution time",
          py::arg("name"), py::arg("execution_time"));
    m.def("enable_function_sampling",
          [](const std::string& name, size_t max_samples = 100) {
              global_tracker.enable_sampling(name, max_samples);
          },
          "Enable sampling for a function",
          py::arg("name"), py::arg("max_samples") = 100);
    m.def("disable_function_sampling",
          [](const std::string& name) {
              global_tracker.disable_sampling(name);
          },
          "Disable sampling for a function",
          py::arg("name"));
    m.def("get_performance_stats", []() { return global_tracker.get_stats(); },
          "Get all performance statistics");
    m.def("clear_performance_stats", []() { global_tracker.clear_stats(); },
          "Clear all performance statistics");
    m.def("get_moving_average",
          [](const std::string& name, size_t window_size = 5) {
              return global_tracker.calculate_moving_average(name, window_size);
          },
          "Calculate moving average for a function",
          py::arg("name"), py::arg("window_size") = 5);
}
