performance.mark("js-parse-end:22445-66cdb57aa2f9e31c.js");
(globalThis.webpackChunk_github_ui_github_ui = globalThis.webpackChunk_github_ui_github_ui || []).push([
  ["22445"], {
    15785(e, t, r) {
      "use strict";
      var n = r(21744),
        o = r(21403),
        a = r(25649),
        i = r(66743);
      let c = "data-analytics-event",
        l = "data-analytics-visible",
        s = `a:not([${c}]), button:not([${c}]), [${c}]`,
        u = `[${l}]`;

      function d(e, t) {
        return e.tagName.toLowerCase() === t
      }

      function m(e) {
        return {
          text: e.textContent || e.getAttribute("aria-label") || "",
          target: e.href
        }
      }

      function f(e) {
        let t = e.closest("form");
        return {
          text: e.textContent || e.getAttribute("aria-label") || "",
          role: e.getAttribute("type") || e.getAttribute("role") || "button",
          ...e.value && {
            value: e.value
          },
          ...t && {
            formAction: t.getAttribute("action") || ""
          }
        }
      }

      function h(e) {
        if (!e) return {};
        let t = JSON.parse(e),
          {
            label: r
          } = t;
        return {
          ... function(e) {
            if (!e) return {};
            let t = {};
            for (let r of e.split(";").map(e => e.trim())) {
              let [e, n] = r.split(":");
              e && (t[e.trim()] = n?.trim() || e.trim())
            }
            return t
          }(r),
          ...t
        }
      }(0, n.on)("click", s, e => {
        if (e && e.currentTarget) try {
          var t;
          (0, i.BI)("analytics.click", (t = e.currentTarget, {
            ...d(t, "a") && m(t),
            ...d(t, "button") && f(t),
            ...h(t.getAttribute(c))
          })), d(e.currentTarget, "details") && e.currentTarget.removeAttribute(c)
        } catch (e) {
          (0, a.N7)(e)
        }
      });
      let p = new IntersectionObserver(function(e) {
        for (let r of e)
          if (r.isIntersecting) try {
            var t;
            (0, i.BI)("analytics.visible", (t = r.target, {
              ...d(t, "a") && m(t),
              ...d(t, "button") && f(t),
              ...h(t.getAttribute(l))
            })), p.unobserve(r.target)
          } catch (e) {
            (0, a.N7)(e)
          }
      }, {
        rootMargin: "0% 0% -30% 0%",
        threshold: 0
      });
      (0, o.lB)(u, e => {
        p.observe(e)
      })
    },
    63222(e, t, r) {
      "use strict";
      var n = r(21403);
      (0, n.lB)(".js-nav-padding-recalculate", e => {
        let t = !1,
          r = 0,
          n = document.querySelector(".js-header-menu"),
          o = document.querySelector(".js-header-wrapper"),
          a = document.querySelector(".js-header"),
          i = document.querySelectorAll(".js-prevent-focus-on-mobile-nav"),
          c = e => {
            let t;
            return () => {
              t && cancelAnimationFrame(t), t = requestAnimationFrame(e)
            }
          },
          l = () => {
            let e = o?.clientHeight;
            e !== r && (document.documentElement.style.setProperty("--header-wrapper-height", `${e}px`), r = e)
          },
          s = () => {
            if (!n || !o || !a) return;
            let e = o.clientHeight,
              t = "absolute" === getComputedStyle(a).position,
              r = "fixed" === getComputedStyle(o).position;
            t && (e += a.clientHeight), r || (e -= window.scrollY), n.style.setProperty("padding-top", `${e}px`)
          },
          u = c(s);
        if (o && "fixed" === getComputedStyle(o).position) {
          let e = c(l);
          new ResizeObserver(() => {
            e()
          }).observe(o), l()
        }
        let d = r => {
          "Escape" === r.key && t && (e.click(), e.focus())
        };
        window.removeEventListener("resize", s), document.removeEventListener("keydown", d);
        let m = () => {
          t || s()
        };
        document.addEventListener("global-banner:close", () => {
          t && s()
        }), e.addEventListener("mousedown", m), e.addEventListener("touchstart", m, {
          passive: !0
        }), e.addEventListener("keydown", m), a.addEventListener("details:toggled", e => {
          if (e.target === a) {
            if (t = e.detail.open) {
              if (window.addEventListener("resize", u), document.addEventListener("keydown", d), i)
                for (let e of i) e.setAttribute("tabindex", "-1")
            } else if (window.removeEventListener("resize", u), document.removeEventListener("keydown", d), i)
              for (let e of i) e.removeAttribute("tabindex")
          }
        }, !1)
      }), (0, n.lB)('#__primerPortalRoot__, .js-header [data-target="deferred-side-panel.panel"]', e => {
        e.setAttribute("data-color-mode", "light"), e.setAttribute("data-light-theme", "light"), e.setAttribute("data-dark-theme", "dark")
      }), (0, n.lB)(".js-header-menu-focus-trap", e => {
        e.addEventListener("focusin", () => {
          let e = document.querySelector(".js-header-menu-toggle");
          e && e.focus()
        })
      }), (0, n.lB)(".js-header-overlay-fixed", () => {
        let e = document.querySelector(".js-header-wrapper"),
          t = document.createElement("div");
        t.setAttribute("data-scroll-watcher", "true"), e.before(t), new IntersectionObserver(t => {
          e?.setAttribute("data-is-top", `${t[0]?.isIntersecting}`)
        }, {
          rootMargin: "100px 0px 0px 0px"
        }).observe(t)
      })
    },
    51117() {
      new class {
        paramsToOverride;
        queryString;
        collectedParamsMap;
        collectedParams;
        queryRe;
        constructor() {
          if (this.paramsToOverride = ["utm_campaign", "utm_medium", "utm_source", "ocid"], this.queryString = document.location.search, this.collectedParamsMap = {}, this.collectedParams = [], this.queryRe = RegExp(`(${this.paramsToOverride.join("|")})=([^=&]*)`, "gi"), !this.queryString || !this.queryRe.test(this.queryString)) return;
          this.collectParams(), this.bindEvents()
        }
        collectParams() {
          for (let e of this.paramsToOverride) {
            let t = RegExp(`${e}=([^=&]*)`, "i"),
              r = t.exec(this.queryString);
            t.lastIndex = 0, r && r[1] && (this.collectedParamsMap[e] = r[1], this.collectedParams.push(`${e}=${r[1]}`))
          }
        }
        overrideParams(e) {
          let t = e.getAttribute("href"),
            r = "";
          if (!(!t || /^javascript:|^mailto:|^tel:|^#/.test(t))) {
            if (-1 !== t.indexOf("#")) {
              let e = t.split("#");
              if (2 !== e.length) return;
              e[0] && (t = e[0]), e[1] && (r = `#${e[1]}`)
            }
            if (-1 === t.indexOf("?")) t += `?${this.collectedParams.join("&")}`;
            else
              for (let e of this.paramsToOverride) {
                if (!this.collectedParamsMap.hasOwnProperty(e)) continue;
                let r = RegExp(`${e}=([^=&]*)`, "i"),
                  n = r.exec(t);
                if (r.lastIndex = 0, !n) {
                  this.collectedParamsMap.hasOwnProperty(e) && (t += `&${e}=${this.collectedParamsMap[e]}`);
                  continue
                }
                t = t.replace(r, `${e}=${this.collectedParamsMap[e]}`)
              }
            t += r, e.setAttribute("data-override-applied", "true"), e.setAttribute("href", t)
          }
        }
        eventReaction(e) {
          let t = e.target;
          !t || "A" !== t.tagName || t.hasAttribute("data-override-applied") || this.overrideParams(t)
        }
        bindEvents() {
          document.body.addEventListener("mouseenter", this.eventReaction.bind(this), !0), document.body.addEventListener("touchstart", this.eventReaction.bind(this), {
            passive: !0,
            capture: !0
          })
        }
      }
    },
    25649(e, t, r) {
      "use strict";
      let n;
      r.d(t, {
        N7: () => b,
        AW: () => y,
        fE: () => v,
        ff: () => A
      });
      var o = r(36301),
        a = r(63371),
        i = r(7753),
        c = r(24212);

      function l(e) {
        return (0, c.q)(e.stack || "").map(e => ({
          filename: e.file || "",
          function: String(e.methodName),
          lineno: (e.lineNumber || 0).toString(),
          colno: (e.column || 0).toString()
        }))
      }

      function s(e) {
        let t = document.querySelectorAll(e);
        if (t.length > 0) return t[t.length - 1]
      }
      var u = r(58209),
        d = r(26316),
        m = r(97398),
        f = r(41763);
      let h = !1,
        p = 0,
        g = Date.now(),
        v = new Set(["AbortError", "AuthSessionExpiredError", "TypeError", "RateLimitError", "NotAcceptableError", "SecFetchHeaderError", "FetchNetworkError", "NoiseError", "ServiceUnavailableError"]),
        y = new Set(["Failed to fetch", "NetworkError when attempting to fetch resource.", "Unable to perform this operation. Please try again later."]);

      function b(e, t = {}) {
        if (!(e instanceof Error || "object" == typeof e && null !== e && "name" in e && "string" == typeof e.name && "message" in e && "string" == typeof e.message)) {
          if (function(e) {
              if (!e || "boolean" == typeof e || "number" == typeof e) return !0;
              if ("string" == typeof e) {
                if (q.some(t => e.includes(t))) return !0
              } else if ("object" == typeof e && "string" == typeof e.message && "number" == typeof e.code) return !0;
              return !1
            }(e)) return;
          let r = Error(),
            n = function(e) {
              try {
                return JSON.stringify(e)
              } catch {
                return "Unserializable"
              }
            }(e);
          S(w({
            type: "UnknownError",
            value: `Unable to report error, due to a thrown non-Error type: ${typeof e}, with value ${n}`,
            stacktrace: l(r),
            catalogService: document.head?.querySelector('meta[name="current-catalog-service"]')?.content,
            catalogServiceHash: document.head?.querySelector('meta[name="current-catalog-service-hash"]')?.content
          }, t));
          return
        }
        e.name && ("AbortError" === e.name || "RateLimitError" === e.name || "NotAcceptableError" === e.name || "SecFetchHeaderError" === e.name || "FetchNetworkError" === e.name || "NoiseError" === e.name || "ServiceUnavailableError" === e.name && A() || v.has(e.name) && y.has(e.message) || e.name.startsWith("ApiError") && y.has(e.message)) || S(w({
          type: e.name,
          value: e.message,
          stacktrace: l(e),
          catalogService: e.catalogService || globalThis.document?.head?.querySelector('meta[name="current-catalog-service"]')?.content,
          catalogServiceHash: e.catalogServiceHash || globalThis.document?.head?.querySelector('meta[name="current-catalog-service-hash"]')?.content
        }, t))
      }
      async function S(e) {
        let t;
        if (t = Date.now() - g > 2592e5, !(!O && !h && p < 10 && (n ??= (0, a.TT)() && function() {
            let e = d.cg?.history,
              t = d.cg?.location;
            if (!e || !t) return !1;
            try {
              return e.replaceState(e.state, document.title, t.href), !0
            } catch {
              return !1
            }
          }())) || t || (0, i.H)()) return;
        let r = document.head?.querySelector('meta[name="browser-errors-url"]')?.content;
        if (r) {
          if (e.error.stacktrace.some(e => E.test(e.filename) || E.test(e.function))) {
            h = !0;
            return
          }
          p++;
          try {
            await fetch(r, {
              method: "post",
              body: JSON.stringify({
                context: e,
                target: document.head?.querySelector('meta[name="ui-target"]')?.content || "full"
              })
            })
          } catch {}
        }
      }

      function w(e, t = {}) {
        let r, n = {
          ...t
        };
        return n.reactAppName || (n.reactAppName = function(e) {
          let t = function() {
            let e = new Set;
            for (let [t, r] of x)
              for (let n of document.querySelectorAll(t))
                if (n instanceof HTMLElement) {
                  let t = n.getAttribute(r);
                  t && e.add(t)
                } return Array.from(e)
          }();
          if (!t || !t.length || !e || !e.length) return;
          let r = new Set;
          for (let n of e) {
            if (!n || !n.filename) continue;
            let e = n.filename.split(/[\\/]/).pop();
            if (!e || r.has(e)) continue;
            r.add(e);
            let o = t.find(t => e.toLowerCase().includes(t.toLowerCase()));
            if (o) return o
          }
        }(e.stacktrace)), Object.assign({
          error: e,
          sanitizedUrl: `${window.location.protocol}//${window.location.host}${((r=s("meta[name=analytics-location]"))?r.content:window.location.pathname)+function(){let e=s("meta[name=analytics-location-query-strip]"),t="";e||(t=window.location.search);let r=s("meta[name=analytics-location-params]");for(let e of(r&&(t+=(t?"&":"?")+r.content),document.querySelectorAll("meta[name=analytics-param-rename]"))){let r=e.content.split(":",2);t=t.replace(RegExp(`(^|[?&])${r[0]}($|=)`,"g"),`$1${r[1]}$2`)}return t}()}` || window.location.href,
          readyState: document.readyState,
          referrer: (0, m.dR)(),
          timeSinceLoad: Math.round(Date.now() - g),
          user: function() {
            let e = document.head?.querySelector('meta[name="user-login"]')?.content;
            if (e) return e;
            let t = (0, o.y)();
            return `anonymous-${t}`
          }() || void 0,
          actorId: document.head?.querySelector('meta[name="octolytics-actor-id"]')?.content,
          bundler: u.vV,
          ui: "vite-tss" === u.vV,
          release: document.head?.querySelector('meta[name="release"]')?.content,
          pastRequestIds: (0, f.xA)()
        }, n)
      }
      let E = /(chrome|moz|safari)-extension:\/\//;

      function A() {
        return !document.head?.querySelector('meta[name="user-login"]')?.content
      }
      let O = !1;
      d.cg?.addEventListener("pageshow", () => O = !1), d.cg?.addEventListener("pagehide", () => O = !0), "function" == typeof BroadcastChannel && new BroadcastChannel("shared-worker-error").addEventListener("message", e => {
        b(e.data.error)
      });
      let q = ["Object Not Found Matching Id", "Not implemented on this platform", "provider because it's not your default extension"],
        x = [
          ["react-app", "app-name"],
          ["react-partial", "partial-name"]
        ]
    },
    66743(e, t, r) {
      "use strict";
      let n;
      r.d(t, {
        BI: () => E,
        lA: () => S,
        sX: () => w,
        Ti: () => A
      });
      var o = r(70837),
        a = r(97088),
        i = r(35205),
        c = r(26316),
        l = r(51189);
      let s = "font-weight: bold; font-size: 12px;",
        u = new Set(["actor_id", "actor_login", "actor_hash", "referrer", "request_id", "visitor_id", "region_edge", "region_render", "staff", "service", "react", "app_name", "page", "title"]),
        d = new Set(["hpc", "ttfb", "fcp", "lcp", "fid", "inp", "cls", "elementtiming", "longTasks", "longAnimationFrames"]),
        m = new Set(["react", "reactApp", "reactPartials", "featureFlags", "ssr", "controller", "action", "routePattern", "cpu", "domNodes", "previousDomNodes", "navigationId"]);

      function f(e) {
        try {
          return JSON.parse(e)
        } catch {
          return e
        }
      }
      let {
        getItem: h
      } = (0, i.A)("localStorage"), p = "dimension_", g = ["utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "scid"];

      function v(e) {
        try {
          return (0, o.O)(e)
        } catch {
          return
        }
      }
      let y = v("octolytics");

      function b(e) {
        let t = v("octolytics")?.baseContext ?? {};
        if (t)
          for (let [e, r] of(delete t.app_id, delete t.event_url, delete t.host, Object.entries(t))) e.startsWith(p) && (t[e.replace(p, "")] = r, delete t[e]);
        let r = c.XC?.querySelector("meta[name=visitor-payload]");
        for (let [e, n] of(r && Object.assign(t, JSON.parse(atob(r.content))), new URLSearchParams(window.location.search))) g.includes(e.toLowerCase()) && (t[e] = n);
        return t.staff = (0, l.Xl)().toString(), Object.assign(t, e)
      }

      function S(e) {
        n?.sendPageView(b(e))
      }

      function w() {
        return c.XC?.head?.querySelector('meta[name="current-catalog-service"]')?.content
      }

      function E(e, t = {}, {
        batched: r = !1
      } = {}) {
        let o = w(),
          a = o ? {
            service: o
          } : {};
        for (let [e, r] of Object.entries(t)) null != r && (a[e] = `${r}`);
        if (n) {
          let t = e || "unknown",
            o = b(a);
          r ? n.sendBatchedEvent(t, b(a)) : n.sendEvent(t, b(a)), "true" === h("stats-dev-logger") && function(e, t = {}) {
            let r, n = [];
            for (let [e, r] of Object.entries(t)) u.has(e) || n.push([e, f(r)]);
            let o = void 0 !== t.value ? ` ${"number"==typeof(r=f(t.value))?String(Math.round(r)):String(r)}` : "";
            console.groupCollapsed(`%cevent%c ${e}${o}`, "background: #8957e5; color: #fff; padding: 2px 6px; border-radius: 3px; font-weight: bold; font-size: 11px;", s), "web-vital" === e ? function(e) {
              for (let [t, r] of e) d.has(t) ? (console.log(`%c${t}`, s), console.table(r)) : m.has(t) || console.log(`${t}:`, r)
            }(n) : (console.table(Object.fromEntries(n.map(([e, t]) => [e, {
              value: t
            }]))), console.log(Object.fromEntries(n))), console.groupEnd()
          }(t, o)
        }
      }

      function A(e) {
        return Object.fromEntries(Object.entries(e).map(([e, t]) => [e, JSON.stringify(t)]))
      }
      y && (delete y.baseContext, y.idleTimeout = 5e3, y.maxBatchSize = 50, n = new a.s(y))
    },
    41763(e, t, r) {
      "use strict";
      r.d(t, {
        Ex: () => i,
        kt: () => l,
        xA: () => c
      });
      var n = r(26316);
      let o = Array(10).fill(null),
        a = 0;

      function i(e) {
        o[a] = e, a = (a + 1) % 10
      }

      function c() {
        let e = [];
        for (let t = 0; t < 10; t++) {
          let r = o[(a - 1 - t + 10) % 10];
          r && e.push(r)
        }
        return e
      }

      function l() {
        let e = n.XC;
        if (!e) return;
        let t = e.querySelector('meta[name="request-id"]'),
          r = t?.getAttribute("content");
        r && i(r)
      }
    },
    35205(e, t, r) {
      "use strict";
      r.d(t, {
        A: () => i,
        D: () => c
      });
      var n = r(26316),
        o = r(51189);
      class a {
        getItem() {
          return null
        }
        setItem() {}
        removeItem() {}
        clear() {}
        key() {
          return null
        }
        get length() {
          return 0
        }
      }

      function i(e, t = {
        throwQuotaErrorsOnSet: !1
      }, r = n.cg, c = e => e, l = e => e) {
        let s;
        try {
          if (!r) throw Error();
          s = r[e] || new a
        } catch {
          s = new a
        }
        let {
          throwQuotaErrorsOnSet: u
        } = t;

        function d(e) {
          t.sendCacheStats && (0, o.iv)({
            incrementKey: e
          })
        }

        function m(e) {
          try {
            if (s.removeItem(e), t.ttl) {
              let t = `${e}:expiry`;
              s.removeItem(t)
            }
          } catch {}
        }
        return {
          getItem: function(e, t = Date.now()) {
            try {
              let r = s.getItem(e);
              if (!r) return null;
              let n = `${e}:expiry`,
                o = Number(s.getItem(n));
              if (o && t > o) return m(e), m(n), d("SAFE_STORAGE_VALUE_EXPIRED"), null;
              return d("SAFE_STORAGE_VALUE_WITHIN_TTL"), c(r)
            } catch {
              return null
            }
          },
          setItem: function(e, r, n = Date.now()) {
            try {
              if (s.setItem(e, l(r)), t.ttl) {
                let r = `${e}:expiry`,
                  o = n + t.ttl;
                s.setItem(r, o.toString())
              }
            } catch (e) {
              if (u && e instanceof Error && e.message.toLowerCase().includes("quota")) throw e
            }
          },
          removeItem: m,
          clear: () => s.clear(),
          getKeys: function() {
            return Object.keys(s)
          },
          get length() {
            return s.length
          }
        }
      }

      function c(e) {
        return i(e, {
          throwQuotaErrorsOnSet: !1
        }, n.cg, JSON.parse, JSON.stringify)
      }
    },
    11730(e, t, r) {
      "use strict";
      r.d(t, {
        Ai: () => a,
        Gq: () => n,
        SO: () => o
      });
      let {
        getItem: n,
        setItem: o,
        removeItem: a
      } = (0, r(35205).A)("sessionStorage")
    },
    97398(e, t, r) {
      "use strict";
      r.d(t, {
        BW: () => i,
        Ff: () => p,
        HK: () => w,
        JA: () => x,
        LM: () => g,
        Pv: () => O,
        Vy: () => h,
        ZW: () => A,
        dR: () => E,
        di: () => v,
        gc: () => q,
        k9: () => S,
        my: () => b,
        wG: () => y,
        xT: () => f
      });
      var n = r(11730),
        o = r(26316),
        a = r(66953);
      let i = "reload",
        c = "soft-nav:fail",
        l = "soft-nav:fail-referrer",
        s = "soft-nav:referrer",
        u = "soft-nav:marker",
        d = "soft-nav:react-app-name",
        m = "soft-nav:latest-mechanism";

      function f() {
        (0, n.SO)(u, "0"), (0, n.Ai)(s), (0, n.Ai)(c), (0, n.Ai)(l), (0, n.Ai)(d), (0, n.Ai)(m)
      }

      function h(e) {
        (0, n.SO)(u, e)
      }

      function p() {
        (0, n.SO)(u, "0")
      }

      function g() {
        let e = (0, n.Gq)(u);
        return e && "0" !== e
      }

      function v() {
        return (0, n.Gq)(u)
      }

      function y() {
        return !!b()
      }

      function b() {
        return (0, n.Gq)(c)
      }

      function S(e) {
        (0, n.SO)(c, e || i), (0, n.SO)(l, window.location.href)
      }

      function w() {
        (0, n.SO)(s, window.location.href)
      }

      function E() {
        return (0, n.Gq)(s) || document.referrer
      }

      function A() {
        let e = (0, a.f)();
        e ? (0, n.SO)(d, e) : (0, n.Ai)(d)
      }

      function O() {
        return (0, n.Gq)(d)
      }

      function q() {
        return !!o.XC?.querySelector("react-app")?.getAttribute("app-name") || !!o.XC?.querySelector("projects-v2")
      }

      function x(e) {
        (0, n.SO)(m, e)
      }
    }
  }
]);
//# sourceMappingURL=22445-66cdb57aa2f9e31c-82f7355851347526.js.map