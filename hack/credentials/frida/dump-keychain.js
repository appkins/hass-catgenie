/*
 * dump-keychain.js
 *
 * Recover the raw 84-character account secret from react-native-keychain.
 * The secret is stored via getGenericPassword() and decrypted through the
 * Android Keystore (javax.crypto.Cipher). On an emulator the Keystore is
 * software-backed, so hooking Cipher.doFinal reveals the plaintext.
 *
 * Two strategies run at once:
 *   1. Hook the react-native-keychain native bridge result directly.
 *   2. Hook Cipher.doFinal and log any decrypt output that looks like the
 *      84-char secret (or JSON containing it).
 *
 * Usage:
 *   frida -U -f com.petnovations -l dump-keychain.js
 */

Java.perform(function () {
  console.log("[keychain] installing hooks");

  var JavaString = Java.use("java.lang.String");

  function toUtf8(bytes) {
    try {
      return JavaString.$new(bytes).toString();
    } catch (e) {
      return null;
    }
  }

  // ---- 1. Cipher.doFinal: catch the decrypted secret ----
  try {
    var Cipher = Java.use("javax.crypto.Cipher");

    function logCipherResult(tag, out) {
      if (!out) return;
      var s = toUtf8(out);
      if (!s) return;
      // The secret is 84 printable chars; also surface short keychain blobs.
      if (s.length >= 16 && s.length <= 512 && /[\x20-\x7e]{16,}/.test(s)) {
        console.log("\n[keychain] " + tag + " (len " + s.length + "): " + s);
      }
    }

    Cipher.doFinal.overload().implementation = function () {
      var out = this.doFinal();
      logCipherResult("Cipher.doFinal()", out);
      return out;
    };
    Cipher.doFinal.overload("[B").implementation = function (input) {
      var out = this.doFinal(input);
      logCipherResult("Cipher.doFinal(byte[])", out);
      return out;
    };
  } catch (e) {
    console.log("[keychain] Cipher hook failed: " + e);
  }

  // ---- 2. react-native-keychain native module reads + WRITES ----
  // Writes (setGenericPassword) tell us whether the secret is re-populated
  // after a state clear, and what value is stored.
  ["com.oblador.keychain.KeychainModule"].forEach(function (cls) {
    try {
      var KeychainModule = Java.use(cls);

      KeychainModule.getGenericPasswordForOptions.overloads.forEach(function (ov) {
        ov.implementation = function () {
          console.log("[keychain] READ getGenericPasswordForOptions");
          return ov.apply(this, arguments);
        };
      });

      // setGenericPasswordForOptions(options/service, username, password, ...)
      if (KeychainModule.setGenericPasswordForOptions) {
        KeychainModule.setGenericPasswordForOptions.overloads.forEach(function (ov) {
          ov.implementation = function () {
            console.log("\n[keychain] WRITE setGenericPasswordForOptions:");
            for (var i = 0; i < arguments.length; i++) {
              try {
                console.log("[keychain]   arg[" + i + "] = " + arguments[i]);
              } catch (e) {}
            }
            return ov.apply(this, arguments);
          };
        });
      }
    } catch (e) {
      console.log("[keychain] " + cls + " not present");
    }
  });

  console.log("[keychain] done — open the app so it reads/writes the keychain");
});
