.PHONY: test example clean

test:
	python3 tests/run.py

example:
	python3 scripts/build_cv.py examples/profile.example.json -o out/example.pdf --kind job --preview
	python3 scripts/verify_cv.py out/example.pdf --profile out/example.profile.json

clean:
	rm -rf out
