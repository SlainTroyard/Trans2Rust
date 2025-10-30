/*
 * Simple example program demonstrating math utilities
 */

#include <stdio.h>
#include <stdlib.h>
#include "math_utils.h"

int main(int argc, char *argv[])
{
	printf("Math Utils Example\n");
	printf("==================\n\n");
	
	// Test factorial
	printf("Factorial of 5: %d\n", factorial(5));
	printf("Factorial of 0: %d\n", factorial(0));
	
	// Test GCD
	printf("GCD of 48 and 18: %d\n", gcd(48, 18));
	printf("GCD of 17 and 13: %d\n", gcd(17, 13));
	
	// Test prime check
	printf("Is 17 prime? %s\n", is_prime(17) ? "yes" : "no");
	printf("Is 20 prime? %s\n", is_prime(20) ? "yes" : "no");
	printf("Is 2 prime? %s\n", is_prime(2) ? "yes" : "no");
	
	return 0;
}

