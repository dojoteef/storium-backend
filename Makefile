-include .env
NAME?=figmentator

.PHONY: test $(wildcard build-%) $(wildcard shutdown-%) \
	$(wildcard deploy-%) $(wildcard redeploy-%)

venv:
	# Need to install pip separately into the venv for Debian/Ubuntu systems
	test -d venv || { python3 -m venv venv --without-pip && . venv/bin/activate; \
		wget https://bootstrap.pypa.io/get-pip.py -O venv/bin/get-pip.py && \
		chmod u+x venv/bin/get-pip.py && venv/bin/get-pip.py; }
	ls .activate.sh > /dev/null || ln -s venv/bin/activate .activate.sh
	echo "deactivate" > .deactivate.sh

source-venv: venv
	. venv/bin/activate

install: source-venv
	pip install -e .

install-dev: install requirements-dev.txt
	pip install -r requirements-dev.txt

install-deploy: install requirements-deploy.txt
	pip install -r requirements-deploy.txt

lint: install-dev
	mypy src && pylint src

test: install-dev
	coverage run -m pytest -v

clean:
	rm -rf venv .pytest_cache .activate.sh .mypy_cache
	find . -iname "*.pyc" -delete

build-%: src install-deploy docker-compose.shared.yml docker-compose.%.yml
	test -d build/$* && rm -rf build/$* || true
	mkdir -p build/$*
	docker-compose \
		$$(test -f docker-compose.env.yml && echo -f docker-compose.env.yml || echo "") \
		-f docker-compose.shared.yml \
		-f docker-compose.$*.yml \
		config > build/$*/docker-compose.yml
	docker-compose -p $(NAME)_$* -f build/$*/docker-compose.yml build

redeploy-%: shutdown-% build-%
	docker-compose -p $(NAME)_$* -f build/$*/docker-compose.yml up -d

deploy-%:
	docker-compose -p $(NAME)_$* -f build/$*/docker-compose.yml up -d

shutdown-%:
	test -f build/$*/docker-compose.yml && \
		docker-compose -p $(NAME)_$* -f build/$*/docker-compose.yml down --remove-orphans || true

shutdown-dev:
	# make a specialized shutdown for dev which removes volumes
	test -f build/dev/docker-compose.yml && \
		docker-compose -p $(NAME)_dev -f build/dev/docker-compose.yml down -v --remove-orphans || true

run-%-shell:
	docker-compose -p $(NAME)_$* -f build/$*/docker-compose.yml run backend sh
