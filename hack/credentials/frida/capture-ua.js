Java.perform(function () {
  try {
    var Version = Java.use("okhttp3.internal.Version");
    console.log("[ua] okhttp default User-Agent = " + Version.userAgent());
  } catch (e) {
    try {
      var V2 = Java.use("okhttp3.internal.Version");
      console.log("[ua] userAgent field = " + V2.userAgent.value);
    } catch (e2) { console.log("[ua] Version lookup failed: " + e + " / " + e2); }
  }
  try {
    var Bridge = Java.use("okhttp3.internal.http.BridgeInterceptor");
    Bridge.intercept.implementation = function (chain) {
      var req = chain.request();
      console.log("[ua] " + req.url() + " app-set UA = " + req.header("User-Agent"));
      return this.intercept(chain);
    };
  } catch (e) { console.log("[ua] bridge hook failed: " + e); }
});
