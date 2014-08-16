all: clean
	pdflatex caching.tex
	bibtex caching.aux
	pdflatex caching.tex
	pdflatex caching.tex
	mv caching.pdf thesis.pdf

clean:
	rm -f *.aux *.bbl *.blg *.log *pdf

