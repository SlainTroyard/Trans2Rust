FROM debian:12

ADD docker/sources.list /etc/apt
RUN apt update
RUN apt install -y cmake ninja-build clang build-essential
COPY . /app
WORKDIR /app
RUN mkdir build
RUN cmake -GNinja -DCMAKE_EXPORT_COMPILE_COMMANDS=On -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++ -S /app -B /app/build
CMD ["bash"]
