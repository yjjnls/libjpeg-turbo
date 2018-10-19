cmake_minimum_required(VERSION 2.8.12)

project(cmake_wrapper)

include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup()

if(CMAKE_SYSTEM_NAME STREQUAL Emscripten)
  add_definitions(-DSIZEOF_SIZE_T=4)
endif()

include(CMakeLists_original.txt)
