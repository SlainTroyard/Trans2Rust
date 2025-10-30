/*
 * Simple math utilities header
 */

#ifndef MATH_UTILS_H
#define MATH_UTILS_H

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Calculate the factorial of a number
 * @param n The number to calculate factorial for (must be >= 0)
 * @return The factorial of n, or -1 if n < 0
 */
int factorial(int n);

/**
 * Calculate the greatest common divisor (GCD) of two numbers
 * @param a First number
 * @param b Second number
 * @return The GCD of a and b
 */
int gcd(int a, int b);

/**
 * Check if a number is prime
 * @param n The number to check
 * @return 1 if n is prime, 0 otherwise
 */
int is_prime(int n);

#ifdef __cplusplus
}
#endif

#endif /* MATH_UTILS_H */

