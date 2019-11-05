.PHONY: test $(wildcard build-%) $(wildcard shutdown-%) \
	$(wildcard deploy-%) $(wildcard redeploy-%)

venv:
	# Need to install pip separately into the venv for Debian/Ubuntu systems
	test -d venv || { python3 -m venv venv --without-pip && . venv/bin/activate; \
		wget https://bootstrap.pypa.io/get-pip.py -O venv/bin/get-pip.py && \
		chmod u+x venv/bin/get-pip.py && venv/bin/get-pip.py; }
	ls .activate.sh > /dev/null || ln -s venv/bin/activate .activate.sh
	echo "deactivate" > .deactivate.sh

install: venv
	. venv/bin/activate; pip install -e .

install-dev: install requirements-dev.txt
	. venv/bin/activate; pip install -r requirements-dev.txt

lint: install-dev
	. venv/bin/activate; mypy src && pylint src

test: install-dev
	. venv/bin/activate; coverage run -m pytest -v

clean:
	rm -rf venv .pytest_cache .activate.sh .mypy_cache
	find . -iname "*.pyc" -delete

build-%: src docker-compose.shared.yml docker-compose.%.yml
	test -d build/$* && rm -rf build/$* || true
	mkdir -p build/$*
	docker-compose \
		-f docker-compose.shared.yml \
		-f docker-compose.$*.yml \
		config > build/$*/docker-compose.yml
	docker-compose -p figmentator_$* -f build/$*/docker-compose.yml build

redeploy-%: shutdown-% build-%
	docker-compose -p figmentator_$* -f build/$*/docker-compose.yml up -d

deploy-%:
	docker-compose -p figmentator_$* -f build/$*/docker-compose.yml up -d

shutdown-%:
	test -f build/$*/docker-compose.yml && \
		docker-compose -p figmentator_$* -f build/$*/docker-compose.yml down --remove-orphans || true

shutdown-dev:
	# make a specialized shutdown for dev which removes volumes
	test -f build/dev/docker-compose.yml && \
		docker-compose -p figmentator_dev -f build/dev/docker-compose.yml down -v --remove-orphans || true

run-%-shell:
	docker-compose -p figmentator_$* -f build/$*/docker-compose.yml run backend sh
