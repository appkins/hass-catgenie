/*
 * capture-auth.js
 *
 * Capture the JWT / refresh token without a proxy by hooking OkHttp. Logs the
 * Authorization header on every request and the body of the refreshToken
 * response (which contains `token` and `expiration`).
 *
 * Usage:
 *   frida -U -f com.petnovations -l capture-auth.js
 */

Java.perform(function () {
  console.log("[auth] installing hooks");

  // Log outgoing request URLs + Authorization header.
  try {
    var Request = Java.use("okhttp3.Request");
    Request.header.overload("java.lang.String").implementation = function (name) {
      var val = this.header(name);
      if (name && name.toLowerCase() === "authorization" && val) {
        console.log("\n[auth] Authorization: " + val);
        if (val.indexOf("Bearer ") === 0) {
          console.log("[auth] >>> bearer/refresh token = " + val.substring(7));
        }
      }
      return val;
    };
  } catch (e) {
    console.log("[auth] okhttp3.Request not present: " + e);
  }

  // Log the refreshToken / login response body (new access token + expiration).
  try {
    var ResponseBody = Java.use("okhttp3.ResponseBody");
    ResponseBody.string.implementation = function () {
      var body = this.string();
      try {
        if (
          body &&
          (body.indexOf('"token"') >= 0 ||
            body.indexOf('"refreshToken"') >= 0 ||
            body.indexOf('"expiration"') >= 0)
        ) {
          console.log("\n[auth] response body: " + body);
        }
      } catch (e) {}
      return body;
    };
  } catch (e) {
    console.log("[auth] okhttp3.ResponseBody not present: " + e);
  }

  // Log the FULL request (method, url, every header, body) for the auth-related
  // endpoints, so we can compare exactly what the app sends vs what we generate.
  var INTEREST = ["ums/", "facade/", "device/", "config/", "gateway/", "notification/"];

  function interesting(url) {
    for (var i = 0; i < INTEREST.length; i++) {
      if (url.indexOf(INTEREST[i]) >= 0) return true;
    }
    return false;
  }

  try {
    var OkHttpClient = Java.use("okhttp3.OkHttpClient");
    var Buffer = Java.use("okio.Buffer");
    OkHttpClient.newCall.implementation = function (request) {
      try {
        var url = request.url().toString();
        if (interesting(url)) {
          console.log("\n[auth] ===== " + request.method() + " " + url);
          var headers = request.headers();
          var n = headers.size();
          for (var i = 0; i < n; i++) {
            console.log("[auth]   " + headers.name(i) + ": " + headers.value(i));
          }
          var body = request.body();
          if (body != null) {
            var buf = Buffer.$new();
            body.writeTo(buf); // JSON bodies are replayable (not one-shot)
            console.log("[auth]   body: " + buf.readUtf8());
          }
        }
      } catch (e) {
        console.log("[auth] newCall log error: " + e);
      }
      return this.newCall(request);
    };
  } catch (e) {
    console.log("[auth] okhttp3.OkHttpClient.newCall hook failed: " + e);
  }

  console.log("[auth] done — log in / let the app refresh its session");
});
