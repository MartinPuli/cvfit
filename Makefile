.PHONY: test example clean

test:
	python3 tests/run.py

example:
	python3 scripts/build_cv.py examples/ada-lovelace.northwind.yaml -o out/ada.pdf --kind job --preview
	python3 scripts/verify_cv.py out/ada.pdf --profile out/ada.profile.json --master examples/ada-lovelace.yaml
	python3 scripts/match_report.py out/ada.pdf --target examples/posting-northwind.json

clean:
	rm -rf out
