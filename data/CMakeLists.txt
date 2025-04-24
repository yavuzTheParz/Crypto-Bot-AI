cmake_minimum_required(VERSION 3.10)
project(dataGrapper)

# Set the C++ standard
set(CMAKE_CXX_STANDARD 17)

# Add CPR and JSON dependencies
find_package(cpr REQUIRED)
find_package(nlohmann_json REQUIRED)
find_package(OpenSSL REQUIRED)

# Add the executable
add_executable(dataGrapper dataGrapper.cpp)
target_link_libraries(dataGrapper
    PRIVATE
    cpr::cpr
    nlohmann_json::nlohmann_json
    OpenSSL::SSL
    OpenSSL::Crypto
)
