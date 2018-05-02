#include <stdlib.h>
#include <stdio.h>
#include <string.h>

void say_hi(void) {
  char buf[64];
  printf("What's your name ?");
  scanf("%s", buf);
  printf("Hello %s!", buf);
}

int main(void) {
  say_hi();
}


