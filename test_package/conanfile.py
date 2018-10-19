#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conans import ConanFile, CMake, tools, RunEnvironment
import os


class TestPackageConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = "cmake"

    def is_emscripten(self):
        try:
            return self.settings.compiler == 'emcc'
        except:
            return False

    def imports(self):
        self.copy("*.dll", dst="bin", src="bin")
        self.copy("*.so*", dst="bin", src="lib")
        self.copy("*.dylib*", dst="bin", src="lib")

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def test(self):
        img_name = os.path.join(self.source_folder, "testimg.jpg")
        bin_path = os.path.join("bin", "test_package")
        if self.is_emscripten():
            import shutil
            shutil.copy(img_name,'testimg.jpg')
        
            img_name = '/WD/testimg.jpg'
            bin_path = 'node %s.js'%bin_path

        command = "%s %s" % (bin_path, img_name)
        self.run(command, run_environment=True)
