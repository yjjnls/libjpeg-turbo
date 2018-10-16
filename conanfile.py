#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import shutil
import platform

try:
    import conanos.conan.hacks.cmake
except:
    if os.environ.get('EMSCRIPTEN_VERSIONS'):
        raise Exception('Please use pip install devutils to patch conan for emscripten binding !')

from conans import ConanFile, CMake, AutoToolsBuildEnvironment, tools


class LibjpegTurboConan(ConanFile):
    name = "libjpeg-turbo"
    version = "1.5.2"
    description = "SIMD-accelerated libjpeg-compatible JPEG codec library"
    url = "http://github.com/bincrafters/conan-libjpeg-turbo"
    author = "Bincrafters <bincrafters@gmail.com>"
    homepage = "https://libjpeg-turbo.org"
    license = "BSD 3-Clause, ZLIB"
    exports = ["LICENSE.md"]
    exports_sources = ["CMakeLists.txt"]
    generators = "cmake"
    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False],
               "fPIC": [True, False],
               "SIMD": [True, False],
               "arithmetic_encoder": [True, False],
               "arithmetic_decoder": [True, False],
               "libjpeg7_compatibility": [True, False],
               "libjpeg8_compatibility": [True, False],
               "mem_src_dst": [True, False],
               "turbojpeg": [True, False],
               "java": [True, False],
               "enable12bit": [True, False]}
    default_options = "shared=False",\
                      "fPIC=True",\
                      "SIMD=True",\
                      "arithmetic_encoder=True",\
                      "arithmetic_decoder=True",\
                      "libjpeg7_compatibility=True",\
                      "libjpeg8_compatibility=True",\
                      "mem_src_dst=True",\
                      "turbojpeg=True",\
                      "java=False",\
                      "enable12bit=False"
    source_subfolder = "source_subfolder"

    def is_emscripten(self):
        try:
            return self.settings.compiler == 'emcc'
        except:
            return False

    def configure(self):
        del self.settings.compiler.libcxx

        if self.settings.os == "Windows":
            self.requires.add("nasm/2.13.01@conan/stable", private=True)
        if self.settings.compiler == "Visual Studio":
            self.options.remove("fPIC")

        if self.is_emscripten():
            del self.settings.os
            del self.settings.arch
            self.options.remove("fPIC")
            self.options.remove("shared")
            self.options.remove("SIMD")

    def source(self):
        tools.get("http://downloads.sourceforge.net/project/libjpeg-turbo/%s/libjpeg-turbo-%s.tar.gz" % (self.version, self.version))
        os.rename("libjpeg-turbo-%s" % self.version, self.source_subfolder)
        os.rename(os.path.join(self.source_subfolder, "CMakeLists.txt"),
                  os.path.join(self.source_subfolder, "CMakeLists_original.txt"))
        shutil.copy("CMakeLists.txt",
                    os.path.join(self.source_subfolder, "CMakeLists.txt"))

    def build_configure(self):
        prefix = os.path.abspath(self.package_folder)
        with tools.chdir(self.source_subfolder):
            # works for unix and mingw environments
            env_build = AutoToolsBuildEnvironment(self, win_bash=self.settings.os == 'Windows' and
                                                  platform.system() == 'Windows')
            env_build.fpic = self.options.fPIC
            if self.settings.os == 'Windows':
                prefix = tools.unix_path(prefix)
            args = ['--prefix=%s' % prefix]
            if self.options.shared:
                args.extend(['--disable-static', '--enable-shared'])
            else:
                args.extend(['--disable-shared', '--enable-static'])
            args.append('--with-jpeg7' if self.options.libjpeg7_compatibility else '--without-jpeg7')
            args.append('--with-jpeg8' if self.options.libjpeg8_compatibility else '--without-jpeg8')
            args.append('--with-arith-enc' if self.options.arithmetic_encoder else '--without-arith-enc')
            args.append('--with-arith-dec' if self.options.arithmetic_decoder else '--without-arith-dec')
            args.append('--with-turbojpeg' if self.options.turbojpeg else '--without-turbojpeg')
            args.append('--with-mem-srcdst' if self.options.mem_src_dst else '--without-mem-srcdst')
            args.append('--with-12bit' if self.options.enable12bit else '--without-12bit')
            args.append('--with-java' if self.options.java else '--without-java')
            args.append('--with-simd' if self.options.SIMD else '--without-simd')

            if self.settings.os == "Macos":
                tools.replace_in_file("configure",
                                      r'-install_name \$rpath/\$soname',
                                      r'-install_name \$soname')

            env_build.configure(args=args)
            env_build.make()
            env_build.make(args=['install'])

    def build_cmake(self):

        # fix cmake that gather install targets from the wrong dir
        for bin_program in ['tjbench', 'cjpeg', 'djpeg', 'jpegtran']:
            tools.replace_in_file("%s/CMakeLists_original.txt" % self.source_subfolder,
                                  '${CMAKE_CURRENT_BINARY_DIR}/' + bin_program + '-static.exe',
                                  '${CMAKE_CURRENT_BINARY_DIR}/bin/' + bin_program + '-static.exe')


        if self.is_emscripten():
            
            tools.replace_in_file("%s/CMakeLists_original.txt" % self.source_subfolder,
                                  'message(FATAL_ERROR "Platform not supported by this build system.  Use autotools instead.")',
                                  '#message(FATAL_ERROR "Platform not supported by this build system.  Use autotools instead.")')

            tools.replace_in_file("%s/CMakeLists_original.txt" % self.source_subfolder,
                                  'set(COMPILE_FLAGS "-DGIF_SUPPORTED -DPPM_SUPPORTED -DUSE_SETMODE")',
                                  'set(COMPILE_FLAGS "-DPPM_SUPPORTED")')

            tools.replace_in_file("%s/CMakeLists_original.txt" % self.source_subfolder,
                                  'set(COMPILE_FLAGS "-DBMP_SUPPORTED -DGIF_SUPPORTED -DPPM_SUPPORTED -DTARGA_SUPPORTED -DUSE_SETMODE")',
                                  'set(COMPILE_FLAGS "-DBMP_SUPPORTED -DPPM_SUPPORTED -DTARGA_SUPPORTED")')
            #sharedlib
            tools.replace_in_file("%s/sharedlib/CMakeLists.txt" % self.source_subfolder,
                        'set_property(TARGET jpegtran PROPERTY COMPILE_FLAGS "-DUSE_SETMODE")','\n'
                        +'set_property(TARGET cjpeg PROPERTY LINK_FLAGS ${LINK_FLAGS})\n'
                        +'set_property(TARGET djpeg PROPERTY LINK_FLAGS ${LINK_FLAGS})\n'
                        +'set_property(TARGET jpegtran PROPERTY LINK_FLAGS ${LINK_FLAGS})\n')

            tools.replace_in_file("%s/sharedlib/CMakeLists.txt" % self.source_subfolder,
                        'add_executable(cjpeg ../cjpeg.c ../cdjpeg.c ../rdgif.c ../rdppm.c','\n'
                        +'set(JS_HELPER "${CMAKE_CURRENT_SOURCE_DIR}/helpers.js")\n'
                        +'set(COMPILE_FLAGS "-DBMP_SUPPORTED -DPPM_SUPPORTED -Wno-missing-prototypes")\n'
                        +'set(LINK_FLAGS " -s FORCE_FILESYSTEM=1 --pre-js ${JS_HELPER} -Wno-missing-prototypes")\n'
                        +'if(NOT WITH_12BIT)\n'
                        +'  set(COMPILE_FLAGS "${COMPILE_FLAGS} -DTARGA_SUPPORTED")\n'
                        +'endif()\n')

            shutil.copy("helpers/sharedlib/helper.js",
                    os.path.join(self.source_subfolder, "sharedlib/helper.js"))

            for name in ['cjpeg','djpeg','jpegtran','md5cmp','tjunittest']:
                shutil.copy("helpers/%s"%name, name)



            
        else:

            tools.replace_in_file("%s/CMakeLists_original.txt" % self.source_subfolder,
                                  'add_test(tjunittest${suffix} tjunittest${suffix})',
                                  'add_test(tjunittest${suffix} bin/tjunittest${suffix})')

            tools.replace_in_file("%s/CMakeLists_original.txt" % self.source_subfolder,
                                  'add_test(tjunittest${suffix}-alloc tjunittest${suffix} -alloc)',
                                  'add_test(tjunittest${suffix}-alloc bin/tjunittest${suffix} -alloc)')

            tools.replace_in_file("%s/CMakeLists_original.txt" % self.source_subfolder,
                                  'add_test(tjunittest${suffix}-yuv tjunittest${suffix} -yuv)',
                                  'add_test(tjunittest${suffix}-yuv bin/tjunittest${suffix} -yuv)')

            tools.replace_in_file("%s/CMakeLists_original.txt" % self.source_subfolder,
                                  'add_test(tjunittest${suffix}-yuv-alloc tjunittest${suffix} -yuv -alloc)',
                                  'add_test(tjunittest${suffix}-yuv-alloc bin/tjunittest${suffix} -yuv -alloc)')
    
            tools.replace_in_file("%s/CMakeLists_original.txt" % self.source_subfolder,
                                  'add_test(tjunittest${suffix}-yuv-nopad tjunittest${suffix} -yuv -noyuvpad)',
                                  'add_test(tjunittest${suffix}-yuv-nopad bin/tjunittest${suffix} -yuv -noyuvpad)')
    

        tools.replace_in_file("%s/CMakeLists_original.txt" % self.source_subfolder,
                                  '# These tests are carefully chosen to provide full coverage of as many of the','\n'
                                 +'if(CMAKE_SYSTEM_NAME STREQUAL Emscripten)\n'
                                 +'  set(dir "" )\n'
                                 +'  set(MD5CMP "md5cmp")\n'
                                 +'  set(MD5_JPEG_3x2_FLOAT_PROG 9bca803d2042bd1eb03819e2bf92b3e5)\n'
                                 +'  set(MD5_PPM_3x2_FLOAT       f6bfab038438ed8f5522fbd33595dcdc)\n'
                                 +'else()\n'
                                 +'  set(dir "bin/" )\n'
                                 +'  set(MD5CMP "bin/md5cmp")\n'
                                 +'endif()\n'                                 
                                 +'# These tests are carefully chosen to provide full coverage of as many of the'
                                  )
        
        

        cmake = CMake(self)
        cmake.definitions['ENABLE_STATIC'] = not self.options.shared
        cmake.definitions['ENABLE_SHARED'] = self.options.shared
        cmake.definitions['WITH_SIMD'] = False if self.is_emscripten() else self.options.SIMD
        cmake.definitions['WITH_ARITH_ENC'] = self.options.arithmetic_encoder
        cmake.definitions['WITH_ARITH_DEC'] = self.options.arithmetic_decoder
        cmake.definitions['WITH_JPEG7'] = self.options.libjpeg7_compatibility
        cmake.definitions['WITH_JPEG8'] = self.options.libjpeg8_compatibility
        cmake.definitions['WITH_MEM_SRCDST'] = self.options.mem_src_dst
        cmake.definitions['WITH_TURBOJPEG'] = self.options.turbojpeg
        cmake.definitions['WITH_JAVA'] = self.options.java
        cmake.definitions['WITH_12BIT'] = self.options.enable12bit
        cmake.configure(source_dir=self.source_subfolder)
        cmake.build()
        cmake.test()
        cmake.install()

    def build(self):
        if self.is_emscripten() or self.settings.compiler == "Visual Studio":
            self.build_cmake()
        else:
            self.build_configure()

    def package(self):
        # remove unneeded directories
        shutil.rmtree(os.path.join(self.package_folder, 'share', 'man'), ignore_errors=True)
        shutil.rmtree(os.path.join(self.package_folder, 'share', 'doc'), ignore_errors=True)
        shutil.rmtree(os.path.join(self.package_folder, 'doc'), ignore_errors=True)

        # remove binaries
        for bin_program in ['cjpeg', 'djpeg', 'jpegtran', 'tjbench', 'wrjpgcom', 'rdjpgcom']:
            for ext in ['', '.exe','.js']:
                try:
                    os.remove(os.path.join(self.package_folder, 'bin', bin_program+ext))
                except:
                    pass

        self.copy("license*", src=self.source_subfolder, dst="licenses", ignore_case=True, keep_path=False)
        # Copying generated header
        if self.settings.compiler == "Visual Studio":
            self.copy("jconfig.h", dst="include", src=".")

    def package_info(self):
        if self.is_emscripten():
            self.cpp_info.libs = ['jpeg', 'turbojpeg']            
        elif self.settings.compiler == "Visual Studio":
            if self.options.shared:
                self.cpp_info.libs = ['jpeg', 'turbojpeg']
            else:
                self.cpp_info.libs = ['jpeg-static', 'turbojpeg-static']
        else:
            self.cpp_info.libs = ['jpeg', 'turbojpeg']
