performance.mark("js-parse-end:43444-636052f37ac382a0.js");
"use strict";
(globalThis.webpackChunk_github_ui_github_ui = globalThis.webpackChunk_github_ui_github_ui || []).push([
  ["43444"], {
    21744(e, t, n) {
      function o() {
        if (!(this instanceof o)) return new o;
        this.size = 0, this.uid = 0, this.selectors = [], this.selectorObjects = {}, this.indexes = Object.create(this.indexes), this.activeIndexes = []
      }
      n.d(t, {
        h: () => A,
        on: () => S
      });
      var r, i = window.document.documentElement,
        a = i.matches || i.webkitMatchesSelector || i.mozMatchesSelector || i.oMatchesSelector || i.msMatchesSelector;
      o.prototype.matchesSelector = function(e, t) {
        return a.call(e, t)
      }, o.prototype.querySelectorAll = function(e, t) {
        return t.querySelectorAll(e)
      }, o.prototype.indexes = [];
      var s = /^#((?:[\w\u00c0-\uFFFF\-]|\\.)+)/g;
      o.prototype.indexes.push({
        name: "ID",
        selector: function(e) {
          var t;
          if (t = e.match(s)) return t[0].slice(1)
        },
        element: function(e) {
          if (e.id) return [e.id]
        }
      });
      var l = /^\.((?:[\w\u00c0-\uFFFF\-]|\\.)+)/g;
      o.prototype.indexes.push({
        name: "CLASS",
        selector: function(e) {
          var t;
          if (t = e.match(l)) return t[0].slice(1)
        },
        element: function(e) {
          var t = e.className;
          if (t) {
            if ("string" == typeof t) return t.split(/\s/);
            else if ("object" == typeof t && "baseVal" in t) return t.baseVal.split(/\s/)
          }
        }
      });
      var c = /^((?:[\w\u00c0-\uFFFF\-]|\\.)+)/g;
      o.prototype.indexes.push({
        name: "TAG",
        selector: function(e) {
          var t;
          if (t = e.match(c)) return t[0].toUpperCase()
        },
        element: function(e) {
          return [e.nodeName.toUpperCase()]
        }
      }), o.prototype.indexes.default = {
        name: "UNIVERSAL",
        selector: function() {
          return !0
        },
        element: function() {
          return [!0]
        }
      }, r = "function" == typeof window.Map ? window.Map : function() {
        function e() {
          this.map = {}
        }
        return e.prototype.get = function(e) {
          return this.map[e + " "]
        }, e.prototype.set = function(e, t) {
          this.map[e + " "] = t
        }, e
      }();
      var u = /((?:\((?:\([^()]+\)|[^()]+)+\)|\[(?:\[[^\[\]]*\]|['"][^'"]*['"]|[^\[\]'"]+)+\]|\\.|[^ >+~,(\[\\]+)+|[>+~])(\s*,\s*)?((?:.|\r|\n)*)/g;

      function d(e, t) {
        var n, o, r, i, a, s, l = (e = e.slice(0).concat(e.default)).length,
          c = t,
          d = [];
        do
          if (u.exec(""), (r = u.exec(c)) && (c = r[3], r[2] || !c)) {
            for (n = 0; n < l; n++)
              if (a = (s = e[n]).selector(r[1])) {
                for (o = d.length, i = !1; o--;)
                  if (d[o].index === s && d[o].key === a) {
                    i = !0;
                    break
                  } i || d.push({
                  index: s,
                  key: a
                });
                break
              }
          } while (r);
        return d
      }

      function h(e, t) {
        return e.id - t.id
      }
      o.prototype.logDefaultIndexUsed = function() {}, o.prototype.add = function(e, t) {
        var n, o, i, a, s, l, c, u, h = this.activeIndexes,
          f = this.selectors,
          p = this.selectorObjects;
        if ("string" == typeof e) {
          for (o = 0, p[(n = {
              id: this.uid++,
              selector: e,
              data: t
            }).id] = n, c = d(this.indexes, e); o < c.length; o++) a = (u = c[o]).key, (s = function(e, t) {
            var n, o, r;
            for (n = 0, o = e.length; n < o; n++)
              if (r = e[n], t.isPrototypeOf(r)) return r
          }(h, i = u.index)) || ((s = Object.create(i)).map = new r, h.push(s)), i === this.indexes.default && this.logDefaultIndexUsed(n), (l = s.map.get(a)) || (l = [], s.map.set(a, l)), l.push(n);
          this.size++, f.push(e)
        }
      }, o.prototype.remove = function(e, t) {
        if ("string" == typeof e) {
          var n, o, r, i, a, s, l, c, u = this.activeIndexes,
            h = this.selectors = [],
            f = this.selectorObjects,
            p = {},
            m = 1 == arguments.length;
          for (r = 0, n = d(this.indexes, e); r < n.length; r++)
            for (o = n[r], i = u.length; i--;)
              if (s = u[i], o.index.isPrototypeOf(s)) {
                if (l = s.map.get(o.key))
                  for (a = l.length; a--;)(c = l[a]).selector === e && (m || c.data === t) && (l.splice(a, 1), p[c.id] = !0);
                break
              } for (r in p) delete f[r], this.size--;
          for (r in f) h.push(f[r].selector)
        }
      }, o.prototype.queryAll = function(e) {
        if (!this.selectors.length) return [];
        var t, n, o, r, i, a, s, l, c = {},
          u = [],
          d = this.querySelectorAll(this.selectors.join(", "), e);
        for (t = 0, o = d.length; t < o; t++)
          for (n = 0, i = d[t], r = (a = this.matches(i)).length; n < r; n++) c[(l = a[n]).id] ? s = c[l.id] : (s = {
            id: l.id,
            selector: l.selector,
            data: l.data,
            elements: []
          }, c[l.id] = s, u.push(s)), s.elements.push(i);
        return u.sort(h)
      }, o.prototype.matches = function(e) {
        if (!e) return [];
        var t, n, o, r, i, a, s, l, c, u, d, f = this.activeIndexes,
          p = {},
          m = [];
        for (t = 0, r = f.length; t < r; t++)
          if (l = (s = f[t]).element(e)) {
            for (n = 0, i = l.length; n < i; n++)
              if (c = s.map.get(l[n]))
                for (o = 0, a = c.length; o < a; o++) !p[d = (u = c[o]).id] && this.matchesSelector(e, u.selector) && (p[d] = !0, m.push(u))
          } return m.sort(h)
      };
      var f = {},
        p = {},
        m = new WeakMap,
        g = new WeakMap,
        b = new WeakMap,
        y = Object.getOwnPropertyDescriptor(Event.prototype, "currentTarget");

      function w(e, t, n) {
        var o = e[t];
        return e[t] = function() {
          return n.apply(e, arguments), o.apply(e, arguments)
        }, e
      }

      function v() {
        m.set(this, !0)
      }

      function k() {
        m.set(this, !0), g.set(this, !0)
      }

      function C() {
        return b.get(this) || null
      }

      function x(e, t) {
        y && Object.defineProperty(e, "currentTarget", {
          configurable: !0,
          enumerable: !0,
          get: t || y.get
        })
      }

      function E(e) {
        if (function(e) {
            try {
              return e.eventPhase, !0
            } catch (e) {
              return !1
            }
          }(e)) {
          var t = (1 === e.eventPhase ? p : f)[e.type];
          if (t) {
            var n = function(e, t, n) {
              var o = [],
                r = t;
              do {
                if (1 !== r.nodeType) break;
                var i = e.matches(r);
                if (i.length) {
                  var a = {
                    node: r,
                    observers: i
                  };
                  n ? o.unshift(a) : o.push(a)
                }
              } while (r = r.parentElement);
              return o
            }(t, e.target, 1 === e.eventPhase);
            if (n.length) {
              w(e, "stopPropagation", v), w(e, "stopImmediatePropagation", k), x(e, C);
              for (var o = 0, r = n.length; o < r && !m.get(e); o++) {
                var i = n[o];
                b.set(e, i.node);
                for (var a = 0, s = i.observers.length; a < s && !g.get(e); a++) i.observers[a].data.call(i.node, e)
              }
              b.delete(e), x(e)
            }
          }
        }
      }

      function S(e, t, n) {
        var r = arguments.length > 3 && void 0 !== arguments[3] ? arguments[3] : {},
          i = !!r.capture,
          a = i ? p : f,
          s = a[e];
        s || (s = new o, a[e] = s, document.addEventListener(e, E, i)), s.add(t, n)
      }

      function A(e, t, n) {
        return e.dispatchEvent(new CustomEvent(t, {
          bubbles: !0,
          cancelable: !0,
          detail: n
        }))
      }
    },
    94571(e, t, n) {
      let o;
      n.d(t, {
        Se: () => E,
        FB: () => d,
        p_: () => _,
        CF: () => m,
        aC: () => F,
        zV: () => $
      });
      let r = new WeakSet,
        i = new WeakMap;

      function a(e = document) {
        if (i.has(e)) return i.get(e);
        let t = !1,
          n = new MutationObserver(e => {
            for (let t of e)
              if ("attributes" === t.type && t.target instanceof Element) u(t.target);
              else if ("childList" === t.type && t.addedNodes.length)
              for (let e of t.addedNodes) e instanceof Element && s(e)
          });
        n.observe(e, {
          childList: !0,
          subtree: !0,
          attributeFilter: ["data-action"]
        });
        let o = {
          get closed() {
            return t
          },
          unsubscribe() {
            t = !0, i.delete(e), n.disconnect()
          }
        };
        return i.set(e, o), o
      }

      function s(e) {
        for (let t of e.querySelectorAll("[data-action]")) u(t);
        e instanceof Element && e.hasAttribute("data-action") && u(e)
      }

      function l(e) {
        let t = e.currentTarget;
        for (let n of c(t))
          if (e.type === n.type) {
            let o = t.closest(n.tag);
            r.has(o) && "function" == typeof o[n.method] && o[n.method](e);
            let i = t.getRootNode();
            if (i instanceof ShadowRoot && r.has(i.host) && i.host.matches(n.tag)) {
              let t = i.host;
              "function" == typeof t[n.method] && t[n.method](e)
            }
          }
      }

      function* c(e) {
        for (let t of (e.getAttribute("data-action") || "").trim().split(/\s+/)) {
          let e = t.lastIndexOf(":"),
            n = Math.max(0, t.lastIndexOf("#")) || t.length;
          yield {
            type: t.slice(0, e),
            tag: t.slice(e + 1, n),
            method: t.slice(n + 1) || "handleEvent"
          }
        }
      }

      function u(e) {
        for (let t of c(e)) e.addEventListener(t.type, l)
      }

      function d(e, t) {
        let n = e.tagName.toLowerCase();
        if (e.shadowRoot) {
          for (let o of e.shadowRoot.querySelectorAll(`[data-target~="${n}.${t}"]`))
            if (!o.closest(n)) return o
        }
        for (let o of e.querySelectorAll(`[data-target~="${n}.${t}"]`))
          if (o.closest(n) === e) return o
      }
      let h = e => String("symbol" == typeof e ? e.description : e).replace(/([A-Z]($|[a-z]))/g, "-$1").replace(/--/g, "-").replace(/^-|-$/, "").toLowerCase(),
        f = (e, t = "property") => {
          let n = h(e);
          if (!n.includes("-")) throw new DOMException(`${t}: ${String(e)} is not a valid ${t} name`, "SyntaxError");
          return n
        },
        p = "attr";

      function m(e, t) {
        O(e, p).add(t)
      }
      let g = new WeakSet;

      function b(e, t) {
        if (g.has(e)) return;
        g.add(e);
        let n = Object.getPrototypeOf(e),
          o = n?.constructor?.attrPrefix ?? "data-";
        for (let r of (t || (t = O(n, p)), t)) {
          let t = e[r],
            n = f(`${o}${r}`),
            i = {
              configurable: !0,
              get() {
                return this.getAttribute(n) || ""
              },
              set(e) {
                this.setAttribute(n, e || "")
              }
            };
          "number" == typeof t ? i = {
            configurable: !0,
            get() {
              return Number(this.getAttribute(n) || 0)
            },
            set(e) {
              this.setAttribute(n, e)
            }
          } : "boolean" == typeof t && (i = {
            configurable: !0,
            get() {
              return this.hasAttribute(n)
            },
            set(e) {
              this.toggleAttribute(n, e)
            }
          }), Object.defineProperty(e, r, i), r in e && !e.hasAttribute(n) && i.set.call(e, t)
        }
      }
      let y = new Map,
        w = new Promise(e => {
          "loading" !== document.readyState ? e() : document.addEventListener("readystatechange", () => e(), {
            once: !0
          })
        }),
        v = new Promise(e => {
          let t = new AbortController;
          t.signal.addEventListener("abort", () => e());
          let n = {
              once: !0,
              passive: !0,
              signal: t.signal
            },
            o = () => t.abort();
          document.addEventListener("mousedown", o, n), document.addEventListener("touchstart", o, n), document.addEventListener("keydown", o, n), document.addEventListener("pointerdown", o, n)
        }),
        k = {
          ready: () => w,
          firstInteraction: () => v,
          visible: e => new Promise(t => {
            let n = new IntersectionObserver(e => {
              for (let o of e)
                if (o.isIntersecting) {
                  t(), n.disconnect();
                  return
                }
            }, {
              rootMargin: "0px 0px 256px 0px",
              threshold: .01
            });
            for (let t of document.querySelectorAll(e)) n.observe(t)
          })
        },
        C = new WeakMap;

      function x(e) {
        cancelAnimationFrame(C.get(e) || 0), C.set(e, requestAnimationFrame(() => {
          for (let t of y.keys()) {
            let n = e instanceof Element && e.matches(t) ? e : e.querySelector(t);
            if (customElements.get(t) || n) {
              let o = n?.getAttribute("data-load-on") || "ready",
                r = o in k ? k[o] : k.ready;
              for (let e of y.get(t) || []) r(t).then(e);
              y.delete(t), C.delete(e)
            }
          }
        }))
      }

      function E(e, t) {
        for (let [n, o] of("string" == typeof e && t && (e = {
            [e]: t
          }), Object.entries(e))) y.has(n) || y.set(n, new Set), y.get(n).add(o);
        S(document)
      }

      function S(e) {
        o || (o = new MutationObserver(e => {
          if (y.size)
            for (let t of e)
              for (let e of t.addedNodes) e instanceof Element && x(e)
        })), x(e), o.observe(e, {
          subtree: !0,
          childList: !0
        })
      }
      let A = Symbol.for("catalyst");
      class I {
        constructor(e, t) {
          const n = this,
            o = e.prototype.connectedCallback;
          e.prototype.connectedCallback = function() {
            n.connectedCallback(this, o)
          };
          const r = e.prototype.disconnectedCallback;
          e.prototype.disconnectedCallback = function() {
            n.disconnectedCallback(this, r)
          };
          const i = e.prototype.attributeChangedCallback;
          e.prototype.attributeChangedCallback = function(e, t, o) {
            n.attributeChangedCallback(this, e, t, o, i)
          };
          let a = e.observedAttributes || [];
          Object.defineProperty(e, "observedAttributes", {
              configurable: !0,
              get() {
                return n.observedAttributes(this, a)
              },
              set(e) {
                a = e
              }
            }),
            function(e) {
              let t = e.observedAttributes || [],
                n = e.attrPrefix ?? "data-",
                o = e => f(`${n}${e}`);
              Object.defineProperty(e, "observedAttributes", {
                configurable: !0,
                get: () => [...O(e.prototype, p)].map(o).concat(t),
                set(e) {
                  t = e
                }
              })
            }(e),
            function(e, t) {
              let n = t || h(e.name).replace(/-element$/, "");
              try {
                window.customElements.define(n, e), window[e.name] = customElements.get(n)
              } catch (e) {
                if (!(e instanceof DOMException && "NotSupportedError" === e.name)) throw e
              }
            }(e, t)
        }
        observedAttributes(e, t) {
          return t
        }
        connectedCallback(e, t) {
          var n, o;
          for (let t of (e.toggleAttribute("data-catalyst", !0), customElements.upgrade(e), e.querySelectorAll("template[data-shadowroot]"))) t.parentElement === e && e.attachShadow({
            mode: "closed" === t.getAttribute("data-shadowroot") ? "closed" : "open"
          }).append(t.content.cloneNode(!0));
          (b(e), r.add(e), e.shadowRoot && (s(o = e.shadowRoot), a(o)), s(e), a(e.ownerDocument), t?.call(e), e.shadowRoot) && (s(n = e.shadowRoot), a(n), S(e.shadowRoot))
        }
        disconnectedCallback(e, t) {
          t?.call(e)
        }
        attributeChangedCallback(e, t, n, o, r) {
          b(e), "data-catalyst" !== t && r && r.call(e, t, n, o)
        }
      }

      function O(e, t) {
        if (!Object.prototype.hasOwnProperty.call(e, A)) {
          let t = e[A],
            n = e[A] = new Map;
          if (t)
            for (let [e, o] of t) n.set(e, new Set(o))
        }
        let n = e[A];
        return n.has(t) || n.set(t, new Set), n.get(t)
      }

      function F(e, t) {
        O(e, "target").add(t), Object.defineProperty(e, t, {
          configurable: !0,
          get() {
            return d(this, t)
          }
        })
      }

      function $(e, t) {
        O(e, "targets").add(t), Object.defineProperty(e, t, {
          configurable: !0,
          get() {
            let e = this.tagName.toLowerCase(),
              n = [];
            if (this.shadowRoot)
              for (let o of this.shadowRoot.querySelectorAll(`[data-targets~="${e}.${t}"]`)) o.closest(e) || n.push(o);
            for (let o of this.querySelectorAll(`[data-targets~="${e}.${t}"]`)) o.closest(e) === this && n.push(o);
            return n
          }
        })
      }

      function _(e) {
        if ("string" == typeof e) return t => {
          new I(t, e)
        };
        new I(e)
      }
    },
    97088(e, t, n) {
      n.d(t, {
        s: () => i
      });
      let o = ["utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "scid"];
      var r = n(36301);
      class i {
        constructor(e) {
          this.options = e, this.eventBatch = [], this.idleCallbackId = null, this.waitTimerId = null, this.onVisibilityChange = () => {
            "hidden" === document.visibilityState && this.flushBatch()
          }, this.boundFlush = () => this.flushBatch(), "u" > typeof document && document.addEventListener("visibilitychange", this.onVisibilityChange), "u" > typeof window && window.addEventListener("pagehide", this.boundFlush)
        }
        get collectorUrl() {
          return this.options.collectorUrl
        }
        get clientId() {
          return this.options.clientId ? this.options.clientId : (0, r.y)()
        }
        get maxBatchSize() {
          return this.options.maxBatchSize ?? 10
        }
        get idleTimeout() {
          return this.options.idleTimeout ?? 1e3
        }
        createEvent(e) {
          return {
            page: location.href,
            title: document.title,
            context: {
              ...this.options.baseContext,
              ... function() {
                let e = {};
                try {
                  for (let [t, n] of new URLSearchParams(window.location.search)) {
                    let r = t.toLowerCase();
                    o.includes(r) && (e[r] = n)
                  }
                  return e
                } catch (e) {
                  return {}
                }
              }(),
              ...e
            }
          }
        }
        sendPageView(e) {
          let t = this.createEvent(e);
          this.send({
            page_views: [t]
          })
        }
        sendEvent(e, t) {
          let n = {
            ...this.createEvent(t),
            type: e
          };
          this.send({
            events: [n]
          })
        }
        sendBatchedEvent(e, t) {
          let n = {
            ...this.createEvent(t),
            type: e
          };
          this.eventBatch.push(n), this.eventBatch.length >= this.maxBatchSize ? this.flushBatch() : this.scheduleFlush()
        }
        flushBatch() {
          if (0 === this.eventBatch.length) return;
          this.cancelScheduledFlush();
          let e = this.eventBatch;
          this.eventBatch = [], this.send({
            events: e
          })
        }
        destroy() {
          this.flushBatch(), "u" > typeof document && document.removeEventListener("visibilitychange", this.onVisibilityChange), "u" > typeof window && window.removeEventListener("pagehide", this.boundFlush)
        }
        scheduleFlush() {
          null === this.idleCallbackId && null === this.waitTimerId && (this.waitTimerId = setTimeout(() => {
            this.waitTimerId = null, "function" == typeof requestIdleCallback ? this.idleCallbackId = requestIdleCallback(this.boundFlush) : this.boundFlush()
          }, this.idleTimeout))
        }
        cancelScheduledFlush() {
          null !== this.idleCallbackId && ("function" == typeof cancelIdleCallback && cancelIdleCallback(this.idleCallbackId), this.idleCallbackId = null), null !== this.waitTimerId && (clearTimeout(this.waitTimerId), this.waitTimerId = null)
        }
        send({
          page_views: e,
          events: t
        }) {
          let n = JSON.stringify({
            client_id: this.clientId,
            page_views: e,
            events: t,
            request_context: {
              referrer: function() {
                let e;
                try {
                  e = window.top.document.referrer
                } catch (t) {
                  if (window.parent) try {
                    e = window.parent.document.referrer
                  } catch (e) {}
                }
                return "" === e && (e = document.referrer), e
              }(),
              user_agent: navigator.userAgent,
              screen_resolution: function() {
                try {
                  return `${screen.width}x${screen.height}`
                } catch (e) {
                  return "unknown"
                }
              }(),
              browser_resolution: function() {
                let e = 0,
                  t = 0;
                try {
                  return "number" == typeof window.innerWidth ? (t = window.innerWidth, e = window.innerHeight) : null != document.documentElement && null != document.documentElement.clientWidth ? (t = document.documentElement.clientWidth, e = document.documentElement.clientHeight) : null != document.body && null != document.body.clientWidth && (t = document.body.clientWidth, e = document.body.clientHeight), `${t}x${e}`
                } catch (e) {
                  return "unknown"
                }
              }(),
              browser_languages: navigator.languages ? navigator.languages.join(",") : navigator.language || "",
              pixel_ratio: window.devicePixelRatio,
              timestamp: Date.now(),
              tz_seconds: -60 * new Date().getTimezoneOffset()
            }
          });
          try {
            if (navigator.sendBeacon) return void navigator.sendBeacon(this.collectorUrl, n)
          } catch {}
          fetch(this.collectorUrl, {
            method: "POST",
            cache: "no-cache",
            headers: {
              "Content-Type": "application/json"
            },
            body: n,
            keepalive: !1
          })
        }
      }
    },
    70837(e, t, n) {
      n.d(t, {
        O: () => o
      });

      function o(e = "ha") {
        let t, n = {};
        for (let o of Array.from(document.head.querySelectorAll(`meta[name^="${e}-"]`))) {
          let {
            name: r,
            content: i
          } = o, a = r.replace(`${e}-`, "").replace(/-/g, "_");
          "url" === a ? t = i : n[a] = i
        }
        if (!t) throw Error(`AnalyticsClient ${e}-url meta tag not found`);
        return {
          collectorUrl: t,
          ...Object.keys(n).length > 0 ? {
            baseContext: n
          } : {}
        }
      }
    }
  }
]);
//# sourceMappingURL=43444-636052f37ac382a0-f8d9ebea8ba7f2b7.js.map