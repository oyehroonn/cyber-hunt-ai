performance.mark("js-parse-end:93308-c21d6ff736807846.js");
"use strict";
(globalThis.webpackChunk_github_ui_github_ui = globalThis.webpackChunk_github_ui_github_ui || []).push([
  ["93308"], {
    13937(e, t, n) {
      let r;
      n.d(t, {
        Ax: () => u,
        JW: () => c,
        ZV: () => l
      });
      class i extends Error {
        constructor(e, t) {
          super(e), this.response = t
        }
      }

      function s() {
        let e, t;
        return [new Promise(function(n, r) {
          e = n, t = r
        }), e, t]
      }
      let a = [],
        o = [];

      function l(e) {
        a.push(e)
      }

      function u(e) {
        o.push(e)
      }

      function c(e, t) {
        !r && (r = new Map, "u" > typeof document && document.addEventListener("submit", h));
        let n = r.get(e) || [];
        r.set(e, [...n, t])
      }

      function h(e) {
        if (!(e.target instanceof HTMLFormElement) || e.defaultPrevented) return;
        let t = e.target,
          n = function(e) {
            let t = [],
              n = t => "object" == typeof t ? t === e : "string" == typeof t && e.matches(t);
            for (let e of r.keys())
              if (n(e)) {
                let n = r.get(e) || [];
                t.push(...n)
              } return t
          }(t);
        if (0 === n.length) return;
        let i = function(e, t) {
            let n = {
              method: t?.formMethod || e.method || "GET",
              url: e.action,
              headers: new Headers({
                "X-Requested-With": "XMLHttpRequest"
              }),
              body: null
            };
            if ("GET" === n.method.toUpperCase()) {
              let t = function(e) {
                let t = new URLSearchParams;
                for (let [n, r] of [...new FormData(e).entries()]) t.append(n, r.toString());
                return t.toString()
              }(e);
              t && (n.url += (~n.url.indexOf("?") ? "&" : "?") + t)
            } else n.body = new FormData(e);
            return n
          }(t, e instanceof SubmitEvent ? e.submitter : null),
          [l, u, c] = s();
        e.preventDefault(), p(n, t, i, l).then(async e => {
          if (e) {
            for (let e of o) await e(t);
            f(i).then(u, c).catch(() => {}).then(() => {
              for (let e of a) e(t)
            })
          } else t.submit()
        }, e => {
          t.submit(), setTimeout(() => {
            throw e
          })
        })
      }
      async function p(e, t, n, r) {
        let i = !1;
        for (let a of e) {
          let [e, o] = s(), l = () => (i = !0, o(), r), u = {
            text: l,
            json: () => (n.headers.set("Accept", "application/json"), l()),
            html: () => (n.headers.set("Accept", "text/html"), l())
          };
          await Promise.race([e, a(t, u, n)])
        }
        return i
      }
      async function f(e) {
        let t = await window.fetch(e.url, {
            method: e.method,
            body: null !== e.body ? e.body : void 0,
            headers: e.headers,
            credentials: "same-origin"
          }),
          n = {
            url: t.url,
            status: t.status,
            statusText: t.statusText,
            headers: t.headers,
            text: "",
            get json() {
              let e = JSON.parse(this.text);
              return delete this.json, this.json = e, this.json
            },
            get html() {
              var r, s;
              let e;
              return delete this.html, this.html = (r = document, s = this.text, (e = r.createElement("template")).innerHTML = s, r.importNode(e.content, !0)), this.html
            }
          };
        if (n.text = await t.text(), t.ok) return n;
        throw new i("request failed", n)
      }
    },
    21744(e, t, n) {
      function r() {
        if (!(this instanceof r)) return new r;
        this.size = 0, this.uid = 0, this.selectors = [], this.selectorObjects = {}, this.indexes = Object.create(this.indexes), this.activeIndexes = []
      }
      n.d(t, {
        h: () => E,
        on: () => k
      });
      var i, s = window.document.documentElement,
        a = s.matches || s.webkitMatchesSelector || s.mozMatchesSelector || s.oMatchesSelector || s.msMatchesSelector;
      r.prototype.matchesSelector = function(e, t) {
        return a.call(e, t)
      }, r.prototype.querySelectorAll = function(e, t) {
        return t.querySelectorAll(e)
      }, r.prototype.indexes = [];
      var o = /^#((?:[\w\u00c0-\uFFFF\-]|\\.)+)/g;
      r.prototype.indexes.push({
        name: "ID",
        selector: function(e) {
          var t;
          if (t = e.match(o)) return t[0].slice(1)
        },
        element: function(e) {
          if (e.id) return [e.id]
        }
      });
      var l = /^\.((?:[\w\u00c0-\uFFFF\-]|\\.)+)/g;
      r.prototype.indexes.push({
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
      var u = /^((?:[\w\u00c0-\uFFFF\-]|\\.)+)/g;
      r.prototype.indexes.push({
        name: "TAG",
        selector: function(e) {
          var t;
          if (t = e.match(u)) return t[0].toUpperCase()
        },
        element: function(e) {
          return [e.nodeName.toUpperCase()]
        }
      }), r.prototype.indexes.default = {
        name: "UNIVERSAL",
        selector: function() {
          return !0
        },
        element: function() {
          return [!0]
        }
      }, i = "function" == typeof window.Map ? window.Map : function() {
        function e() {
          this.map = {}
        }
        return e.prototype.get = function(e) {
          return this.map[e + " "]
        }, e.prototype.set = function(e, t) {
          this.map[e + " "] = t
        }, e
      }();
      var c = /((?:\((?:\([^()]+\)|[^()]+)+\)|\[(?:\[[^\[\]]*\]|['"][^'"]*['"]|[^\[\]'"]+)+\]|\\.|[^ >+~,(\[\\]+)+|[>+~])(\s*,\s*)?((?:.|\r|\n)*)/g;

      function h(e, t) {
        var n, r, i, s, a, o, l = (e = e.slice(0).concat(e.default)).length,
          u = t,
          h = [];
        do
          if (c.exec(""), (i = c.exec(u)) && (u = i[3], i[2] || !u)) {
            for (n = 0; n < l; n++)
              if (a = (o = e[n]).selector(i[1])) {
                for (r = h.length, s = !1; r--;)
                  if (h[r].index === o && h[r].key === a) {
                    s = !0;
                    break
                  } s || h.push({
                  index: o,
                  key: a
                });
                break
              }
          } while (i);
        return h
      }

      function p(e, t) {
        return e.id - t.id
      }
      r.prototype.logDefaultIndexUsed = function() {}, r.prototype.add = function(e, t) {
        var n, r, s, a, o, l, u, c, p = this.activeIndexes,
          f = this.selectors,
          d = this.selectorObjects;
        if ("string" == typeof e) {
          for (r = 0, d[(n = {
              id: this.uid++,
              selector: e,
              data: t
            }).id] = n, u = h(this.indexes, e); r < u.length; r++) a = (c = u[r]).key, (o = function(e, t) {
            var n, r, i;
            for (n = 0, r = e.length; n < r; n++)
              if (i = e[n], t.isPrototypeOf(i)) return i
          }(p, s = c.index)) || ((o = Object.create(s)).map = new i, p.push(o)), s === this.indexes.default && this.logDefaultIndexUsed(n), (l = o.map.get(a)) || (l = [], o.map.set(a, l)), l.push(n);
          this.size++, f.push(e)
        }
      }, r.prototype.remove = function(e, t) {
        if ("string" == typeof e) {
          var n, r, i, s, a, o, l, u, c = this.activeIndexes,
            p = this.selectors = [],
            f = this.selectorObjects,
            d = {},
            g = 1 == arguments.length;
          for (i = 0, n = h(this.indexes, e); i < n.length; i++)
            for (r = n[i], s = c.length; s--;)
              if (o = c[s], r.index.isPrototypeOf(o)) {
                if (l = o.map.get(r.key))
                  for (a = l.length; a--;)(u = l[a]).selector === e && (g || u.data === t) && (l.splice(a, 1), d[u.id] = !0);
                break
              } for (i in d) delete f[i], this.size--;
          for (i in f) p.push(f[i].selector)
        }
      }, r.prototype.queryAll = function(e) {
        if (!this.selectors.length) return [];
        var t, n, r, i, s, a, o, l, u = {},
          c = [],
          h = this.querySelectorAll(this.selectors.join(", "), e);
        for (t = 0, r = h.length; t < r; t++)
          for (n = 0, s = h[t], i = (a = this.matches(s)).length; n < i; n++) u[(l = a[n]).id] ? o = u[l.id] : (o = {
            id: l.id,
            selector: l.selector,
            data: l.data,
            elements: []
          }, u[l.id] = o, c.push(o)), o.elements.push(s);
        return c.sort(p)
      }, r.prototype.matches = function(e) {
        if (!e) return [];
        var t, n, r, i, s, a, o, l, u, c, h, f = this.activeIndexes,
          d = {},
          g = [];
        for (t = 0, i = f.length; t < i; t++)
          if (l = (o = f[t]).element(e)) {
            for (n = 0, s = l.length; n < s; n++)
              if (u = o.map.get(l[n]))
                for (r = 0, a = u.length; r < a; r++) !d[h = (c = u[r]).id] && this.matchesSelector(e, c.selector) && (d[h] = !0, g.push(c))
          } return g.sort(p)
      };
      var f = {},
        d = {},
        g = new WeakMap,
        m = new WeakMap,
        b = new WeakMap,
        v = Object.getOwnPropertyDescriptor(Event.prototype, "currentTarget");

      function y(e, t, n) {
        var r = e[t];
        return e[t] = function() {
          return n.apply(e, arguments), r.apply(e, arguments)
        }, e
      }

      function w() {
        g.set(this, !0)
      }

      function x() {
        g.set(this, !0), m.set(this, !0)
      }

      function S() {
        return b.get(this) || null
      }

      function O(e, t) {
        v && Object.defineProperty(e, "currentTarget", {
          configurable: !0,
          enumerable: !0,
          get: t || v.get
        })
      }

      function j(e) {
        if (function(e) {
            try {
              return e.eventPhase, !0
            } catch (e) {
              return !1
            }
          }(e)) {
          var t = (1 === e.eventPhase ? d : f)[e.type];
          if (t) {
            var n = function(e, t, n) {
              var r = [],
                i = t;
              do {
                if (1 !== i.nodeType) break;
                var s = e.matches(i);
                if (s.length) {
                  var a = {
                    node: i,
                    observers: s
                  };
                  n ? r.unshift(a) : r.push(a)
                }
              } while (i = i.parentElement);
              return r
            }(t, e.target, 1 === e.eventPhase);
            if (n.length) {
              y(e, "stopPropagation", w), y(e, "stopImmediatePropagation", x), O(e, S);
              for (var r = 0, i = n.length; r < i && !g.get(e); r++) {
                var s = n[r];
                b.set(e, s.node);
                for (var a = 0, o = s.observers.length; a < o && !m.get(e); a++) s.observers[a].data.call(s.node, e)
              }
              b.delete(e), O(e)
            }
          }
        }
      }

      function k(e, t, n) {
        var i = arguments.length > 3 && void 0 !== arguments[3] ? arguments[3] : {},
          s = !!i.capture,
          a = s ? d : f,
          o = a[e];
        o || (o = new r, a[e] = o, document.addEventListener(e, j, s)), o.add(t, n)
      }

      function E(e, t, n) {
        return e.dispatchEvent(new CustomEvent(t, {
          bubbles: !0,
          cancelable: !0,
          detail: n
        }))
      }
    },
    5225(e, t, n) {
      function r(...e) {
        return JSON.stringify(e, (e, t) => "object" == typeof t ? t : String(t))
      }

      function i(e, t = {}) {
        let {
          hash: n = r,
          cache: s = new Map
        } = t;
        return function(...t) {
          let r = n.apply(this, t);
          if (s.has(r)) return s.get(r);
          let i = e.apply(this, t);
          return i instanceof Promise && (i = i.catch(e => {
            throw s.delete(r), e
          })), s.set(r, i), i
        }
      }
      n.d(t, {
        A: () => i
      })
    },
    85498(e, t, n) {
      n.d(t, {
        TemplateInstance: () => v,
        xr: () => g
      });
      let r = new Map;

      function i(e) {
        if (r.has(e)) return r.get(e);
        let t = e.length,
          n = 0,
          i = 0,
          s = 0,
          a = [];
        for (let r = 0; r < t; r += 1) {
          let t = e[r],
            o = e[r + 1],
            l = e[r - 1];
          "{" === t && "{" === o && "\\" !== l ? (1 === (s += 1) && (i = r), r += 1) : "}" === t && "}" === o && "\\" !== l && s && 0 == (s -= 1) && (i > n && (a.push(Object.freeze({
            type: "string",
            start: n,
            end: i,
            value: e.slice(n, i)
          })), n = i), a.push(Object.freeze({
            type: "part",
            start: i,
            end: r + 2,
            value: e.slice(n + 2, r).trim()
          })), r += 1, n = r + 1)
        }
        return n < t && a.push(Object.freeze({
          type: "string",
          start: n,
          end: t,
          value: e.slice(n, t)
        })), r.set(e, Object.freeze(a)), r.get(e)
      }
      let s = new WeakMap,
        a = new WeakMap;
      class o {
        constructor(e, t) {
          this.expression = t, s.set(this, e), e.updateParent("")
        }
        get attributeName() {
          return s.get(this).attr.name
        }
        get attributeNamespace() {
          return s.get(this).attr.namespaceURI
        }
        get value() {
          return a.get(this)
        }
        set value(e) {
          a.set(this, e || ""), s.get(this).updateParent(e)
        }
        get element() {
          return s.get(this).element
        }
        get booleanValue() {
          return s.get(this).booleanValue
        }
        set booleanValue(e) {
          s.get(this).booleanValue = e
        }
      }
      class l {
        constructor(e, t) {
          this.element = e, this.attr = t, this.partList = []
        }
        get booleanValue() {
          return this.element.hasAttributeNS(this.attr.namespaceURI, this.attr.name)
        }
        set booleanValue(e) {
          if (1 !== this.partList.length) throw new DOMException("Operation not supported", "NotSupportedError");
          this.partList[0].value = e ? "" : null
        }
        append(e) {
          this.partList.push(e)
        }
        updateParent(e) {
          if (1 === this.partList.length && null === e) this.element.removeAttributeNS(this.attr.namespaceURI, this.attr.name);
          else {
            let e = this.partList.map(e => "string" == typeof e ? e : e.value).join("");
            this.element.setAttributeNS(this.attr.namespaceURI, this.attr.name, e)
          }
        }
      }
      let u = new WeakMap;
      class c {
        constructor(e, t) {
          this.expression = t, u.set(this, [e]), e.textContent = ""
        }
        get value() {
          return u.get(this).map(e => e.textContent).join("")
        }
        set value(e) {
          this.replace(e)
        }
        get previousSibling() {
          return u.get(this)[0].previousSibling
        }
        get nextSibling() {
          return u.get(this)[u.get(this).length - 1].nextSibling
        }
        replace(...e) {
          var t, n;
          let r = e.map(e => "string" == typeof e ? new Text(e) : e);
          r.length || r.push(new Text(""));
          let i = u.get(this)[0];
          for (let e of r) null == (t = i.parentNode) || t.insertBefore(e, i);
          for (let e of u.get(this)) null == (n = e.parentNode) || n.removeChild(e);
          u.set(this, r)
        }
      }
      class h extends c {
        constructor(e) {
          var t;
          super(e, null != (t = e.getAttribute("expression")) ? t : ""), this.template = e
        }
        get directive() {
          var e;
          return null != (e = this.template.getAttribute("directive")) ? e : ""
        }
      }

      function p(e) {
        return {
          processCallback(t, n, r) {
            var i;
            if ("object" == typeof r && r) {
              for (let t of n)
                if (t.expression in r) {
                  let n = null != (i = r[t.expression]) ? i : "";
                  e(t, n, r)
                }
            }
          }
        }
      }

      function f(e, t) {
        e.value = t instanceof Node ? t : String(t)
      }
      let d = p(f),
        g = p((e, t) => {
          "boolean" == typeof t && e instanceof o && "boolean" == typeof e.element[e.attributeName] && (e.booleanValue = t, 1) || f(e, t)
        }),
        m = new WeakMap,
        b = new WeakMap;
      class v extends(globalThis.DocumentFragment || EventTarget) {
        constructor(e, t, n = d) {
          var r, s;
          super(), Object.getPrototypeOf(this) !== v.prototype && Object.setPrototypeOf(this, v.prototype), this.appendChild(e.content.cloneNode(!0)), b.set(this, Array.from(function* e(t) {
            let n, r = t.ownerDocument.createTreeWalker(t, NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT, null);
            for (; n = r.nextNode();)
              if (n instanceof HTMLTemplateElement)
                if (n.hasAttribute("directive")) yield new h(n);
                else
                  for (let t of e(n.content)) yield t;
            else if (n instanceof Element && n.hasAttributes())
              for (let e = 0; e < n.attributes.length; e += 1) {
                let t = n.attributes.item(e);
                if (t && t.value.includes("{{")) {
                  let e = new l(n, t);
                  for (let n of i(t.value))
                    if ("string" === n.type) e.append(n.value);
                    else {
                      let t = new o(e, n.value);
                      e.append(t), yield t
                    }
                }
              } else if (n instanceof Text && n.textContent && n.textContent.includes("{{")) {
                let e = i(n.textContent);
                for (let t = 0; t < e.length; t += 1) {
                  let r = e[t];
                  r.end < n.textContent.length && n.splitText(r.end), "part" === r.type && (yield new c(n, r.value));
                  break
                }
              }
          }(this))), m.set(this, n), null == (s = (r = m.get(this)).createCallback) || s.call(r, this, b.get(this), t), m.get(this).processCallback(this, b.get(this), t)
        }
        update(e) {
          m.get(this).processCallback(this, b.get(this), e)
        }
      }
    },
    74043(e, t, n) {
      function r(e) {
        let t = "==".slice(0, (4 - e.length % 4) % 4),
          n = atob(e.replace(/-/g, "+").replace(/_/g, "/") + t),
          r = new ArrayBuffer(n.length),
          i = new Uint8Array(r);
        for (let e = 0; e < n.length; e++) i[e] = n.charCodeAt(e);
        return r
      }

      function i(e) {
        let t = new Uint8Array(e),
          n = "";
        for (let e of t) n += String.fromCharCode(e);
        return btoa(n).replace(/\+/g, "-").replace(/\//g, "_").replace(/=/g, "")
      }
      n.d(t, {
        $j: () => w,
        Jt: () => S,
        PG: () => v,
        d5: () => y,
        vt: () => x
      });
      var s = "copy",
        a = "convert";

      function o(e, t, n) {
        if (t === s) return n;
        if (t === a) return e(n);
        if (t instanceof Array) return n.map(n => o(e, t[0], n));
        if (t instanceof Object) {
          let r = {};
          for (let [i, s] of Object.entries(t)) {
            if (s.derive) {
              let e = s.derive(n);
              void 0 !== e && (n[i] = e)
            }
            if (!(i in n)) {
              if (s.required) throw Error(`Missing key: ${i}`);
              continue
            }
            if (null == n[i]) {
              r[i] = null;
              continue
            }
            r[i] = o(e, s.schema, n[i])
          }
          return r
        }
      }

      function l(e, t) {
        return {
          required: !0,
          schema: e,
          derive: t
        }
      }

      function u(e) {
        return {
          required: !0,
          schema: e
        }
      }

      function c(e) {
        return {
          required: !1,
          schema: e
        }
      }
      var h = {
          type: u(s),
          id: u(a),
          transports: c(s)
        },
        p = {
          appid: c(s),
          appidExclude: c(s),
          credProps: c(s)
        },
        f = {
          appid: c(s),
          appidExclude: c(s),
          credProps: c(s)
        },
        d = {
          publicKey: u({
            rp: u(s),
            user: u({
              id: u(a),
              name: u(s),
              displayName: u(s)
            }),
            challenge: u(a),
            pubKeyCredParams: u(s),
            timeout: c(s),
            excludeCredentials: c([h]),
            authenticatorSelection: c(s),
            attestation: c(s),
            extensions: c(p)
          }),
          signal: c(s)
        },
        g = {
          type: u(s),
          id: u(s),
          rawId: u(a),
          authenticatorAttachment: c(s),
          response: u({
            clientDataJSON: u(a),
            attestationObject: u(a),
            transports: l(s, e => {
              var t;
              return (null == (t = e.getTransports) ? void 0 : t.call(e)) || []
            })
          }),
          clientExtensionResults: l(f, e => e.getClientExtensionResults())
        },
        m = {
          mediation: c(s),
          publicKey: u({
            challenge: u(a),
            timeout: c(s),
            rpId: c(s),
            allowCredentials: c([h]),
            userVerification: c(s),
            extensions: c(p)
          }),
          signal: c(s)
        },
        b = {
          type: u(s),
          id: u(s),
          rawId: u(a),
          authenticatorAttachment: c(s),
          response: u({
            clientDataJSON: u(a),
            authenticatorData: u(a),
            signature: u(a),
            userHandle: u(a)
          }),
          clientExtensionResults: l(f, e => e.getClientExtensionResults())
        };

      function v(e) {
        return o(r, d, e)
      }

      function y(e) {
        return o(r, m, e)
      }

      function w() {
        return !!(navigator.credentials && navigator.credentials.create && navigator.credentials.get && window.PublicKeyCredential)
      }
      async function x(e) {
        let t = await navigator.credentials.create(e);
        return t.toJSON = () => o(i, g, t), t
      }
      async function S(e) {
        let t = await navigator.credentials.get(e);
        return t.toJSON = () => o(i, b, t), t
      }
    }
  }
]);
//# sourceMappingURL=93308-c21d6ff736807846-c8583e1d12b2f8e4.js.map