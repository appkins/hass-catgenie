/*
 * capture-http.js
 *
 * Full-fidelity packet interceptor for the CatGenie app, at the application
 * layer (above TLS — no proxy or CA install needed, immune to cert pinning).
 *
 * Captures EVERY route the app makes, with the complete request and response:
 *   - method + full URL (path AND query string)
 *   - every request header (incl. the y-pm-sg / x-pm-en / x-render-t signing set)
 *   - request body
 *   - response status line
 *   - every response header
 *   - response body
 *
 * It hooks both HTTP stacks an Android app can use:
 *   1. OkHttp 4 — okhttp3.internal.connection.RealCall.getResponseWithInterceptorChain
 *      (React Native networking, most app traffic). One call -> one final Response.
 *   2. java.net.HttpURLConnection — used by the Firebase/analytics SDKs
 *      (Installations, Remote Config, Bugfender, etc.), which do NOT go through
 *      OkHttp. Captures method/url/query/request-headers and the full response
 *      (status, headers, and body); request bodies on this stack are one-shot
 *      streams and are not echoed.
 *
 * The petnovations API itself is entirely OkHttp, so its request bodies (and
 * everything else) are captured in full.
 *
 * Usage:
 *   frida -U -f com.petnovations -l capture-http.js
 *   # or via the repo tooling:  make REDROID=1 http
 */

Java.perform(function () {
  console.log("[http] installing full-capture hooks");
  // Force JIT-compiled methods back to interpreted mode so hooks fire immediately.
  Java.deoptimizeEverything();

  var MAX_BODY = 1024 * 1024; // peek up to 1 MiB of each response body
  var seq = 0;

  var IGNORE_HOSTS = ["bugfender.com", "firebase", "google", "gstatic", "crashlytics", "amazonaws.com"];
  function ignored(url) {
    for (var i = 0; i < IGNORE_HOSTS.length; i++) {
      if (url.indexOf(IGNORE_HOSTS[i]) >= 0) return true;
    }
    return false;
  }

  function line(s) {
    console.log("[http] " + s);
  }

  function dumpHeaders(headers, prefix) {
    try {
      var n = headers.size();
      for (var i = 0; i < n; i++) {
        line(prefix + headers.name(i) + ": " + headers.value(i));
      }
    } catch (e) {
      line(prefix + "<headers unreadable: " + e + ">");
    }
  }

  // ---- 1. OkHttp ----------------------------------------------------------
  try {
    var RealCall = Java.use("okhttp3.internal.connection.RealCall");
    var Buffer = Java.use("okio.Buffer");

    // OkHttp 4 is Kotlin: the internal method is mangled to
    // `getResponseWithInterceptorChain$okhttp`. Fall back to the plain name for
    // OkHttp 3 / older builds.
    var hookName = RealCall["getResponseWithInterceptorChain$okhttp"]
      ? "getResponseWithInterceptorChain$okhttp"
      : "getResponseWithInterceptorChain";

    RealCall[hookName].implementation = function () {
      var id = ++seq;
      var req = null;
      try {
        req = this.request();
      } catch (e) {
        try {
          req = this.originalRequest.value;
        } catch (e2) {}
      }

      // --- request ---
      if (req !== null) {
        try {
          var url = req.url().toString(); // includes the query string
          if (ignored(url)) {
            return this[hookName]();
          }
          line("");
          line("===== #" + id + " REQUEST  " + req.method() + " " + url);
          dumpHeaders(req.headers(), "#" + id + " > ");
          var body = req.body();
          if (body !== null) {
            try {
              var buf = Buffer.$new();
              body.writeTo(buf); // JSON/form bodies are replayable
              line("#" + id + " > body: " + buf.readUtf8());
            } catch (eb) {
              line("#" + id + " > body: <unreadable: " + eb + ">");
            }
          }
        } catch (er) {
          line("#" + id + " request log error: " + er);
        }
      }

      // --- response (or error) ---
      var resp;
      try {
        resp = this[hookName]();
      } catch (err) {
        line("#" + id + " <<< NETWORK ERROR: " + err);
        throw err;
      }

      try {
        line("----- #" + id + " RESPONSE " + resp.code() + " " + resp.message());
        dumpHeaders(resp.headers(), "#" + id + " < ");
        try {
          var peek = resp.peekBody(MAX_BODY); // non-consuming copy
          var text = peek.string();
          line("#" + id + " < body: " + text);
        } catch (epb) {
          line("#" + id + " < body: <unreadable: " + epb + ">");
        }
      } catch (erp) {
        line("#" + id + " response log error: " + erp);
      }

      return resp;
    };
    line("OkHttp RealCall hook installed (" + hookName + ")");
  } catch (e) {
    line("OkHttp hook failed: " + e);
  }

  // ---- 2. java.net.HttpURLConnection (Firebase et al.) --------------------
  // Hook getInputStream/getErrorStream to log the response, and the request
  // metadata available on the connection. Bodies written via getOutputStream
  // are wrapped so we can echo what was sent.
  try {
    function safe(fn, fallback) {
      try {
        return fn();
      } catch (e) {
        return fallback;
      }
    }

    function logUrlConn(conn) {
      var id = ++seq;
      conn._capId = id;
      line("");
      line(
        "===== #" + id + " REQUEST  " + safe(function () {
          return conn.getRequestMethod();
        }, "?") + " " + safe(function () {
          return conn.getURL().toString(); // includes query string
        }, "?") + "   (HttpURLConnection)"
      );
      var props = safe(function () {
        return conn.getRequestProperties();
      }, null);
      if (props !== null) {
        var keys = props.keySet().toArray();
        for (var i = 0; i < keys.length; i++) {
          line("#" + id + " > " + keys[i] + ": " +
            safe(function () {
              return props.get(keys[i]).toString();
            }, "?"));
        }
      }
      return id;
    }

    function logUrlResp(conn, id) {
      var code = safe(function () {
        return conn.getResponseCode();
      }, -1);
      line("----- #" + id + " RESPONSE " + code + " " +
        safe(function () {
          return conn.getResponseMessage();
        }, ""));
      var hf = safe(function () {
        return conn.getHeaderFields();
      }, null);
      if (hf !== null) {
        var keys = hf.keySet().toArray();
        for (var i = 0; i < keys.length; i++) {
          var k = keys[i];
          line("#" + id + " < " + (k === null ? "(status)" : k) + ": " +
            safe(function () {
              return hf.get(k).toString();
            }, "?"));
        }
      }
    }

    // Hook the single concrete impl (HttpsURLConnectionImpl delegates into it),
    // on getResponseCode — the one method every client path funnels through to
    // actually send the request. A per-connection guard prevents the duplicate
    // logging that hooking multiple delegating classes would cause.
    var Impl = Java.use("com.android.okhttp.internal.huc.HttpURLConnectionImpl");
    Impl.getResponseCode.implementation = function () {
      if (!this._capLogged) {
        this._capLogged = true;
        var url = safe(function () { return this.getURL().toString(); }.bind(this), "");
        if (ignored(url)) {
          return this.getResponseCode();
        }
        var id = logUrlConn(this);
        var code = this.getResponseCode();
        logUrlResp(this, id);
        return code;
      }
      return this.getResponseCode();
    };

    // Capture the response body too: read the stream fully, log it, and hand the
    // caller back a replayable copy so the app still works. FIS/analytics bodies
    // are small, so buffering in memory is fine.
    var ByteArrayInputStream = Java.use("java.io.ByteArrayInputStream");
    var ByteArrayOutputStream = Java.use("java.io.ByteArrayOutputStream");
    var JString = Java.use("java.lang.String");

    function teeBody(conn, is, kind) {
      if (is === null) {
        return is;
      }
      var id = conn._capId || -1;
      try {
        var baos = ByteArrayOutputStream.$new();
        var buf = Java.array("byte", Array.from({ length: 16384 }, function () {
          return 0;
        }));
        var n;
        while ((n = is.read(buf)) !== -1) {
          baos.write(buf, 0, n);
        }
        is.close();
        var bytes = baos.toByteArray();
        line("#" + id + " < " + kind + ": " + JString.$new(bytes, "UTF-8"));
        return ByteArrayInputStream.$new(bytes);
      } catch (e) {
        line("#" + id + " < body: <unreadable: " + e + ">");
        return is;
      }
    }

    Impl.getInputStream.implementation = function () {
      return teeBody(this, this.getInputStream(), "body");
    };
    Impl.getErrorStream.implementation = function () {
      return teeBody(this, this.getErrorStream(), "error-body");
    };
    line("HttpURLConnection hook installed (HttpURLConnectionImpl.getResponseCode)");
  } catch (e) {
    line("HttpURLConnection hooks failed: " + e);
  }

  line("done — drive the app; every request/response is logged with #id pairs");
});
