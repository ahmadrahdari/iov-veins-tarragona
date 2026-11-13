# FogRoam over 5G NR. Expects inet4.5, simu5g, veins and veins_inet in $(ROOT)
# (build/build5g.sh calls: make makefiles ROOT=$SIM/src VEINS_PROJ=$SIM/src/veins).
ROOT ?= $(abspath ../src)
VEINS_PROJ ?= $(ROOT)/veins

all: checkmakefiles
	@cd src && $(MAKE)

clean: checkmakefiles
	@cd src && $(MAKE) clean

makefiles:
	@cd src && opp_makemake --make-so -f --deep -o fogroam5g -O out \
	  -KINET_PROJ=$(ROOT)/inet4.5 -KSIMU5G_PROJ=$(ROOT)/simu5g -KVEINS_PROJ=$(VEINS_PROJ) -KVEINS_INET_PROJ=$(ROOT)/veins_inet \
	  -DINET_IMPORT -I. -I'$$(INET_PROJ)/src' -I'$$(SIMU5G_PROJ)/src' -I'$$(VEINS_PROJ)/src' -I'$$(VEINS_INET_PROJ)/src' \
	  -L'$$(INET_PROJ)/src' -L'$$(SIMU5G_PROJ)/src' -L'$$(VEINS_PROJ)/src' -L'$$(VEINS_INET_PROJ)/src' \
	  -lINET'$$(D)' -lsimu5g'$$(D)' -lveins'$$(D)' -lveins_inet'$$(D)'

checkmakefiles:
	@if [ ! -f src/Makefile ]; then echo 'run "make makefiles" first'; exit 1; fi
