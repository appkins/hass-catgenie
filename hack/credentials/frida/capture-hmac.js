/*
 * capture-hmac.js
 *
 * The most direct way to get what the integration needs.
 *
 * signing.py only ever uses the *derived* 32-char HMAC key:
 *     HMAC_KEY = "Yt" + secret[56:84] + "x3"
 * and signs messages with HmacSHA256. By hooking javax.crypto.Mac we capture
 * that key (and every signed message) straight out of memory — no need to crack
 * the Keystore at all.
 *
 * From the captured 32-char key you can reconstruct a working `secret` for the
 * config flow:  secret = ("0" * 56) + key[2:30]      # key[2:30] == secret[56:84]
 * (signing.py slices [56:84], so the first 56 chars are irrelevant.)
 *
 * Usage:
 *   frida -U -f com.petnovations -l capture-hmac.js
 */

Java.perform(function () {
  console.log("[hmac] installing hooks");

  var Mac = Java.use("javax.crypto.Mac");
  var SecretKeySpec = Java.use("javax.crypto.spec.SecretKeySpec");
  var String = Java.use("java.lang.String");

  function bytesToString(bytes) {
    try {
      return String.$new(bytes).toString();
    } catch (e) {
      return "<non-utf8>";
    }
  }

  function bytesToHex(bytes) {
    var hex = "";
    for (var i = 0; i < bytes.length; i++) {
      var b = bytes[i] & 0xff;
      hex += ("0" + b.toString(16)).slice(-2);
    }
    return hex;
  }

  // Capture the key at Mac.init(Key)
  Mac.init.overload("java.security.Key").implementation = function (key) {
    try {
      var algo = this.getAlgorithm();
      if (algo && algo.toLowerCase().indexOf("hmac") >= 0) {
        var enc = Java.cast(key, SecretKeySpec).getEncoded();
        var keyStr = bytesToString(enc);
        console.log("\n[hmac] ===== Mac.init =====");
        console.log("[hmac] algorithm : " + algo);
        console.log("[hmac] key (utf8): " + keyStr);
        console.log("[hmac] key (hex) : " + bytesToHex(enc));
        if (keyStr.length === 32) {
          console.log("[hmac] >>> secret[56:84] = " + keyStr.substring(2, 30));
          console.log(
            '[hmac] >>> config "secret" = ' +
              "0".repeat(56) +
              keyStr.substring(2, 30)
          );
        }
      }
    } catch (e) {
      console.log("[hmac] init hook error: " + e);
    }
    return this.init(key);
  };

  // Capture the signed message at Mac.doFinal(byte[])
  Mac.doFinal.overload("[B").implementation = function (input) {
    var algo = this.getAlgorithm();
    if (algo && algo.toLowerCase().indexOf("hmac") >= 0) {
      console.log("[hmac] doFinal message: " + bytesToString(input));
    }
    return this.doFinal(input);
  };

  console.log("[hmac] done — trigger a device refresh / command in the app");
});
