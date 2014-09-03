#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <inttypes.h>

#include <stdarg.h>
#include <stddef.h>
#include <setjmp.h>
#include <cmocka.h>
#include <math.h>

#include "ftfp.h"

static void null_test_success(void **state) {
  //(void) state;
}


void p(fixed f) {
  char buf[40];

  fix_print(buf, f);
  printf("n: %s\n", buf);
}


#define unit_fixint_dbl(name) unit_test(convert_dbl_##name)
#define CONVERT_DBL(name, d, bits) static void convert_dbl_##name(void **state) { \
  fixed f = bits; \
  fixed g = fix_convert_double(d); \
  assert_memory_equal( &f, &g, sizeof(fixed)); \
}

CONVERT_DBL(zero     , 0         , 0x00000);
CONVERT_DBL(one      , 1         , 0x20000);
CONVERT_DBL(one_neg  , -1        , 0xfffe0000);
CONVERT_DBL(two      , 2         , 0x40000);
CONVERT_DBL(two_neg  , -2        , 0xfffc0000);
CONVERT_DBL(many     , 1000.4    , 0x7d0cccc);
CONVERT_DBL(many_neg , -1000.4   , 0xf82f3334);
CONVERT_DBL(frac     , 0.5342    , 0x11180);
CONVERT_DBL(frac_neg , -0.5342   , 0xfffeee80);
CONVERT_DBL(inf_pos  , INFINITY  , F_INF_POS);
CONVERT_DBL(inf_neg  , -INFINITY , F_INF_NEG);
CONVERT_DBL(nan      , nan("0")  , F_NAN);

#define unit_fixnum(name) unit_test(fixnum_##name)
#define TEST_FIXNUM(name, z, frac, bits) static void fixnum_##name(void **state) { \
  fixed f = bits; \
  fixed g = FIXNUM(z, frac); \
  assert_true( FIX_EQ(f, g) ); \
}

TEST_FIXNUM(zero     , 0     , 0    , 0x0);
TEST_FIXNUM(one      , 1     , 0    , 0x20000);
TEST_FIXNUM(one_neg  , -1    , 0    , 0xfffe0000);
TEST_FIXNUM(two      , 2     , 0    , 0x40000);
TEST_FIXNUM(two_neg  , -2    , 0    , 0xfffc0000);
TEST_FIXNUM(many     , 1000  , 4    , 0x7d0cccc);
TEST_FIXNUM(many_neg , -1000 , 4    , 0xf82f3334);
TEST_FIXNUM(frac     , 0     , 5342 , 0x11184);
TEST_FIXNUM(frac_neg , -0    , 5342 , 0xfffeee7c);

#define unit_add(name) unit_test(add_##name)
#define ADD_CUST(name, op1, op2, result) static void add_##name(void **state) { \
  fixed o1 = fix_convert_double(op1); \
  fixed o2 = fix_convert_double(op2); \
  fixed added = fix_add(o1,o2); \
  fixed expected = result; \
  assert_true( FIX_EQ(added, expected) ); \
}
#define ADD(name, op1, op2, val) ADD_CUST(name, op1, op2, fix_convert_double(val))

ADD(one_zero,      1,     0,     1);
ADD(one_one,       1,     1,     2);
ADD(fifteen_one,   15,    1,     16);
ADD_CUST(overflow, 1<<13, 1<<13, F_INF_POS);
// TODO: negative overflow, NaNs, fractions

#define unit_neg(name) unit_test(neg_##name)
#define NEG_CUST(name, op1, result) static void neg_##name(void **state) { \
  fixed o1 = fix_convert_double(op1); \
  fixed negd = fix_neg(o1); \
  fixed expected = result; \
  assert_true( FIX_EQ(negd, expected) ); \
}
#define NEG(name, op1, val) NEG_CUST(name, op1, fix_convert_double(val))

NEG(zero,    0, 0);
NEG(one,     1, -1);
NEG(one_neg, -1, 1);
NEG_CUST(inf, INFINITY, F_INF_NEG);
NEG_CUST(inf_neg, -INFINITY, F_INF_POS);
NEG_CUST(nan, nan("0"), F_NAN);

int main(int argc, char** argv) {

  const UnitTest tests[] = {
    unit_test(null_test_success),
    unit_fixint_dbl(zero),
    unit_fixint_dbl(one),
    unit_fixint_dbl(one_neg),
    unit_fixint_dbl(two),
    unit_fixint_dbl(two_neg),
    unit_fixint_dbl(many),
    unit_fixint_dbl(many_neg),
    unit_fixint_dbl(frac),
    unit_fixint_dbl(frac_neg),
    unit_fixint_dbl(inf_pos),
    unit_fixint_dbl(inf_neg),
    unit_fixint_dbl(nan),

    unit_fixnum(zero),
    unit_fixnum(one),
    unit_fixnum(one_neg),
    unit_fixnum(two),
    unit_fixnum(two_neg),
    unit_fixnum(many),
    unit_fixnum(many_neg),
    unit_fixnum(frac),
    unit_fixnum(frac_neg),

    unit_add(one_zero),
    unit_add(one_one),
    unit_add(fifteen_one),
    unit_add(overflow),

    unit_neg(zero),
    unit_neg(one),
    unit_neg(one_neg),
    unit_neg(inf),
    unit_neg(inf_neg),
    unit_neg(nan),
  };
  return run_tests(tests);
}