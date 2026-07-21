/* viz/app/data.js — bundle loading + decoding (viz/PLAN.md §3.1, §5).
 *
 * Classic script, IIFE-namespaced (window.VIZ.data). Zero dependencies,
 * zero network: bundles arrive as committed .js wrappers
 * (window.VIZ_DATA["<name>"] = base64(gzip-or-plain canonical JSON)),
 * loaded by script-tag injection; payloads are gunzipped with the native
 * DecompressionStream. Encoding is discriminated by the gzip magic bytes
 * after base64 decode — never by configuration.
 *
 * Array transport (§3.1): {dtype: "f4"|"f8"|"u1", shape, b64} —
 * little-endian row-major raw bytes, decoded here with explicit
 * little-endian reads so byte order is never platform-implicit.
 */
(function () {
  "use strict";

  var SUPPORTED_SCHEMA_VERSION = 1; // readers refuse versions they do not implement

  var cache = Object.create(null); // name -> Promise<bundle>

  function b64ToBytes(b64) {
    var bin = atob(b64);
    var out = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
    return out;
  }

  function gunzip(bytes) {
    if (typeof DecompressionStream === "undefined") {
      return Promise.reject(new Error(
        "native DecompressionStream is unavailable in this browser — " +
        "the viz layer does not vendor a decompression library " +
        "(viz/PLAN.md §3.1); use a browser with DecompressionStream support"
      ));
    }
    var ds = new DecompressionStream("gzip");
    var stream = new Blob([bytes]).stream().pipeThrough(ds);
    return new Response(stream).arrayBuffer().then(function (buf) {
      return new Uint8Array(buf);
    });
  }

  function decodeBlob(name) {
    var b64 = window.VIZ_DATA && window.VIZ_DATA[name];
    if (typeof b64 !== "string") {
      return Promise.reject(new Error("bundle not loaded: " + name));
    }
    var bytes = b64ToBytes(b64);
    var isGzip = bytes.length >= 2 && bytes[0] === 0x1f && bytes[1] === 0x8b;
    var plain = isGzip ? gunzip(bytes) : Promise.resolve(bytes);
    return plain.then(function (raw) {
      var bundle = JSON.parse(new TextDecoder("utf-8").decode(raw));
      var v = bundle.viz_bundle_schema_version;
      if (v !== SUPPORTED_SCHEMA_VERSION) {
        throw new Error(
          "bundle " + name + " has schema version " + v +
          "; this reader implements version " + SUPPORTED_SCHEMA_VERSION +
          " only and refuses unknown versions (stable-keys contract)"
        );
      }
      return bundle;
    });
  }

  function injectScript(src) {
    return new Promise(function (resolve, reject) {
      var el = document.createElement("script");
      el.src = src;
      el.onload = function () { resolve(); };
      el.onerror = function () {
        reject(new Error("failed to load script: " + src));
      };
      document.head.appendChild(el);
    });
  }

  /* getBundle("scenario/<id>" | "bases/<id>" | "index") -> Promise<bundle>.
   * Injects data/<name>.js on first use; parsed bundles are cached. */
  function getBundle(name) {
    if (!(name in cache)) {
      var ready = (window.VIZ_DATA && typeof window.VIZ_DATA[name] === "string")
        ? Promise.resolve()
        : injectScript("data/" + name + ".js");
      cache[name] = ready.then(function () { return decodeBlob(name); });
    }
    return cache[name];
  }

  /* decodeArray({dtype, shape, b64}) -> {shape, data: typed array}
   * (explicit little-endian; row-major as transported). */
  function decodeArray(obj) {
    var bytes = b64ToBytes(obj.b64);
    var view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
    var n = obj.shape.reduce(function (a, b) { return a * b; }, 1);
    var data;
    var i;
    if (obj.dtype === "f4") {
      data = new Float32Array(n);
      for (i = 0; i < n; i++) data[i] = view.getFloat32(4 * i, true);
    } else if (obj.dtype === "f8") {
      data = new Float64Array(n);
      for (i = 0; i < n; i++) data[i] = view.getFloat64(8 * i, true);
    } else if (obj.dtype === "u1") {
      data = bytes.slice(0, n);
    } else {
      throw new Error("unknown array dtype: " + obj.dtype);
    }
    return { shape: obj.shape.slice(), data: data };
  }

  window.VIZ = window.VIZ || {};
  window.VIZ.data = {
    SUPPORTED_SCHEMA_VERSION: SUPPORTED_SCHEMA_VERSION,
    getBundle: getBundle,
    decodeArray: decodeArray
  };
})();
