CC = cc
CFLAGS = -std=c11 -O2 -Wall -Wextra -Werror -pedantic
CFLAGS += -ffp-contract=off
LDLIBS = -lm

PROGRAMS = linear poisson renewal ctmc stopping finance bs
SOURCES_linear = chapter01_markov_chains/linear.c
SOURCES_poisson = chapter02_poisson_processes/poisson.c
SOURCES_renewal = chapter03_renewal_processes/renewal.c
SOURCES_ctmc = chapter04_continuous_time_markov_chains/ctmc.c
SOURCES_stopping = chapter05_martingales/stopping.c
SOURCES_finance = chapter06_mathematical_finance/finance.c
SOURCES_bs = chapter06_mathematical_finance/bs.c

.PHONY: all clean
all: $(addprefix build/,$(PROGRAMS))

build:
	mkdir -p $@

define program_rule
build/$(1): $$(SOURCES_$(1)) | build
	$$(CC) $$(CFLAGS) $$< $$(LDLIBS) -o $$@
endef
$(foreach program,$(PROGRAMS),$(eval $(call program_rule,$(program))))

clean:
	rm -f $(addprefix build/,$(PROGRAMS))
