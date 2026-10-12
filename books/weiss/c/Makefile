CC = clang
CFLAGS = -std=c11 -Wall -Wextra -Werror -pedantic

FIGURES = $(notdir $(wildcard ../WEISS_2E_extracted/fig*))
BINARIES = $(addprefix bin/,$(FIGURES))
CH12_OBJECTS = ch12.o ch12_splay.o ch12_redblack.o ch12_skip.o ch12_aa.o \
               ch12_treap.o ch12_kd.o ch12_pair.o

.PHONY: all check clean
all: $(BINARIES)

bin:
	mkdir -p bin

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

bin/fig1.%: fig1.%.c | bin
	$(CC) $(CFLAGS) $< -o $@

bin/fig2.%: fig2.%.c array_input.h | bin
	$(CC) $(CFLAGS) $< -o $@

bin/fig3.%: fig3.%.c ch3.o figure_entry.h | bin
	$(CC) $(CFLAGS) $< ch3.o -o $@

bin/fig4.%: fig4.%.c ch4.o figure_entry.h | bin
	$(CC) $(CFLAGS) $< ch4.o -o $@

bin/fig5.%: fig5.%.c ch5.o figure_entry.h | bin
	$(CC) $(CFLAGS) $< ch5.o -o $@

bin/fig6.%: fig6.%.c ch6.o figure_entry.h | bin
	$(CC) $(CFLAGS) $< ch6.o -o $@

bin/fig7.%: fig7.%.c ch7.o figure_entry.h | bin
	$(CC) $(CFLAGS) $< ch7.o -o $@

bin/fig8.%: fig8.%.c ch8.o figure_entry.h | bin
	$(CC) $(CFLAGS) $< ch8.o -o $@

bin/fig9.%: fig9.%.c ch9.o figure_entry.h | bin
	$(CC) $(CFLAGS) $< ch9.o -o $@

bin/fig10.%: fig10.%.c ch10.o figure_entry.h | bin
	$(CC) $(CFLAGS) $< ch10.o -o $@

bin/fig12.%: fig12.%.c $(CH12_OBJECTS) figure_entry.h | bin
	$(CC) $(CFLAGS) $< $(CH12_OBJECTS) -o $@

bin/figPG.%: figPG.%.c chpg.o figure_entry.h | bin
	$(CC) $(CFLAGS) $< chpg.o -o $@

bin/test_figures: testkit/testkit.c testkit/testkit.h tests/test_figures.c | bin
	$(CC) $(CFLAGS) testkit/testkit.c tests/test_figures.c -o $@

check: all bin/test_figures
	./bin/test_figures
	python3 verify_all.py

clean:
	rm -f $(BINARIES) bin/test_figures bin/debug-figure *.o
