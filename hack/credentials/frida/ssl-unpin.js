/*
 * ssl-unpin.js
 *
 * Disable common TLS certificate pinning so an HTTPS proxy (mitmproxy) can read
 * the CatGenie app's traffic. Covers OkHttp CertificatePinner, the platform
 * TrustManager (TrustManagerImpl), and a generic SSLContext bypass.
 *
 * Usage:
 *   frida -U -f com.petnovations -l ssl-unpin.js
 */

Java.perform(function () {
  console.log("[ssl-unpin] installing hooks");

  // 1. OkHttp CertificatePinner.check() -> no-op
  try {
    var CertificatePinner = Java.use("okhttp3.CertificatePinner");
    CertificatePinner.check.overload("java.lang.String", "java.util.List").implementation =
      function (hostname) {
        console.log("[ssl-unpin] OkHttp CertificatePinner.check bypassed: " + hostname);
      };
    // Older signature
    CertificatePinner.check.overload(
      "java.lang.String",
      "[Ljava.security.cert.Certificate;"
    ).implementation = function (hostname) {
      console.log("[ssl-unpin] OkHttp CertificatePinner.check[] bypassed: " + hostname);
    };
  } catch (e) {
    console.log("[ssl-unpin] OkHttp pinner not present");
  }

  // 2. Android platform TrustManagerImpl.verifyChain() -> return the chain unchecked
  try {
    var TrustManagerImpl = Java.use("com.android.org.conscrypt.TrustManagerImpl");
    TrustManagerImpl.verifyChain.implementation = function (
      untrustedChain,
      trustAnchorChain,
      host,
      clientAuth,
      ocspData,
      tlsSctData
    ) {
      console.log("[ssl-unpin] TrustManagerImpl.verifyChain bypassed: " + host);
      return untrustedChain;
    };
  } catch (e) {
    console.log("[ssl-unpin] TrustManagerImpl not present");
  }

  // 3. Generic X509TrustManager via a custom SSLContext
  try {
    var X509TrustManager = Java.use("javax.net.ssl.X509TrustManager");
    var SSLContext = Java.use("javax.net.ssl.SSLContext");

    var TrustManager = Java.registerClass({
      name: "com.frida.TrustAllManager",
      implements: [X509TrustManager],
      methods: {
        checkClientTrusted: function () {},
        checkServerTrusted: function () {},
        getAcceptedIssuers: function () {
          return [];
        },
      },
    });

    var tms = [TrustManager.$new()];
    var initOverload = SSLContext.init.overload(
      "[Ljavax.net.ssl.KeyManager;",
      "[Ljavax.net.ssl.TrustManager;",
      "java.security.SecureRandom"
    );
    initOverload.implementation = function (km, tm, sr) {
      console.log("[ssl-unpin] SSLContext.init overridden with trust-all manager");
      initOverload.call(this, km, tms, sr);
    };
  } catch (e) {
    console.log("[ssl-unpin] SSLContext hook failed: " + e);
  }

  console.log("[ssl-unpin] done");
});
