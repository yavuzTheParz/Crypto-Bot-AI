# Distributed under the OSI-approved BSD 3-Clause License.  See accompanying
# file Copyright.txt or https://cmake.org/licensing for details.

cmake_minimum_required(VERSION 3.5)

# If CMAKE_DISABLE_SOURCE_CHANGES is set to true and the source directory is an
# existing directory in our source tree, calling file(MAKE_DIRECTORY) on it
# would cause a fatal error, even though it would be a no-op.
if(NOT EXISTS "/mnt/c/Users/yavuz/trading_bot/binapi/build_dataGrapper/_deps/zlib-src")
  file(MAKE_DIRECTORY "/mnt/c/Users/yavuz/trading_bot/binapi/build_dataGrapper/_deps/zlib-src")
endif()
file(MAKE_DIRECTORY
  "/mnt/c/Users/yavuz/trading_bot/binapi/build_dataGrapper/_deps/zlib-build"
  "/mnt/c/Users/yavuz/trading_bot/binapi/build_dataGrapper/_deps/zlib-subbuild/zlib-populate-prefix"
  "/mnt/c/Users/yavuz/trading_bot/binapi/build_dataGrapper/_deps/zlib-subbuild/zlib-populate-prefix/tmp"
  "/mnt/c/Users/yavuz/trading_bot/binapi/build_dataGrapper/_deps/zlib-subbuild/zlib-populate-prefix/src/zlib-populate-stamp"
  "/mnt/c/Users/yavuz/trading_bot/binapi/build_dataGrapper/_deps/zlib-subbuild/zlib-populate-prefix/src"
  "/mnt/c/Users/yavuz/trading_bot/binapi/build_dataGrapper/_deps/zlib-subbuild/zlib-populate-prefix/src/zlib-populate-stamp"
)

set(configSubDirs )
foreach(subDir IN LISTS configSubDirs)
    file(MAKE_DIRECTORY "/mnt/c/Users/yavuz/trading_bot/binapi/build_dataGrapper/_deps/zlib-subbuild/zlib-populate-prefix/src/zlib-populate-stamp/${subDir}")
endforeach()
if(cfgdir)
  file(MAKE_DIRECTORY "/mnt/c/Users/yavuz/trading_bot/binapi/build_dataGrapper/_deps/zlib-subbuild/zlib-populate-prefix/src/zlib-populate-stamp${cfgdir}") # cfgdir has leading slash
endif()
