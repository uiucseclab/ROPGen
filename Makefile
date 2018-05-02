all:
	gcc -m32 -static -U_FORTIFY_SOURCE -fno-stack-protector test.c -o teststatic
