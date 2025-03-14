#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <vector>
#include <stack>
#include <string>
#include <unordered_map>
#include <thread>
#include <mutex>

namespace py = pybind11;

// Thread-local call stack tracking
class CallStackTracker {
private:
    struct CallFrame {
        std::string function;
        std::string module;
        int line;
        double enter_time;
    };

    // Thread-local storage for call stacks
    static thread_local std::stack<CallFrame> call_stack;
    
    // Global registry of trackers
    static std::unordered_map<std::thread::id, CallStackTracker*> trackers;
    static std::mutex trackers_mutex;

public:
    CallStackTracker() {
        std::lock_guard<std::mutex> lock(trackers_mutex);
        trackers[std::this_thread::get_id()] = this;
    }
    
    ~CallStackTracker() {
        std::lock_guard<std::mutex> lock(trackers_mutex);
        trackers.erase(std::this_thread::get_id());
    }

    // Push a new frame to the call stack
    void push_frame(const std::string& function, const std::string& module, int line, double time) const {        call_stack.push({function, module, line, time});
    }
    
    // Pop the top frame and return its info
    std::tuple<std::string, std::string, int, double> pop_frame() {
        if (call_stack.empty()) {
            return std::make_tuple("", "", 0, 0.0);
        }
        
        auto frame = call_stack.top();
        call_stack.pop();
        
        return std::make_tuple(frame.function, frame.module, frame.line, frame.enter_time);
    }
    
    // Get the current call depth
    int get_depth() const {
        return static_cast<int>(call_stack.size());
    }
    
    // Get the full call stack
    std::vector<std::tuple<std::string, std::string, int>> get_stack() const {
        std::vector<std::tuple<std::string, std::string, int>> result;
        
        // We need to copy the stack to avoid modifying it
        auto stack_copy = call_stack;
        while (!stack_copy.empty()) {
            const auto& frame = stack_copy.top();
            result.push_back(std::make_tuple(frame.function, frame.module, frame.line));
            stack_copy.pop();
        }
        
        return result;
    }
    
    // Get tracker for the current thread
    static CallStackTracker* get_thread_tracker() {
        std::lock_guard<std::mutex> lock(trackers_mutex);
        auto it = trackers.find(std::this_thread::get_id());
        if (it != trackers.end()) {
            return it->second;
        }
        return nullptr;
    }
};

// Initialize static members
thread_local std::stack<CallStackTracker::CallFrame> CallStackTracker::call_stack;
std::unordered_map<std::thread::id, CallStackTracker*> CallStackTracker::trackers;
std::mutex CallStackTracker::trackers_mutex;

// Bind the CallStackTracker to Python
void init_call_stack(py::module& m) {
    py::class_<CallStackTracker>(m, "CallStackTracker")
        .def(py::init<>())
        .def("push_frame", &CallStackTracker::push_frame, 
             py::arg("function"), py::arg("module"), py::arg("line"), py::arg("time"))
        .def("pop_frame", &CallStackTracker::pop_frame)
        .def("get_depth", &CallStackTracker::get_depth)
        .def("get_stack", &CallStackTracker::get_stack)
        .def_static("get_thread_tracker", &CallStackTracker::get_thread_tracker,
                   py::return_value_policy::reference);
}
