#! /usr/bin/env bash
set -x
cargo build --release
cp ./target/release/libdubins_rust.so ../viewplanning/dubins/dubins_rust.so

