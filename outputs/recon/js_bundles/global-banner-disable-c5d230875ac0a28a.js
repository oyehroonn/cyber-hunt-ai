performance.mark("js-parse-end:global-banner-disable-c5d230875ac0a28a.js");
(() => {
  var e = {
      35684() {
        let e = document.cookie.match(RegExp("(?:^|;\\s*)disabled_global_site_banners\\s*=\\s*([^;]+)")),
          t = e ? e[1] : null;
        if (t) {
          let e = t.split(",") || [];
          for (let t = 0; t < e.length; t++) {
            let r = document.getElementById(e[t] || "");
            r && (r.hidden = !0)
          }
        }
      }
    },
    t = {};

  function r(o) {
    var n = t[o];
    if (void 0 !== n) return n.exports;
    var l = t[o] = {
      exports: {}
    };
    return e[o](l, l.exports, r), l.exports
  }
  r.n = e => {
    var t = e && e.__esModule ? () => e.default : () => e;
    return r.d(t, {
      a: t
    }), t
  }, r.d = (e, t) => {
    for (var o in t) r.o(t, o) && !r.o(e, o) && Object.defineProperty(e, o, {
      enumerable: !0,
      get: t[o]
    })
  }, r.o = (e, t) => Object.prototype.hasOwnProperty.call(e, t), r.rv = () => "1.7.7", r.ruid = "bundler=rspack@1.7.7", (() => {
    "use strict";
    r(35684)
  })()
})();
//# sourceMappingURL=global-banner-disable-c5d230875ac0a28a-ef56468e8076feca.js.map