#!/bin/sh
# Build TTY simulators from an official sim tree after applying the HCL patch.
set -eu
if [ "$#" -ne 2 ]; then
  echo "Usage: sh build_y86_variants.sh /path/to/sim /path/to/build-output" >&2
  exit 2
fi
sim_tree=$(cd "$1" && pwd)
mkdir -p "$2"
build_output=$(cd "$2" && pwd)
cc_bin=${CC:-clang}
make -C "$sim_tree/misc" CC="$cc_bin" LEXLIB=-ll 'LCFLAGS=-O1 -std=gnu89' 'CFLAGS=-Wall -O2 -fcommon -std=gnu89' all
build_variant() {
  exercise_number=$1
  processor=$2
  template=$3
  source_program=$4
  "$sim_tree/misc/hcl2c" -n "ex4-$exercise_number" < "$sim_tree/$processor/$template.hcl" > "$build_output/ex4-$exercise_number.c"
  "$cc_bin" -Wall -O2 -fcommon -std=gnu89 -I"$sim_tree/misc" -I"$sim_tree/$processor" \
    -o "$build_output/ex4-$exercise_number" "$sim_tree/$processor/$source_program.c" \
    "$build_output/ex4-$exercise_number.c" "$sim_tree/misc/isa.c" -lm
}
build_variant 52 seq seq-full ssim
build_variant 53 pipe pipe-nobypass psim
build_variant 54 pipe pipe-full psim
build_variant 55 pipe pipe-nt psim
build_variant 56 pipe pipe-btfnt psim
build_variant 57 pipe pipe-lf psim
build_variant 58 pipe pipe-1w psim
