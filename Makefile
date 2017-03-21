PY = python2.7 -m compileall -q -f

CONFIG = config

SRC = src
SRC_CONF = $(SRC)/$(CONFIG)

TARGETS = pretty
TARGET_CONF = $(TARGETS)/$(CONFIG)

all: clean $(TARGETS)

$(TARGETS):
	cp -r $(SRC) $(TARGETS)
	-$(PY) $(TARGETS)
	find $(TARGETS) -name '*.py' -delete
	rm $(TARGET_CONF)/setting.pyc
	cp $(SRC_CONF)/setting.py $(TARGET_CONF)

clean: 
	rm -rf $(TARGETS)
