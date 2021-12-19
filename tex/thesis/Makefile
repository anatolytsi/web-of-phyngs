###
### generic GNU make Makefile for .tex -> .pdf.
### ransford at cs.washington.edu
###   http://github.com/ransford/pdflatex-makefile
### edited by Emanuel Regnath, 2016
###
### Recommended usage:
###   1. $ make pdf          (make the pdf)
###   2. $ make snapshot     (pass around a draft...)
###   2. $ make distill      (submit the camera-ready version with embedded fonts)
###

###################################################################################################
# #  Own Changes
###################################################################################################

TARGET=thesis

# output directory
OUTPUTDIR=.

# include directory
INCDIR = ./tum

# compiler
PDFLATEX	?= pdflatex -halt-on-error -file-line-error 
# PDFLATEX	?= xelatex
#BIBTEX		?= biber --quiet
BIBTEX		?= bibtex -terse
MAKEGLOSSARIES ?= makeglossaries -d $(OUTPUTDIR)

## Action for 'make view'
PDFVIEWER	?= xdg-open   # only "open" if on Darwin 

# uncomment to get all output
QUIET = defined


# uncomment for additional post processing (define your own rule)
# AFTERALL =


###################################################################################################
# #  Don't edit below this Line!!!
###################################################################################################

# search for additional tex files
export TEXINPUTS+=:${INCDIR}:${OUTPUTDIR}//
export max_print_line=1000

# check if the variable QUIET has any value
ifneq ($(QUIET),)
#PDFLATEX	+= -interaction=batchmode
ERRFILTER_AUX	:= 2>&1 | egrep --color -A5 ':[[:digit:]]+:|^l\.[0-9]* |Warning'
#> /dev/null || (egrep ':[[:digit:]]+:|^l\.[0-9]*|Warning' *.log && false)
ERRFILTER	:= 2>&1 | egrep ':[[:digit:]]+:|^l\.[0-9]* |Warning'
else
PDFLATEX	+= -interaction=nonstopmode
endif


## Name of the target file, minus .pdf: e.g., TARGET=mypaper causes this
## Makefile to turn mypaper.tex into mypaper.pdf.
TARGETS += $(TARGET)
TEXTARGETS = $(TARGETS:=.tex)
PDFTARGETS = $(TARGETS:=.pdf)
AUXFILES   = $(TARGETS:=.aux)
LOGFILES   = $(TARGETS:=.log)

## If $(TARGET).tex refers to .bib files like \bibliography{foo,bar}, then
## $(BIBFILES) will contain foo.bib and bar.bib, and both files will be added as
## dependencies to $(PDFTARGETS).
## Effect: updating a .bib file will trigger re-typesetting.
BIBFILES += $(patsubst %,%.bib,\
		$(shell grep '^[^%]*\\bibliography{' $(TEXTARGETS) | \
			grep -o '\\bibliography{[^}]\+}' | \
			sed -e 's/^[^%]*\\bibliography{\([^}]*\)}.*/\1/' \
			    -e 's/, */ /g'))

## Add \input'ed or \include'd files to $(PDFTARGETS) dependencies; ignore
## .tex extensions.
INCLUDEDTEX = $(patsubst %,%.tex,\
		$(shell grep '^[^%]*\\\(input\|include\){' $(TEXTARGETS) | \
			grep -o '\\\(input\|include\){[^}]\+}' | \
			sed -e 's/^.*{\([^}]*\)}.*/\1/' \
			    -e 's/\.tex$$//'))

AUXFILES += $(INCLUDEDTEX:.tex=.aux)



# .PHONY names all targets that aren't filenames
.PHONY: all clean pdf view snapshot distill distclean

all: pdf $(AFTERALL) view

pdf: $(PDFTARGETS)

view: $(PDFTARGETS)
	$(PDFVIEWER) $(PDFTARGETS)


# to generate aux but not pdf from pdflatex, use -draftmode
%.aux: %.tex 
	$(PDFLATEX) $* $(ERRFILTER_AUX)

# introduce BibTeX dependency if we found a \bibliography
ifneq ($(strip $(BIBFILES)),)
BIBDEPS = %.bbl
%.bbl: %.aux $(BIBFILES)
	$(BIBTEX) $*
endif

# introduce makeglossaries dependency if we found \printglossary/ies
HAS_GLOSSARIES = $(shell \
		grep '^[^%]*\\printglossar\(ies\|y\)' $(TEXTARGETS) $(INCLUDEDTEX) && \
		echo HAS_GLOSSARIES)
ifneq ($(HAS_GLOSSARIES),)
GLSDEPS = %.gls
%.gls: %.aux
	$(MAKEGLOSSARIES) $(TARGETS)
endif

$(PDFTARGETS): %.pdf: %.tex %.aux $(GLSDEPS) $(BIBDEPS) $(INCLUDEDTEX) 
	$(PDFLATEX) $* $(ERRFILTER)
ifneq ($(strip $(BIBFILES)),)
	@if egrep -q "undefined (references|citations)" $*.log; then \
		$(BIBTEX) $* && $(PDFLATEX) $* $(ERRFILTER); fi
endif
	@while grep -q "Rerun to" $*.log; do \
		$(PDFLATEX) $* $(ERRFILTER); done

DRAFTS := $(PDFTARGETS:.pdf=-$(REVISION).pdf)
$(DRAFTS): %-$(REVISION).pdf: %.pdf
	cp $< $@
snapshot: $(DRAFTS)

%.distilled.pdf: %.pdf
	gs -q -dSAFER -dNOPAUSE -dBATCH -sDEVICE=pdfwrite -sOutputFile=$@ \
		-dCompatibilityLevel=1.5 -dPDFSETTINGS=/prepress -c .setpdfwrite -f $<
	exiftool -overwrite_original -Title="" -Creator="" -CreatorTool="" $@

distill: $(PDFTARGETS:.pdf=.distilled.pdf)

distclean: clean
	$(RM) $(PDFTARGETS) $(PDFTARGETS:.pdf=.distilled.pdf) $(EXTRADISTCLEAN)

clean:
	$(RM) $(foreach T,$(TARGETS), \
		$(T).bbl $(T).bcf $(T).bit $(T).blg \
		$(T)-blx.bib $(T).brf $(T).glg $(T).glo \
		$(T).gls $(T).glsdefs $(T).glx \ $(T).gxg \
		$(T).acn $(T).acr $(T).alg $(T).sym $(T).sbl $(T).ter $(T).tms\
		$(T).gxs $(T).idx $(T).ilg $(T).ind \
		$(T).ist $(T).loa $(T).lof $(T).lol \
		$(T).lot $(T).maf $(T).mtc $(T).nav \
		$(T).out $(T).pag $(T).run.xml $(T).snm \
		$(T).svn $(T).tdo $(T).tns $(T).toc \
		$(T).vtc $(T).url) \
		$(AUXFILES) $(LOGFILES) \
		$(EXTRACLEAN)