# CatGenie credential extraction — Docker-driven.
#
# Emulator path (x86, needs ARM translation — may fail for this arm64-only app):
#   make up && make install && make frida && make secret
#
# ReDroid path (recommended — bundled arm translation; run prep once with sudo):
#   sudo ./redroid-prep.sh
#   make REDROID=1 up && make REDROID=1 install && make REDROID=1 frida
#   make REDROID=1 secret      # -> out/capture-hmac.log
#   make REDROID=1 token       # -> out/capture-auth.log
#   make REDROID=1 down

# REDROID=1 swaps the whole flow onto the ReDroid compose file.
ifdef REDROID
COMPOSE_FILE := -f docker-compose.redroid.yml
endif

COMPOSE := docker compose $(COMPOSE_FILE)
EXEC    := $(COMPOSE) exec -T tools
# Interactive (TTY) exec — required for the Frida capture targets so the session
# stays attached while you drive the app. `-T` closes stdin and Frida exits.
IEXEC   := $(COMPOSE) exec tools

# Network adb devices (emulator/redroid) must be (re)connected each session —
# they don't persist like USB. Prepend this to any adb command run in tools.
ADBC := adb connect $$EMULATOR_HOST:5555 >/dev/null 2>&1; adb wait-for-device;

.PHONY: help prep up tools down logs web packages install frida capture secret token keychain unpin shell clean

prep: ## (ReDroid) Load host kernel modules — run with sudo
	sudo ./redroid-prep.sh

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	  | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

up: ## Start the device + tools, wait for boot
	$(COMPOSE) up -d --build
	@echo "Waiting for Android to boot (first run pulls the image)..."
	@$(EXEC) bash -lc 'adb connect $$EMULATOR_HOST:5555 >/dev/null; adb wait-for-device; \
	  until [ "$$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d "\r")" = "1" ]; do sleep 3; done; \
	  echo "Android booted."'
ifdef REDROID
	@echo "View/operate the screen with: scrcpy -s 127.0.0.1:5555  (adb connect localhost:5555 first)"
else
	@echo "View the screen at http://localhost:6080"
endif

web: ## (emulator) Print the noVNC URL
	@echo "http://localhost:6080"

packages: ## List installed packages (find the CatGenie package name)
	$(EXEC) bash -lc '$(ADBC) adb shell pm list packages | sort'

install: ## Install the split APK set from ./apk into the emulator
	@test -f apk/base.apk || { echo "Run ./extract-xapk.sh <file.xapk> first (need ./apk/base.apk)"; exit 1; }
	$(EXEC) bash -lc '$(ADBC) adb install-multiple -r -g /work/apk/base.apk /work/apk/config.arm64_v8a.apk /work/apk/config.xxhdpi.apk /work/apk/config.en.apk'

frida: ## Push + start frida-server, forward its port
	$(EXEC) setup-frida.sh

capture: ## Capture key + token together in ONE login session (recommended)
	$(IEXEC) extract.sh frida/dump-keychain.js frida/capture-hmac.js frida/capture-auth.js

secret: ## Capture the HMAC key / 84-char secret
	$(IEXEC) extract.sh frida/capture-hmac.js

keychain: ## Dump the raw keychain secret (Cipher.doFinal)
	$(IEXEC) extract.sh frida/dump-keychain.js

token: ## Capture the JWT / refresh token
	$(IEXEC) extract.sh frida/capture-auth.js

unpin: ## Run the SSL-unpinning script (for use with an external proxy)
	$(IEXEC) extract.sh frida/ssl-unpin.js

shell: ## Open a shell in the tools container
	$(COMPOSE) exec tools bash

logs: ## Tail device/container logs
	$(COMPOSE) logs -f

down: ## Stop and remove everything
	$(COMPOSE) down -v

clean: ## Remove captured output
	rm -rf out
