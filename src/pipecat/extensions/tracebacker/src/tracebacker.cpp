#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>
#include <vector>
#include <string>
#include <unordered_map>
#include <chrono>
#include <thread>
#include <mutex>
#include <atomic>

namespace py = pybind11;

// Simple thread-safe trace collector
class TraceCollector {
private:
    struct TraceEntry {
        std::string function;
        std::string filename;
        int line;
        double timestamp;
        double duration;
        std::thread::id thread_id;
    };
    
    std::vector<TraceEntry> traces;
    std::mutex trace_mutex;
    std::atomic<bool> is_active{false};
    
public:
    TraceCollector() = default;
    
    void start() {
        std::lock_guard<std::mutex> lock(trace_mutex);
        traces.clear();
        is_active = true;
    }
    
    void stop() {
        is_active = false;
    }
    
    void add_trace(const std::string& function, 
                   const std::string& filename,
                   int line,
                   double timestamp, 
                   double duration) {
        if (!is_active) return;
        
        std::lock_guard<std::mutex> lock(trace_mutex);
        traces.push_back({
            function,
            filename,
            line,
            timestamp,
            duration,
            std::this_thread::get_id()
        });
    }
    
    std::vector<py::dict> get_traces() {
        std::lock_guard<std::mutex> lock(trace_mutex);
        std::vector<py::dict> result;
        result.reserve(traces.size());
        
        for (const auto& trace : traces) {
            py::dict entry;
            entry["function"] = trace.function;
            entry["filename"] = trace.filename;
            entry["line"] = trace.line;
            entry["timestamp"] = trace.timestamp;
            entry["duration"] = trace.duration;
            entry["thread_id"] = std::hash<std::thread::id>{}(trace.thread_id);
            result.push_back(entry);
        }
        
        return result;
    }
    
    void clear() {
        std::lock_guard<std::mutex> lock(trace_mutex);
        traces.clear();
    }
    
    bool is_tracing() const {
        return is_active;
    }
};

// Global instance
TraceCollector global_collector;

// Trace function execution time
class FunctionTracer {
private:
    std::string function_name;
    std::string filename;
    int line;
    std::chrono::high_resolution_clock::time_point start_time;
    
public:
    FunctionTracer(const std::string& func, const std::string& file, int ln) 
    : function_name(func), filename(file), line(ln) {
        start_time = std::chrono::high_resolution_clock::now();
    }
    
    ~FunctionTracer() {
        auto end_time = std::chrono::high_resolution_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::microseconds>(
            end_time - start_time).count() / 1000000.0;
        
        auto timestamp = std::chrono::duration_cast<std::chrono::microseconds>(
            start_time.time_since_epoch()).count() / 1000000.0;
        
        global_collector.add_trace(function_name, filename, line, timestamp, duration);
    }
};

PYBIND11_MODULE(_tracebacker, m) {
    m.doc() = "TraceBacker: A high-performance profiling and tracing tool for Python";
    
    // Expose the collector API
    m.def("start_tracing", []() { global_collector.start(); }, 
          "Start collecting trace data");
          
    m.def("stop_tracing", []() { global_collector.stop(); }, 
          "Stop collecting trace data");
          
    m.def("get_traces", []() { return global_collector.get_traces(); }, 
          "Get all collected traces");
          
    m.def("clear_traces", []() { global_collector.clear(); }, 
          "Clear all collected traces");
          
    m.def("is_tracing", []() { return global_collector.is_tracing(); }, 
          "Check if tracing is active");
    
    // Function tracer class
    py::class_<FunctionTracer>(m, "FunctionTracer")
        .def(py::init<std::string, std::string, int>(),
             py::arg("function"), py::arg("filename"), py::arg("line"));
    
    // Create a Python decorator for tracing functions
    m.def("trace_function", [](py::function func) {
        return py::cpp_function([func](py::args args, py::kwargs kwargs) {
            std::string func_name = py::str(func.attr("__name__"));
            std::string filename = "<unknown>";
            int line = 0;
            
            // Try to get source info
            if (py::hasattr(func, "__code__")) {
                auto code = func.attr("__code__");
                if (py::hasattr(code, "co_filename")) {
                    filename = py::str(code.attr("co_filename"));
                }
                if (py::hasattr(code, "co_firstlineno")) {
                    line = py::int_(code.attr("co_firstlineno"));
                }
            }
            
            // Create tracer
            FunctionTracer tracer(func_name, filename, line);
            
            // Call the function
            return func(*args, **kwargs);
        });
    }, "Decorator to trace function execution");
}
