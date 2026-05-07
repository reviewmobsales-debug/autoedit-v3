.PHONY: install test run docker clean

install:
	python3 -m pip install -r requirements.txt

test:
	python3 -m py_compile main.py
	python3 -c "from editor.effects import remove_silences; print('effects OK')"
	python3 -c "from editor.captions import render_caption_style; print('captions OK')"

run:
	python3 main.py --server --port 5002

docker:
	docker build -t autoedit .

docker-run:
	docker run -p 8080:10000 autoedit

clean:
	rm -rf uploads/*.mp4 exports/*.mp4 __pycache__ editor/__pycache__
	pkill -f "python3 main.py" || true
