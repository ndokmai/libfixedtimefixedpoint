#!/usr/bin/env python
import math

# This file generates C code to print a fixed point number.
#
# Printing must be constant time, and we need to support variable-sized integer
# and fraction fields (as long as they add to 62).
#
# Strategy:
#
# Each binary fixed-point number has exactly one decimal expansion, with a fixed
# number of non-zero digits. Also, the binary number can be considered as the
# sum of each of the numbers represented by each of its bits.
#
# We're going to exploit these facts. First, we calculate the largest number of decimal
# digits that a given fixed-point format (N intbits, 62-N fracbits) can generate:
#
#   integer digits = ceil( log_10 ( 2^intbits ) )
#   fractional digits = fracbits
#   total size = integer digits + fractional digits + 2 (sign and decimal point)
#
# Now, we start generating at the absolute smallest decimal digit. By the
# decimal expansion of 2^-i, only one bit (the 0th) can contribute anything
# different than 0 to this deciaml digit. So, compute this final digit based on
# the last bit.
#
# Moving up one decimal spot, two bits can add their value. Compute this sum,
# but remember that we might have carry from the previous digit.
#
# Continue in this manner, producing the decimal digit for each location, until
# the entire number is printed.
#
# To support printing "NaN" and "+Inf", etc., add a term to the polynomial,
# which multiplies by 0 if an exceptional state, zeroing out the normal
# computation, and adding back in a " "  if necessary.

#TODO: read these from base.h
int_bits  = 8
frac_bits = 31
flag_bits = 2

number_bits = int_bits + frac_bits

# characters in the integer is given by the base 10 log of the maximum number
int_chars = int(math.ceil(math.log(2**int_bits,10)))

#characters in the base-10 significand is exactly the number of bits
#  0.5, 0.25, 0.125, etc.
# Each step involves extending another power of ten down...
frac_chars = frac_bits

sign_char = 1
point_char = 1

sign_loc = 0
int_loc = sign_char
point_loc = sign_char + int_chars
frac_loc = sign_char + int_chars + point_char
length = sign_char + int_chars + point_char + frac_chars

########

bits = [2**i for i in range(-frac_bits, int_bits)]

# Ensure the patterns are up to snuff
fmt = "%%0%d.%df"%(length - sign_char, frac_chars)
dec_patterns = [fmt%(b) for b in bits]

#generate the list of contributory things
fraction_patterns = [s[int_chars+sign_char:] for s in dec_patterns]
int_patterns = [s[:int_chars] for s in dec_patterns]

# make a dictionary of dictionaries for fraction patterns.
# Top level key: character in fraction [0, frac_chars)
# Second level key: contributory bit
# Second level value: resulting decimal digit
fracs = {i: {bit: fraction_patterns[bit][i] for bit in range(len(fraction_patterns))} for i in range(frac_chars)}
ints =  {i: {bit: int_patterns[bit][i]      for bit in range(len(int_patterns))}      for i in range(int_chars)}

def frac_poly(n):
    patterns = [(k,v) for k, v in fracs[n].iteritems()]
    terms = ["(%c * bit%d)"%(p, bit+flag_bits) for bit, p in patterns if p != "0"]
    return " + ".join(terms)

def int_poly(n):
    patterns = [(k,v) for k, v in ints[n].iteritems()]
    terms = ["(%c * bit%d)"%(p, bit+flag_bits) for bit, p in patterns if p != "0"]
    return " + ".join(terms)

print """#include "ftfp.h"

/*********
 * This file is autogenerated by generate_print.py.
 * Please don't modify it manually.
 *********/

void fix_print(char* buffer, fixed f) {
  uint8_t isinfpos = FIX_IS_INF_POS(f);
  uint8_t isinfneg = FIX_IS_INF_NEG(f);
  uint8_t isnan = FIX_IS_NAN(f);
  uint8_t excep = isinfpos | isinfneg | isnan;

  uint32_t carry = 0;
  uint32_t scratch = 0;
  uint32_t neg = !!FIX_TOP_BIT(f);

  f = fix_abs(f);"""

print "\n".join(["  uint8_t bit%d = (((f) >> (%d))&1);"%(i,i) for i in range(2,2+number_bits)])

# start at the end and move forward...
for position in reversed(range(frac_chars)):
    poly = frac_poly(position)
    print "  scratch = %s + carry;"%(poly)
    print "  buffer[%d] = ((%d + (scratch %% 10)) * (1-excep) + (excep * %d));"%(frac_loc+position, ord('0'), ord(' ')), "carry = scratch / 10;"

print
print "  buffer[%d] = excep*%d + (1-excep)*%d;"%(point_loc, ord(' '), ord('.'))
print

extra_polynomials = {
        1: " + (isnan * %d) + (isinfpos | isinfneg) * %d"%(ord('N'), ord('I')),
        2: " + (isnan * %d) + (isinfpos | isinfneg) * %d"%(ord('a'), ord('n')),
        3: " + (isnan * %d) + (isinfpos | isinfneg) * %d"%(ord('N'), ord('f')),
        }

for position in reversed(range(int_chars)):
    poly = int_poly(position)
    print "  scratch = %s + carry;"%(poly)
    print "  buffer[%d] = ((%d + (scratch %% 10)) * (1-excep)) %s;"%(int_loc + position, ord('0'),
        extra_polynomials.get(int_loc+position, "+ (excep * %d)"%(ord(' ')))), "carry = scratch / 10;"

print """
  uint8_t n = (neg*(1-excep) + isinfneg);
  buffer[0] = %d * n + %d * (1-n);
"""%(ord('-'), ord(' '))

print "  buffer[%d] = '\\0';"%(length);

print """}
"""

