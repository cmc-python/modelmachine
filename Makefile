SRC_DIR = modelmachine
GENERATED = build dist *.egg-info

all : test lint pep257 dist

twine : dist
	twine upload dist/*

clean :
	rm -rf $(GENERATED)

lint :
	pylint $(SRC_DIR)

pep257 :
	pep257 $(SRC_DIR)
