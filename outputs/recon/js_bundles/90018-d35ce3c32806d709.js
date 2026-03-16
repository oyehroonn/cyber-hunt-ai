performance.mark("js-parse-end:90018-d35ce3c32806d709.js");
(globalThis.webpackChunk_github_ui_github_ui = globalThis.webpackChunk_github_ui_github_ui || []).push([
  ["90018"], {
    244(e, t, n) {
      "use strict";
      var r, o, c = n(45871),
        a = n(70580),
        u = function() {
          return (u = Object.assign || function(e) {
            for (var t, n = 1, r = arguments.length; n < r; n++)
              for (var o in t = arguments[n]) Object.prototype.hasOwnProperty.call(t, o) && (e[o] = t[o]);
            return e
          }).apply(this, arguments)
        };
      "function" == typeof SuppressedError && SuppressedError;
      var i = ((r = {})[c.BLOCKS.PARAGRAPH] = function(e, t) {
          return "<p>".concat(t(e.content), "</p>")
        }, r[c.BLOCKS.HEADING_1] = function(e, t) {
          return "<h1>".concat(t(e.content), "</h1>")
        }, r[c.BLOCKS.HEADING_2] = function(e, t) {
          return "<h2>".concat(t(e.content), "</h2>")
        }, r[c.BLOCKS.HEADING_3] = function(e, t) {
          return "<h3>".concat(t(e.content), "</h3>")
        }, r[c.BLOCKS.HEADING_4] = function(e, t) {
          return "<h4>".concat(t(e.content), "</h4>")
        }, r[c.BLOCKS.HEADING_5] = function(e, t) {
          return "<h5>".concat(t(e.content), "</h5>")
        }, r[c.BLOCKS.HEADING_6] = function(e, t) {
          return "<h6>".concat(t(e.content), "</h6>")
        }, r[c.BLOCKS.EMBEDDED_ENTRY] = function(e, t) {
          return "<div>".concat(t(e.content), "</div>")
        }, r[c.BLOCKS.EMBEDDED_RESOURCE] = function(e, t) {
          return "<div>".concat(t(e.content), "</div>")
        }, r[c.BLOCKS.UL_LIST] = function(e, t) {
          return "<ul>".concat(t(e.content), "</ul>")
        }, r[c.BLOCKS.OL_LIST] = function(e, t) {
          return "<ol>".concat(t(e.content), "</ol>")
        }, r[c.BLOCKS.LIST_ITEM] = function(e, t) {
          return "<li>".concat(t(e.content), "</li>")
        }, r[c.BLOCKS.QUOTE] = function(e, t) {
          return "<blockquote>".concat(t(e.content), "</blockquote>")
        }, r[c.BLOCKS.HR] = function() {
          return "<hr/>"
        }, r[c.BLOCKS.TABLE] = function(e, t) {
          return "<table>".concat(t(e.content), "</table>")
        }, r[c.BLOCKS.TABLE_ROW] = function(e, t) {
          return "<tr>".concat(t(e.content), "</tr>")
        }, r[c.BLOCKS.TABLE_HEADER_CELL] = function(e, t) {
          return "<th>".concat(t(e.content), "</th>")
        }, r[c.BLOCKS.TABLE_CELL] = function(e, t) {
          return "<td>".concat(t(e.content), "</td>")
        }, r[c.INLINES.ASSET_HYPERLINK] = function(e) {
          return l(c.INLINES.ASSET_HYPERLINK, e)
        }, r[c.INLINES.ENTRY_HYPERLINK] = function(e) {
          return l(c.INLINES.ENTRY_HYPERLINK, e)
        }, r[c.INLINES.RESOURCE_HYPERLINK] = function(e) {
          return f(c.INLINES.RESOURCE_HYPERLINK, e)
        }, r[c.INLINES.EMBEDDED_ENTRY] = function(e) {
          return l(c.INLINES.EMBEDDED_ENTRY, e)
        }, r[c.INLINES.EMBEDDED_RESOURCE] = function(e) {
          return f(c.INLINES.EMBEDDED_RESOURCE, e)
        }, r[c.INLINES.HYPERLINK] = function(e, t) {
          var n = "string" == typeof e.data.uri ? e.data.uri : "";
          return "<a href=".concat('"'.concat(n.replace(/"/g, "&quot;"), '"'), ">").concat(t(e.content), "</a>")
        }, r),
        s = ((o = {})[c.MARKS.BOLD] = function(e) {
          return "<b>".concat(e, "</b>")
        }, o[c.MARKS.ITALIC] = function(e) {
          return "<i>".concat(e, "</i>")
        }, o[c.MARKS.UNDERLINE] = function(e) {
          return "<u>".concat(e, "</u>")
        }, o[c.MARKS.CODE] = function(e) {
          return "<code>".concat(e, "</code>")
        }, o[c.MARKS.SUPERSCRIPT] = function(e) {
          return "<sup>".concat(e, "</sup>")
        }, o[c.MARKS.SUBSCRIPT] = function(e) {
          return "<sub>".concat(e, "</sub>")
        }, o[c.MARKS.STRIKETHROUGH] = function(e) {
          return "<s>".concat(e, "</s>")
        }, o),
        l = function(e, t) {
          return "<span>type: ".concat(a(e), " id: ").concat(a(t.data.target.sys.id), "</span>")
        },
        f = function(e, t) {
          return "<span>type: ".concat(a(e), " urn: ").concat(a(t.data.target.sys.urn), "</span>")
        };
      t.documentToHtmlString = function(e, t) {
        return (void 0 === t && (t = {}), e && e.content) ? function e(t, n) {
          var r = n.renderNode,
            o = n.renderMark,
            u = n.preserveWhitespace;
          return t.map(function(t) {
            return function(t, n) {
              var r = n.renderNode,
                o = n.renderMark,
                u = n.preserveWhitespace;
              if (c.helpers.isText(t)) {
                var i = a(t.value);
                return (u && (i = i.replace(/\n/g, "<br/>").replace(/ {2,}/g, function(e) {
                  return "&nbsp;".repeat(e.length)
                })), t.marks.length > 0) ? t.marks.reduce(function(e, t) {
                  return o[t.type] ? o[t.type](e) : e
                }, i) : i
              }
              return t.nodeType && r[t.nodeType] ? r[t.nodeType](t, function(t) {
                return e(t, {
                  renderMark: o,
                  renderNode: r,
                  preserveWhitespace: u
                })
              }) : ""
            }(t, {
              renderNode: r,
              renderMark: o,
              preserveWhitespace: u
            })
          }).join("")
        }(e.content, {
          renderNode: u(u({}, i), t.renderNode),
          renderMark: u(u({}, s), t.renderMark),
          preserveWhitespace: t.preserveWhitespace
        }) : ""
      }
    },
    4240(e, t, n) {
      "use strict";
      var r, o, c = n(96540),
        a = n(45871),
        u = function() {
          return (u = Object.assign || function(e) {
            for (var t, n = 1, r = arguments.length; n < r; n++)
              for (var o in t = arguments[n]) Object.prototype.hasOwnProperty.call(t, o) && (e[o] = t[o]);
            return e
          }).apply(this, arguments)
        };
      "function" == typeof SuppressedError && SuppressedError;
      var i = ((r = {})[a.BLOCKS.DOCUMENT] = function(e, t) {
          return t
        }, r[a.BLOCKS.PARAGRAPH] = function(e, t) {
          return c.createElement("p", null, t)
        }, r[a.BLOCKS.HEADING_1] = function(e, t) {
          return c.createElement("h1", null, t)
        }, r[a.BLOCKS.HEADING_2] = function(e, t) {
          return c.createElement("h2", null, t)
        }, r[a.BLOCKS.HEADING_3] = function(e, t) {
          return c.createElement("h3", null, t)
        }, r[a.BLOCKS.HEADING_4] = function(e, t) {
          return c.createElement("h4", null, t)
        }, r[a.BLOCKS.HEADING_5] = function(e, t) {
          return c.createElement("h5", null, t)
        }, r[a.BLOCKS.HEADING_6] = function(e, t) {
          return c.createElement("h6", null, t)
        }, r[a.BLOCKS.EMBEDDED_ENTRY] = function(e, t) {
          return c.createElement("div", null, t)
        }, r[a.BLOCKS.EMBEDDED_RESOURCE] = function(e, t) {
          return c.createElement("div", null, t)
        }, r[a.BLOCKS.UL_LIST] = function(e, t) {
          return c.createElement("ul", null, t)
        }, r[a.BLOCKS.OL_LIST] = function(e, t) {
          return c.createElement("ol", null, t)
        }, r[a.BLOCKS.LIST_ITEM] = function(e, t) {
          return c.createElement("li", null, t)
        }, r[a.BLOCKS.QUOTE] = function(e, t) {
          return c.createElement("blockquote", null, t)
        }, r[a.BLOCKS.HR] = function() {
          return c.createElement("hr", null)
        }, r[a.BLOCKS.TABLE] = function(e, t) {
          return c.createElement("table", null, c.createElement("tbody", null, t))
        }, r[a.BLOCKS.TABLE_ROW] = function(e, t) {
          return c.createElement("tr", null, t)
        }, r[a.BLOCKS.TABLE_HEADER_CELL] = function(e, t) {
          return c.createElement("th", null, t)
        }, r[a.BLOCKS.TABLE_CELL] = function(e, t) {
          return c.createElement("td", null, t)
        }, r[a.INLINES.ASSET_HYPERLINK] = function(e) {
          return l(a.INLINES.ASSET_HYPERLINK, e)
        }, r[a.INLINES.ENTRY_HYPERLINK] = function(e) {
          return l(a.INLINES.ENTRY_HYPERLINK, e)
        }, r[a.INLINES.RESOURCE_HYPERLINK] = function(e) {
          return f(a.INLINES.RESOURCE_HYPERLINK, e)
        }, r[a.INLINES.EMBEDDED_ENTRY] = function(e) {
          return l(a.INLINES.EMBEDDED_ENTRY, e)
        }, r[a.INLINES.EMBEDDED_RESOURCE] = function(e, t) {
          return f(a.INLINES.EMBEDDED_RESOURCE, e)
        }, r[a.INLINES.HYPERLINK] = function(e, t) {
          return c.createElement("a", {
            href: e.data.uri
          }, t)
        }, r),
        s = ((o = {})[a.MARKS.BOLD] = function(e) {
          return c.createElement("b", null, e)
        }, o[a.MARKS.ITALIC] = function(e) {
          return c.createElement("i", null, e)
        }, o[a.MARKS.UNDERLINE] = function(e) {
          return c.createElement("u", null, e)
        }, o[a.MARKS.CODE] = function(e) {
          return c.createElement("code", null, e)
        }, o[a.MARKS.SUPERSCRIPT] = function(e) {
          return c.createElement("sup", null, e)
        }, o[a.MARKS.SUBSCRIPT] = function(e) {
          return c.createElement("sub", null, e)
        }, o[a.MARKS.STRIKETHROUGH] = function(e) {
          return c.createElement("s", null, e)
        }, o);

      function l(e, t) {
        return c.createElement("span", {
          key: t.data.target.sys.id
        }, "type: ", t.nodeType, " id: ", t.data.target.sys.id)
      }

      function f(e, t) {
        return c.createElement("span", {
          key: t.data.target.sys.urn
        }, "type: ", t.nodeType, " urn: ", t.data.target.sys.urn)
      }
      t.documentToReactComponents = function(e, t) {
        return (void 0 === t && (t = {}), e) ? function e(t, n) {
          var r = n.renderNode,
            o = n.renderMark,
            u = n.renderText,
            i = n.preserveWhitespace;
          if (a.helpers.isText(t)) {
            var s = u ? u(t.value) : t.value;
            if (i && !u) {
              var l = (s = s.replace(/ {2,}/g, function(e) {
                  return "\xa0".repeat(e.length)
                })).split("\n"),
                f = [];
              l.forEach(function(e, t) {
                f.push(e), t !== l.length - 1 && f.push(c.createElement("br", null))
              }), s = f
            }
            return t.marks.reduce(function(e, t) {
              return o[t.type] ? o[t.type](e) : e
            }, s)
          }
          var d, p = (d = t.content, d.map(function(t, r) {
            var o;
            return o = e(t, n), c.isValidElement(o) && null === o.key ? c.cloneElement(o, {
              key: r
            }) : o
          }));
          return t.nodeType && r[t.nodeType] ? r[t.nodeType](t, p) : c.createElement(c.Fragment, null, p)
        }(e, {
          renderNode: u(u({}, i), t.renderNode),
          renderMark: u(u({}, s), t.renderMark),
          renderText: t.renderText,
          preserveWhitespace: t.preserveWhitespace
        }) : null
      }
    },
    73893(e, t, n) {
      "use strict";
      n.d(t, {
        A: () => E
      });
      var r = n(6044),
        o = n.n(r),
        c = "function" == typeof Symbol && "symbol" == typeof Symbol.iterator ? function(e) {
          return typeof e
        } : function(e) {
          return e && "function" == typeof Symbol && e.constructor === Symbol && e !== Symbol.prototype ? "symbol" : typeof e
        },
        a = function(e, t) {
          if (Array.isArray(e)) return e;
          if (Symbol.iterator in Object(e)) return function(e, t) {
            var n = [],
              r = !0,
              o = !1,
              c = void 0;
            try {
              for (var a, u = e[Symbol.iterator](); !(r = (a = u.next()).done) && (n.push(a.value), !t || n.length !== t); r = !0);
            } catch (e) {
              o = !0, c = e
            } finally {
              try {
                !r && u.return && u.return()
              } finally {
                if (o) throw c
              }
            }
            return n
          }(e, t);
          throw TypeError("Invalid attempt to destructure non-iterable instance")
        };

      function u(e) {
        if (!Array.isArray(e)) return Array.from(e);
        for (var t = 0, n = Array(e.length); t < e.length; t++) n[t] = e[t];
        return n
      }
      var i = {},
        s = function(e, t) {
          var n = t.entryId,
            r = t.linkType,
            o = t.spaceId;
          return o ? e.get(o + "!" + r + "!" + n) : e.get(r + "!" + n)
        },
        l = function(e, t) {
          var n = t.sys,
            r = n.type,
            o = n.linkType;
          if ("ResourceLink" === r) {
            var c = t.sys.urn,
              u = /.*:spaces\/([A-Za-z0-9]*)\/entries\/([A-Za-z0-9]*)/;
            if (!u.test(c)) return i;
            var l = a(c.match(u), 3),
              f = (l[0], l[1]),
              d = l[2];
            return s(e, {
              linkType: o.split(":")[1],
              entryId: d,
              spaceId: f
            }) || i
          }
          return s(e, {
            linkType: o,
            entryId: t.sys.id
          }) || i
        },
        f = function(e) {
          if (Array.isArray(e)) return e.filter(function(e) {
            return e !== i
          });
          for (var t in e) e[t] === i && delete e[t];
          return e
        },
        d = function e(t, n, r, o) {
          if (n(t)) return r(t);
          if (t && (void 0 === t ? "undefined" : c(t)) === "object") {
            for (var a in t) t.hasOwnProperty(a) && (t[a] = e(t[a], n, r, o));
            o && (t = f(t))
          }
          return t
        },
        p = function(e, t, n) {
          var r = l(e, t);
          return r === i ? n ? r : t : r
        };
      let E = function(e, t) {
        if (t = t || {}, !e.items) return [];
        var n = o()(e),
          r = Object.keys(n.includes || {}).reduce(function(t, n) {
            return [].concat(u(t), u(e.includes[n]))
          }, []),
          c = [].concat(u(n.items), u(r)).filter(function(e) {
            return !!e.sys
          }),
          a = new Map(c.reduce(function(e, t) {
            var n, r = ((n = t.sys).space ? [n.type + "!" + n.id, n.space.sys.id + "!" + n.type + "!" + n.id] : [n.type + "!" + n.id]).map(function(e) {
              return [e, t]
            });
            return e.push.apply(e, u(r)), e
          }, []));
        return c.forEach(function(e) {
          var n, r = Array.isArray(n = t.itemEntryPoints) ? Object.keys(e).filter(function(e) {
            return -1 !== n.indexOf(e)
          }).reduce(function(t, n) {
            return t[n] = e[n], t
          }, {}) : e;
          Object.assign(e, d(r, function(e) {
            return e && e.sys && "Link" === e.sys.type || e && e.sys && "ResourceLink" === e.sys.type
          }, function(e) {
            return p(a, e, t.removeUnresolved)
          }, t.removeUnresolved))
        }), n.items
      }
    },
    70580(e) {
      "use strict";
      var t = /["'&<>]/;
      e.exports = function(e) {
        var n, r = "" + e,
          o = t.exec(r);
        if (!o) return r;
        var c = "",
          a = 0,
          u = 0;
        for (a = o.index; a < r.length; a++) {
          switch (r.charCodeAt(a)) {
            case 34:
              n = "&quot;";
              break;
            case 38:
              n = "&amp;";
              break;
            case 39:
              n = "&#39;";
              break;
            case 60:
              n = "&lt;";
              break;
            case 62:
              n = "&gt;";
              break;
            default:
              continue
          }
          u !== a && (c += r.substring(u, a)), u = a + 1, c += n
        }
        return u !== a ? c + r.substring(u, a) : c
      }
    },
    6044(e, t, n) {
      e.exports = function() {
        "use strict";
        var e = Function.prototype.toString,
          t = Object.create,
          r = Object.defineProperty,
          o = Object.getOwnPropertyDescriptor,
          c = Object.getOwnPropertyNames,
          a = Object.getOwnPropertySymbols,
          u = Object.getPrototypeOf,
          i = Object.prototype,
          s = i.hasOwnProperty,
          l = i.propertyIsEnumerable,
          f = "function" == typeof a,
          d = "function" == typeof WeakMap,
          p = function() {
            if (d) return function() {
              return new WeakMap
            };
            var e = function() {
              function e() {
                this._keys = [], this._values = []
              }
              return e.prototype.has = function(e) {
                return !!~this._keys.indexOf(e)
              }, e.prototype.get = function(e) {
                return this._values[this._keys.indexOf(e)]
              }, e.prototype.set = function(e, t) {
                this._keys.push(e), this._values.push(t)
              }, e
            }();
            return function() {
              return new e
            }
          }(),
          E = function(n, r) {
            var o = n.__proto__ || u(n);
            if (!o) return t(null);
            var c = o.constructor;
            if (c === r.Object) return o === r.Object.prototype ? {} : t(o);
            if (~e.call(c).indexOf("[native code]")) try {
              return new c
            } catch (e) {}
            return t(o)
          },
          y = function(e, t, n, r) {
            var o = E(e, t);
            for (var c in r.set(e, o), e) s.call(e, c) && (o[c] = n(e[c], r));
            if (f)
              for (var u = a(e), i = 0, d = u.length, p = void 0; i < d; ++i) p = u[i], l.call(e, p) && (o[p] = n(e[p], r));
            return o
          },
          h = function(e, t, n, u) {
            var i = E(e, t);
            u.set(e, i);
            for (var s = f ? c(e).concat(a(e)) : c(e), l = 0, d = s.length, p = void 0, y = void 0; l < d; ++l)
              if ("callee" !== (p = s[l]) && "caller" !== p)
                if (y = o(e, p)) {
                  y.get || y.set || (y.value = n(e[p], u));
                  try {
                    r(i, p, y)
                  } catch (e) {
                    i[p] = y.value
                  }
                } else i[p] = n(e[p], u);
            return i
          },
          b = function(e) {
            var t = "";
            return e.global && (t += "g"), e.ignoreCase && (t += "i"), e.multiline && (t += "m"), e.unicode && (t += "u"), e.sticky && (t += "y"), t
          },
          S = Array.isArray,
          g = Object.getPrototypeOf,
          m = function() {
            return "u" > typeof globalThis ? globalThis : "u" > typeof self ? self : "u" > typeof window ? window : void 0 !== n.g ? n.g : (console && console.error && console.error('Unable to locate global object, returning "this".'), this)
          }();

        function L(e, t) {
          var n = !!(t && t.isStrict),
            r = t && t.realm || m,
            o = n ? h : y,
            c = function(e, t) {
              if (!e || "object" != typeof e) return e;
              if (t.has(e)) return t.get(e);
              var a, u = e.__proto__ || g(e),
                i = u && u.constructor;
              if (!i || i === r.Object) return o(e, r, c, t);
              if (S(e)) {
                if (n) return h(e, r, c, t);
                a = new i, t.set(e, a);
                for (var s = 0, l = e.length; s < l; ++s) a[s] = c(e[s], t);
                return a
              }
              if (e instanceof r.Date) return new i(e.getTime());
              if (e instanceof r.RegExp) return (a = new i(e.source, e.flags || b(e))).lastIndex = e.lastIndex, a;
              if (r.Map && e instanceof r.Map) return a = new i, t.set(e, a), e.forEach(function(e, n) {
                a.set(n, c(e, t))
              }), a;
              if (r.Set && e instanceof r.Set) return a = new i, t.set(e, a), e.forEach(function(e) {
                a.add(c(e, t))
              }), a;
              if (r.Blob && e instanceof r.Blob) return e.slice(0, e.size, e.type);
              if (r.Buffer && r.Buffer.isBuffer(e)) return a = r.Buffer.allocUnsafe ? r.Buffer.allocUnsafe(e.length) : new i(e.length), t.set(e, a), e.copy(a), a;
              if (r.ArrayBuffer) {
                if (r.ArrayBuffer.isView(e)) return a = new i(e.buffer.slice(0)), t.set(e, a), a;
                if (e instanceof r.ArrayBuffer) return a = e.slice(0), t.set(e, a), a
              }
              return "function" == typeof e.then || e instanceof Error || r.WeakMap && e instanceof r.WeakMap || r.WeakSet && e instanceof r.WeakSet ? e : o(e, r, c, t)
            };
          return c(e, p())
        }
        return L.default = L, L.strict = function(e, t) {
          return L(e, {
            isStrict: !0,
            realm: t ? t.realm : void 0
          })
        }, L
      }()
    },
    94571(e, t, n) {
      "use strict";
      let r;
      n.d(t, {
        Se: () => I,
        FB: () => f,
        p_: () => B,
        CF: () => y,
        aC: () => _,
        zV: () => w
      });
      let o = new WeakSet,
        c = new WeakMap;

      function a(e = document) {
        if (c.has(e)) return c.get(e);
        let t = !1,
          n = new MutationObserver(e => {
            for (let t of e)
              if ("attributes" === t.type && t.target instanceof Element) l(t.target);
              else if ("childList" === t.type && t.addedNodes.length)
              for (let e of t.addedNodes) e instanceof Element && u(e)
          });
        n.observe(e, {
          childList: !0,
          subtree: !0,
          attributeFilter: ["data-action"]
        });
        let r = {
          get closed() {
            return t
          },
          unsubscribe() {
            t = !0, c.delete(e), n.disconnect()
          }
        };
        return c.set(e, r), r
      }

      function u(e) {
        for (let t of e.querySelectorAll("[data-action]")) l(t);
        e instanceof Element && e.hasAttribute("data-action") && l(e)
      }

      function i(e) {
        let t = e.currentTarget;
        for (let n of s(t))
          if (e.type === n.type) {
            let r = t.closest(n.tag);
            o.has(r) && "function" == typeof r[n.method] && r[n.method](e);
            let c = t.getRootNode();
            if (c instanceof ShadowRoot && o.has(c.host) && c.host.matches(n.tag)) {
              let t = c.host;
              "function" == typeof t[n.method] && t[n.method](e)
            }
          }
      }

      function* s(e) {
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

      function l(e) {
        for (let t of s(e)) e.addEventListener(t.type, i)
      }

      function f(e, t) {
        let n = e.tagName.toLowerCase();
        if (e.shadowRoot) {
          for (let r of e.shadowRoot.querySelectorAll(`[data-target~="${n}.${t}"]`))
            if (!r.closest(n)) return r
        }
        for (let r of e.querySelectorAll(`[data-target~="${n}.${t}"]`))
          if (r.closest(n) === e) return r
      }
      let d = e => String("symbol" == typeof e ? e.description : e).replace(/([A-Z]($|[a-z]))/g, "-$1").replace(/--/g, "-").replace(/^-|-$/, "").toLowerCase(),
        p = (e, t = "property") => {
          let n = d(e);
          if (!n.includes("-")) throw new DOMException(`${t}: ${String(e)} is not a valid ${t} name`, "SyntaxError");
          return n
        },
        E = "attr";

      function y(e, t) {
        C(e, E).add(t)
      }
      let h = new WeakSet;

      function b(e, t) {
        if (h.has(e)) return;
        h.add(e);
        let n = Object.getPrototypeOf(e),
          r = n?.constructor?.attrPrefix ?? "data-";
        for (let o of (t || (t = C(n, E)), t)) {
          let t = e[o],
            n = p(`${r}${o}`),
            c = {
              configurable: !0,
              get() {
                return this.getAttribute(n) || ""
              },
              set(e) {
                this.setAttribute(n, e || "")
              }
            };
          "number" == typeof t ? c = {
            configurable: !0,
            get() {
              return Number(this.getAttribute(n) || 0)
            },
            set(e) {
              this.setAttribute(n, e)
            }
          } : "boolean" == typeof t && (c = {
            configurable: !0,
            get() {
              return this.hasAttribute(n)
            },
            set(e) {
              this.toggleAttribute(n, e)
            }
          }), Object.defineProperty(e, o, c), o in e && !e.hasAttribute(n) && c.set.call(e, t)
        }
      }
      let S = new Map,
        g = new Promise(e => {
          "loading" !== document.readyState ? e() : document.addEventListener("readystatechange", () => e(), {
            once: !0
          })
        }),
        m = new Promise(e => {
          let t = new AbortController;
          t.signal.addEventListener("abort", () => e());
          let n = {
              once: !0,
              passive: !0,
              signal: t.signal
            },
            r = () => t.abort();
          document.addEventListener("mousedown", r, n), document.addEventListener("touchstart", r, n), document.addEventListener("keydown", r, n), document.addEventListener("pointerdown", r, n)
        }),
        L = {
          ready: () => g,
          firstInteraction: () => m,
          visible: e => new Promise(t => {
            let n = new IntersectionObserver(e => {
              for (let r of e)
                if (r.isIntersecting) {
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
        v = new WeakMap;

      function O(e) {
        cancelAnimationFrame(v.get(e) || 0), v.set(e, requestAnimationFrame(() => {
          for (let t of S.keys()) {
            let n = e instanceof Element && e.matches(t) ? e : e.querySelector(t);
            if (customElements.get(t) || n) {
              let r = n?.getAttribute("data-load-on") || "ready",
                o = r in L ? L[r] : L.ready;
              for (let e of S.get(t) || []) o(t).then(e);
              S.delete(t), v.delete(e)
            }
          }
        }))
      }

      function I(e, t) {
        for (let [n, r] of("string" == typeof e && t && (e = {
            [e]: t
          }), Object.entries(e))) S.has(n) || S.set(n, new Set), S.get(n).add(r);
        N(document)
      }

      function N(e) {
        r || (r = new MutationObserver(e => {
          if (S.size)
            for (let t of e)
              for (let e of t.addedNodes) e instanceof Element && O(e)
        })), O(e), r.observe(e, {
          subtree: !0,
          childList: !0
        })
      }
      let A = Symbol.for("catalyst");
      class R {
        constructor(e, t) {
          const n = this,
            r = e.prototype.connectedCallback;
          e.prototype.connectedCallback = function() {
            n.connectedCallback(this, r)
          };
          const o = e.prototype.disconnectedCallback;
          e.prototype.disconnectedCallback = function() {
            n.disconnectedCallback(this, o)
          };
          const c = e.prototype.attributeChangedCallback;
          e.prototype.attributeChangedCallback = function(e, t, r) {
            n.attributeChangedCallback(this, e, t, r, c)
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
                r = e => p(`${n}${e}`);
              Object.defineProperty(e, "observedAttributes", {
                configurable: !0,
                get: () => [...C(e.prototype, E)].map(r).concat(t),
                set(e) {
                  t = e
                }
              })
            }(e),
            function(e, t) {
              let n = t || d(e.name).replace(/-element$/, "");
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
          var n, r;
          for (let t of (e.toggleAttribute("data-catalyst", !0), customElements.upgrade(e), e.querySelectorAll("template[data-shadowroot]"))) t.parentElement === e && e.attachShadow({
            mode: "closed" === t.getAttribute("data-shadowroot") ? "closed" : "open"
          }).append(t.content.cloneNode(!0));
          (b(e), o.add(e), e.shadowRoot && (u(r = e.shadowRoot), a(r)), u(e), a(e.ownerDocument), t?.call(e), e.shadowRoot) && (u(n = e.shadowRoot), a(n), N(e.shadowRoot))
        }
        disconnectedCallback(e, t) {
          t?.call(e)
        }
        attributeChangedCallback(e, t, n, r, o) {
          b(e), "data-catalyst" !== t && o && o.call(e, t, n, r)
        }
      }

      function C(e, t) {
        if (!Object.prototype.hasOwnProperty.call(e, A)) {
          let t = e[A],
            n = e[A] = new Map;
          if (t)
            for (let [e, r] of t) n.set(e, new Set(r))
        }
        let n = e[A];
        return n.has(t) || n.set(t, new Set), n.get(t)
      }

      function _(e, t) {
        C(e, "target").add(t), Object.defineProperty(e, t, {
          configurable: !0,
          get() {
            return f(this, t)
          }
        })
      }

      function w(e, t) {
        C(e, "targets").add(t), Object.defineProperty(e, t, {
          configurable: !0,
          get() {
            let e = this.tagName.toLowerCase(),
              n = [];
            if (this.shadowRoot)
              for (let r of this.shadowRoot.querySelectorAll(`[data-targets~="${e}.${t}"]`)) r.closest(e) || n.push(r);
            for (let r of this.querySelectorAll(`[data-targets~="${e}.${t}"]`)) r.closest(e) === this && n.push(r);
            return n
          }
        })
      }

      function B(e) {
        if ("string" == typeof e) return t => {
          new R(t, e)
        };
        new R(e)
      }
    },
    31993(e, t, n) {
      "use strict";

      function r(e) {
        return e
      }
      n.d(t, {
        j: () => r
      })
    }
  }
]);
//# sourceMappingURL=90018-d35ce3c32806d709-9b5b07c0f10a2082.js.map