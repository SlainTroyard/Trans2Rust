cmake_minimum_required(VERSION 3.10.0)
project(Examples)

add_executable(example
  src/main.c
  src/math_utils.c
)

target_include_directories(example PRIVATE src)

