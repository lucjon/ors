LATEXMK ?= latexmk
LFLAGS += -pdf
SUBTARGETS := 01-zhang-summary 04-outline



ifeq ($(PDFS),)
$(SUBTARGETS): %:
	make -C $@

all: $(SUBTARGETS)
else
all: $(PDFS)
	
endif


$(PDFS): %.pdf: %.tex
	$(LATEXMK) $(LFLAGS) $<

$(patsubst %,clean-%,$(PDFS)):
	$(LATEXMK) -C $<
	rm -f $(@:clean-%.pdf=%.bbl) $(@:clean-%.pdf=%.run.xml)

clean: $(patsubst %,clean-%,$(PDFS))
	rm -f missfont.log


.PHONY: clean $(patsubst %,clean-%,$(PDFS)) $(SUBTARGETS)
