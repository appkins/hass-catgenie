# CatGenie credential extraction (Docker)

Reproducibly extract the two values the integration needs — the **token**
(JWT/refresh token) and the **secret** (HMAC key) — from the CatGenie Android app
running in an emulator. Everything runs in containers; the host only needs
**Docker** and **KVM**.

> Only do this for **your own account**. The values are per-account credentials.

## What you get

| Config field | Source | Script |
|---|---|---|
| `token`  | `Authorization: Bearer …` / refreshToken response | `frida/capture-auth.js` |
| `secret` | HMAC key from `javax.crypto.Mac` (reconstructable to a config secret) | `frida/capture-hmac.js` |
| `secret` (raw) | keychain plaintext via `Cipher.doFinal` | `frida/dump-keychain.js` |
| _all routes_ | full method/url+query/headers/body + response, every request | `frida/capture-http.js` |

### Capture every route (`make http`)

`frida/capture-http.js` is a full-fidelity, app-layer packet interceptor. It hooks
**both** HTTP stacks the app uses — OkHttp 4
(`RealCall.getResponseWithInterceptorChain$okhttp`, all React Native traffic) and
`java.net.HttpURLConnection` (the Firebase SDKs) — so *every* request is logged
with its method, full URL _including the query string_, all request headers
(the `y-pm-sg`/`x-pm-en`/`x-render-t` signing set included), the request body, the
response status, all response headers, and the response body. Because it sits
above TLS it needs no proxy or CA install and is immune to cert pinning.

```sh
make REDROID=1 http      # -> out/capture-http.log ; then drive the app
```

Requests are tagged `#<id>` so each `REQUEST`/`RESPONSE` pair lines up. For an
on-the-wire alternative (mitmproxy), run `make unpin` alongside an external proxy.

## Prerequisites

- Docker + Docker Compose.
- Hardware virtualization: `/dev/kvm` must exist and be usable
  (`ls -l /dev/kvm`; add yourself to the `kvm` group if needed). Without KVM the
  emulator is unusably slow.
- The CatGenie APK saved here as **`catgenie.apk`** (from APKMirror/apkpure). If
  it's a split APK, keep the base as `catgenie.apk` — `make install` falls back
  to `install-multiple`.

## Steps

```bash
cd hack/credentials

make up          # start emulator (first run pulls a large image) + tools
make web         # -> http://localhost:6080  (watch/operate the phone screen)

make install     # install catgenie.apk
make packages    # confirm the package name; if it isn't com.petnovations.catgenie,
                 # set PKG in docker-compose.yml (tools service) and `make up` again

make frida       # push + start frida-server, forward its port

# --- capture ---
make secret      # then, in the noVNC screen: log in and open your device
make token       # then: let the app refresh / re-open it
```

Watch the terminal output (also saved under `out/`). You're looking for:

- **secret** (`make secret`): a line like
  ```
  [hmac] key (utf8): Ytnu5XPMENDE25FPFEFVR2UsrFwtx3
  [hmac] >>> config "secret" = 00000000000000000000000000000000000000000000000000000000nu5XPMENDE25FPFEFVR2UsrFwt
  ```
  Paste that `config "secret"` value into the integration's **secret** field.
  (It's a 56-char filler + the 28 chars `signing.py` actually slices — see below.)

- **token** (`make token`): a line like
  ```
  [auth] >>> bearer/refresh token = eyJhbGciOiJSUzUxMi␣...
  ```
  Use the token POSTed to `/facade/v1/mobile-user/refreshToken` (the long-lived
  refresh token) for the **token** field.

```bash
make down        # tear everything down
```

## Why the reconstructed secret works

`signing.py` derives the HMAC key as `"Yt" + secret[56:84] + "x3"` and never uses
any other part of the 84-char secret. So a secret of `("0" * 56) + key[2:30]`
produces the identical HMAC key and signs correctly. If you'd rather have the
**real** 84-char secret, use `make keychain` (hooks `Cipher.doFinal`) instead.

## If the app won't run

- **ABI**: the app is React Native (native `.so` libs). The emulator is x86_64; an
  arm64-only build relies on ART's ARM translation (present on Android 11+
  x86_64 images, which this uses). If it still crashes on launch, the app is
  likely arm64-only without a working translation — use a **physical rooted
  device** with the same `frida/*.js` scripts.
- **Cert pinning** (only relevant if you proxy traffic instead of using Frida):
  run `make unpin` alongside mitmproxy.
- **Root**: the `emulator_13.0` image is a Google-APIs (non-Play) build, so
  `adb root` works — `make frida` relies on it.

## Files

- `docker-compose.yml` — emulator + tools services
- `Dockerfile.tools` — adb + frida-tools + python
- `setup-frida.sh` — download/push/start frida-server, forward port 27042
- `extract.sh` — `frida -f <pkg> -l <script>` over the remote server
- `frida/` — the hook scripts
- `Makefile` — the workflow above (`make help`)
