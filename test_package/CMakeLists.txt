cmake_minimum_required(VERSION 2.8.11)
project(test_package)

include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup()

add_executable(${PROJECT_NAME} test_package.c)
if(CMAKE_SYSTEM_NAME STREQUAL Emscripten)
    target_link_libraries(${PROJECT_NAME} turbojpeg)
    set(JS_HELPER "${CMAKE_CURRENT_SOURCE_DIR}/helpers.js")
    set(COMPILE_FLAGS " -Wno-missing-prototypes")
    set(LINK_FLAGS " -s FORCE_FILESYSTEM=1 --pre-js ${JS_HELPER} -Wno-missing-prototypes")
    set_property(TARGET ${PROJECT_NAME} PROPERTY LINK_FLAGS ${LINK_FLAGS})

else()
    target_link_libraries(${PROJECT_NAME} ${CONAN_LIBS})
endif()
set_property(TARGET ${PROJECT_NAME} PROPERTY C_STANDARD 99)

