LATEXMK ?= latexmk
LFLAGS += -pdf -pdflatex="pdflatex -shell-escape %O %S"
SUBTARGETS := 01-zhang-summary 04-project 05-zhang-cs 06-talk



ifeq ($(PDFS),)
all: experiment.tex $(SUBTARGETS)

$(SUBTARGETS): %:
	make -C $@
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

experiment.tex: experiment.dat
	./ors.py -f $< report --format latex_booktabs | sed 's/\\\$$/$$/g' > $@


.PHONY: clean $(patsubst %,clean-%,$(PDFS)) $(SUBTARGETS)
