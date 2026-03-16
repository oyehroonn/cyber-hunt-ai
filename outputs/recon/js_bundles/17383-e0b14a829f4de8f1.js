performance.mark("js-parse-end:17383-e0b14a829f4de8f1.js");
(globalThis.webpackChunk_github_ui_github_ui = globalThis.webpackChunk_github_ui_github_ui || []).push([
  ["17383"], {
    16869(e, t, r) {
      "use strict";
      r.d(t, {
        A: () => o
      });
      var i, n, s = /^((children|dangerouslySetInnerHTML|key|ref|autoFocus|defaultValue|defaultChecked|innerHTML|suppressContentEditableWarning|suppressHydrationWarning|valueLink|abbr|accept|acceptCharset|accessKey|action|allow|allowUserMedia|allowPaymentRequest|allowFullScreen|allowTransparency|alt|async|autoComplete|autoPlay|capture|cellPadding|cellSpacing|challenge|charSet|checked|cite|classID|className|cols|colSpan|content|contentEditable|contextMenu|controls|controlsList|coords|crossOrigin|data|dateTime|decoding|default|defer|dir|disabled|disablePictureInPicture|download|draggable|encType|enterKeyHint|form|formAction|formEncType|formMethod|formNoValidate|formTarget|frameBorder|headers|height|hidden|high|href|hrefLang|htmlFor|httpEquiv|id|inputMode|integrity|is|keyParams|keyType|kind|label|lang|list|loading|loop|low|marginHeight|marginWidth|max|maxLength|media|mediaGroup|method|min|minLength|multiple|muted|name|nonce|noValidate|open|optimum|pattern|placeholder|playsInline|poster|preload|profile|radioGroup|readOnly|referrerPolicy|rel|required|reversed|role|rows|rowSpan|sandbox|scope|scoped|scrolling|seamless|selected|shape|size|sizes|slot|span|spellCheck|src|srcDoc|srcLang|srcSet|start|step|style|summary|tabIndex|target|title|translate|type|useMap|value|width|wmode|wrap|about|datatype|inlist|prefix|property|resource|typeof|vocab|autoCapitalize|autoCorrect|autoSave|color|incremental|fallback|inert|itemProp|itemScope|itemType|itemID|itemRef|on|option|results|security|unselectable|accentHeight|accumulate|additive|alignmentBaseline|allowReorder|alphabetic|amplitude|arabicForm|ascent|attributeName|attributeType|autoReverse|azimuth|baseFrequency|baselineShift|baseProfile|bbox|begin|bias|by|calcMode|capHeight|clip|clipPathUnits|clipPath|clipRule|colorInterpolation|colorInterpolationFilters|colorProfile|colorRendering|contentScriptType|contentStyleType|cursor|cx|cy|d|decelerate|descent|diffuseConstant|direction|display|divisor|dominantBaseline|dur|dx|dy|edgeMode|elevation|enableBackground|end|exponent|externalResourcesRequired|fill|fillOpacity|fillRule|filter|filterRes|filterUnits|floodColor|floodOpacity|focusable|fontFamily|fontSize|fontSizeAdjust|fontStretch|fontStyle|fontVariant|fontWeight|format|from|fr|fx|fy|g1|g2|glyphName|glyphOrientationHorizontal|glyphOrientationVertical|glyphRef|gradientTransform|gradientUnits|hanging|horizAdvX|horizOriginX|ideographic|imageRendering|in|in2|intercept|k|k1|k2|k3|k4|kernelMatrix|kernelUnitLength|kerning|keyPoints|keySplines|keyTimes|lengthAdjust|letterSpacing|lightingColor|limitingConeAngle|local|markerEnd|markerMid|markerStart|markerHeight|markerUnits|markerWidth|mask|maskContentUnits|maskUnits|mathematical|mode|numOctaves|offset|opacity|operator|order|orient|orientation|origin|overflow|overlinePosition|overlineThickness|panose1|paintOrder|pathLength|patternContentUnits|patternTransform|patternUnits|pointerEvents|points|pointsAtX|pointsAtY|pointsAtZ|preserveAlpha|preserveAspectRatio|primitiveUnits|r|radius|refX|refY|renderingIntent|repeatCount|repeatDur|requiredExtensions|requiredFeatures|restart|result|rotate|rx|ry|scale|seed|shapeRendering|slope|spacing|specularConstant|specularExponent|speed|spreadMethod|startOffset|stdDeviation|stemh|stemv|stitchTiles|stopColor|stopOpacity|strikethroughPosition|strikethroughThickness|string|stroke|strokeDasharray|strokeDashoffset|strokeLinecap|strokeLinejoin|strokeMiterlimit|strokeOpacity|strokeWidth|surfaceScale|systemLanguage|tableValues|targetX|targetY|textAnchor|textDecoration|textRendering|textLength|to|transform|u1|u2|underlinePosition|underlineThickness|unicode|unicodeBidi|unicodeRange|unitsPerEm|vAlphabetic|vHanging|vIdeographic|vMathematical|values|vectorEffect|version|vertAdvY|vertOriginX|vertOriginY|viewBox|viewTarget|visibility|widths|wordSpacing|writingMode|x|xHeight|x1|x2|xChannelSelector|xlinkActuate|xlinkArcrole|xlinkHref|xlinkRole|xlinkShow|xlinkTitle|xlinkType|xmlBase|xmlns|xmlnsXlink|xmlLang|xmlSpace|y|y1|y2|yChannelSelector|z|zoomAndPan|for|class|autofocus)|(([Dd][Aa][Tt][Aa]|[Aa][Rr][Ii][Aa]|x)-.*))$/;
      let o = (i = function(e) {
        return s.test(e) || 111 === e.charCodeAt(0) && 110 === e.charCodeAt(1) && 91 > e.charCodeAt(2)
      }, n = Object.create(null), function(e) {
        return void 0 === n[e] && (n[e] = i(e)), n[e]
      })
    },
    8887(e, t, r) {
      "use strict";
      r.d(t, {
        A: () => i
      });
      let i = function(e) {
        function t(e, t, i) {
          var n = t.trim().split(p);
          t = n;
          var s = n.length,
            o = e.length;
          switch (o) {
            case 0:
            case 1:
              var a = 0;
              for (e = 0 === o ? "" : e[0] + " "; a < s; ++a) t[a] = r(e, t[a], i).trim();
              break;
            default:
              var l = a = 0;
              for (t = []; a < s; ++a)
                for (var c = 0; c < o; ++c) t[l++] = r(e[c] + " ", n[a], i).trim()
          }
          return t
        }

        function r(e, t, r) {
          var i = t.charCodeAt(0);
          switch (33 > i && (i = (t = t.trim()).charCodeAt(0)), i) {
            case 38:
              return t.replace(m, "$1" + e.trim());
            case 58:
              return e.trim() + t.replace(m, "$1" + e.trim());
            default:
              if (0 < +r && 0 < t.indexOf("\f")) return t.replace(m, (58 === e.charCodeAt(0) ? "" : "$1") + e.trim())
          }
          return e + t
        }

        function i(e, t, r, s) {
          var o = e + ";",
            a = 2 * t + 3 * r + 4 * s;
          if (944 === a) {
            e = o.indexOf(":", 9) + 1;
            var l = o.substring(e, o.length - 1).trim();
            return l = o.substring(0, e).trim() + l + ";", 1 === j || 2 === j && n(l, 1) ? "-webkit-" + l + l : l
          }
          if (0 === j || 2 === j && !n(o, 1)) return o;
          switch (a) {
            case 1015:
              return 97 === o.charCodeAt(10) ? "-webkit-" + o + o : o;
            case 951:
              return 116 === o.charCodeAt(3) ? "-webkit-" + o + o : o;
            case 963:
              return 110 === o.charCodeAt(5) ? "-webkit-" + o + o : o;
            case 1009:
              if (100 !== o.charCodeAt(4)) break;
            case 969:
            case 942:
              return "-webkit-" + o + o;
            case 978:
              return "-webkit-" + o + "-moz-" + o + o;
            case 1019:
            case 983:
              return "-webkit-" + o + "-moz-" + o + "-ms-" + o + o;
            case 883:
              if (45 === o.charCodeAt(8)) return "-webkit-" + o + o;
              if (0 < o.indexOf("image-set(", 11)) return o.replace(_, "$1-webkit-$2") + o;
              break;
            case 932:
              if (45 === o.charCodeAt(4)) switch (o.charCodeAt(5)) {
                case 103:
                  return "-webkit-box-" + o.replace("-grow", "") + "-webkit-" + o + "-ms-" + o.replace("grow", "positive") + o;
                case 115:
                  return "-webkit-" + o + "-ms-" + o.replace("shrink", "negative") + o;
                case 98:
                  return "-webkit-" + o + "-ms-" + o.replace("basis", "preferred-size") + o
              }
              return "-webkit-" + o + "-ms-" + o + o;
            case 964:
              return "-webkit-" + o + "-ms-flex-" + o + o;
            case 1023:
              if (99 !== o.charCodeAt(8)) break;
              return "-webkit-box-pack" + (l = o.substring(o.indexOf(":", 15)).replace("flex-", "").replace("space-between", "justify")) + "-webkit-" + o + "-ms-flex-pack" + l + o;
            case 1005:
              return h.test(o) ? o.replace(d, ":-webkit-") + o.replace(d, ":-moz-") + o : o;
            case 1e3:
              switch (t = (l = o.substring(13).trim()).indexOf("-") + 1, l.charCodeAt(0) + l.charCodeAt(t)) {
                case 226:
                  l = o.replace(v, "tb");
                  break;
                case 232:
                  l = o.replace(v, "tb-rl");
                  break;
                case 220:
                  l = o.replace(v, "lr");
                  break;
                default:
                  return o
              }
              return "-webkit-" + o + "-ms-" + l + o;
            case 1017:
              if (-1 === o.indexOf("sticky", 9)) break;
            case 975:
              switch (t = (o = e).length - 10, a = (l = (33 === o.charCodeAt(t) ? o.substring(0, t) : o).substring(e.indexOf(":", 7) + 1).trim()).charCodeAt(0) + (0 | l.charCodeAt(7))) {
                case 203:
                  if (111 > l.charCodeAt(8)) break;
                case 115:
                  o = o.replace(l, "-webkit-" + l) + ";" + o;
                  break;
                case 207:
                case 102:
                  o = o.replace(l, "-webkit-" + (102 < a ? "inline-" : "") + "box") + ";" + o.replace(l, "-webkit-" + l) + ";" + o.replace(l, "-ms-" + l + "box") + ";" + o
              }
              return o + ";";
            case 938:
              if (45 === o.charCodeAt(5)) switch (o.charCodeAt(6)) {
                case 105:
                  return l = o.replace("-items", ""), "-webkit-" + o + "-webkit-box-" + l + "-ms-flex-" + l + o;
                case 115:
                  return "-webkit-" + o + "-ms-flex-item-" + o.replace(x, "") + o;
                default:
                  return "-webkit-" + o + "-ms-flex-line-pack" + o.replace("align-content", "").replace(x, "") + o
              }
              break;
            case 973:
            case 989:
              if (45 !== o.charCodeAt(3) || 122 === o.charCodeAt(4)) break;
            case 931:
            case 953:
              if (!0 === C.test(e)) return 115 === (l = e.substring(e.indexOf(":") + 1)).charCodeAt(0) ? i(e.replace("stretch", "fill-available"), t, r, s).replace(":fill-available", ":stretch") : o.replace(l, "-webkit-" + l) + o.replace(l, "-moz-" + l.replace("fill-", "")) + o;
              break;
            case 962:
              if (o = "-webkit-" + o + (102 === o.charCodeAt(5) ? "-ms-" + o : "") + o, 211 === r + s && 105 === o.charCodeAt(13) && 0 < o.indexOf("transform", 10)) return o.substring(0, o.indexOf(";", 27) + 1).replace(f, "$1-webkit-$2") + o
          }
          return o
        }

        function n(e, t) {
          var r = e.indexOf(1 === t ? ":" : "{"),
            i = e.substring(0, 3 !== t ? r : 10);
          return r = e.substring(r + 1, e.length - 1), F(2 !== t ? i : i.replace(S, "$1"), r, t)
        }

        function s(e, t) {
          var r = i(t, t.charCodeAt(0), t.charCodeAt(1), t.charCodeAt(2));
          return r !== t + ";" ? r.replace(A, " or ($1)").substring(4) : "(" + t + ")"
        }

        function o(e, t, r, i, n, s, o, a, c, u) {
          for (var d, h = 0, f = t; h < I; ++h) switch (d = E[h].call(l, e, f, r, i, n, s, o, a, c, u)) {
            case void 0:
            case !1:
            case !0:
            case null:
              break;
            default:
              f = d
          }
          if (f !== t) return f
        }

        function a(e) {
          return void 0 !== (e = e.prefix) && (F = null, e ? "function" != typeof e ? j = 1 : (j = 2, F = e) : j = 0), a
        }

        function l(e, r) {
          var a = e;
          if (33 > a.charCodeAt(0) && (a = a.trim()), a = [a], 0 < I) {
            var l = o(-1, r, a, a, k, O, 0, 0, 0, 0);
            void 0 !== l && "string" == typeof l && (r = l)
          }
          var d = function e(r, a, l, d, h) {
            for (var f, p, m, v, A, x = 0, S = 0, C = 0, _ = 0, E = 0, F = 0, P = m = f = 0, R = 0, z = 0, N = 0, D = 0, $ = l.length, B = $ - 1, H = "", W = "", U = "", q = ""; R < $;) {
              if (p = l.charCodeAt(R), R === B && 0 !== S + _ + C + x && (0 !== S && (p = 47 === S ? 10 : 47), _ = C = x = 0, $++, B++), 0 === S + _ + C + x) {
                if (R === B && (0 < z && (H = H.replace(u, "")), 0 < H.trim().length)) {
                  switch (p) {
                    case 32:
                    case 9:
                    case 59:
                    case 13:
                    case 10:
                      break;
                    default:
                      H += l.charAt(R)
                  }
                  p = 59
                }
                switch (p) {
                  case 123:
                    for (f = (H = H.trim()).charCodeAt(0), m = 1, D = ++R; R < $;) {
                      switch (p = l.charCodeAt(R)) {
                        case 123:
                          m++;
                          break;
                        case 125:
                          m--;
                          break;
                        case 47:
                          switch (p = l.charCodeAt(R + 1)) {
                            case 42:
                            case 47:
                              e: {
                                for (P = R + 1; P < B; ++P) switch (l.charCodeAt(P)) {
                                  case 47:
                                    if (42 === p && 42 === l.charCodeAt(P - 1) && R + 2 !== P) {
                                      R = P + 1;
                                      break e
                                    }
                                    break;
                                  case 10:
                                    if (47 === p) {
                                      R = P + 1;
                                      break e
                                    }
                                }
                                R = P
                              }
                          }
                          break;
                        case 91:
                          p++;
                        case 40:
                          p++;
                        case 34:
                        case 39:
                          for (; R++ < B && l.charCodeAt(R) !== p;);
                      }
                      if (0 === m) break;
                      R++
                    }
                    if (m = l.substring(D, R), 0 === f && (f = (H = H.replace(c, "").trim()).charCodeAt(0)), 64 === f) {
                      switch (0 < z && (H = H.replace(u, "")), p = H.charCodeAt(1)) {
                        case 100:
                        case 109:
                        case 115:
                        case 45:
                          z = a;
                          break;
                        default:
                          z = L
                      }
                      if (D = (m = e(a, z, m, p, h + 1)).length, 0 < I && (A = o(3, m, z = t(L, H, N), a, k, O, D, p, h, d), H = z.join(""), void 0 !== A && 0 === (D = (m = A.trim()).length) && (p = 0, m = "")), 0 < D) switch (p) {
                        case 115:
                          H = H.replace(w, s);
                        case 100:
                        case 109:
                        case 45:
                          m = H + "{" + m + "}";
                          break;
                        case 107:
                          m = (H = H.replace(g, "$1 $2")) + "{" + m + "}", m = 1 === j || 2 === j && n("@" + m, 3) ? "@-webkit-" + m + "@" + m : "@" + m;
                          break;
                        default:
                          m = H + m, 112 === d && (W += m, m = "")
                      } else m = ""
                    } else m = e(a, t(a, H, N), m, d, h + 1);
                    U += m, m = N = z = P = f = 0, H = "", p = l.charCodeAt(++R);
                    break;
                  case 125:
                  case 59:
                    if (1 < (D = (H = (0 < z ? H.replace(u, "") : H).trim()).length)) switch (0 === P && (45 === (f = H.charCodeAt(0)) || 96 < f && 123 > f) && (D = (H = H.replace(" ", ":")).length), 0 < I && void 0 !== (A = o(1, H, a, r, k, O, W.length, d, h, d)) && 0 === (D = (H = A.trim()).length) && (H = "\0\0"), f = H.charCodeAt(0), p = H.charCodeAt(1), f) {
                      case 0:
                        break;
                      case 64:
                        if (105 === p || 99 === p) {
                          q += H + l.charAt(R);
                          break
                        }
                      default:
                        58 !== H.charCodeAt(D - 1) && (W += i(H, f, p, H.charCodeAt(2)))
                    }
                    N = z = P = f = 0, H = "", p = l.charCodeAt(++R)
                }
              }
              switch (p) {
                case 13:
                case 10:
                  47 === S ? S = 0 : 0 === 1 + f && 107 !== d && 0 < H.length && (z = 1, H += "\0"), 0 < I * M && o(0, H, a, r, k, O, W.length, d, h, d), O = 1, k++;
                  break;
                case 59:
                case 125:
                  if (0 === S + _ + C + x) {
                    O++;
                    break
                  }
                default:
                  switch (O++, v = l.charAt(R), p) {
                    case 9:
                    case 32:
                      if (0 === _ + x + S) switch (E) {
                        case 44:
                        case 58:
                        case 9:
                        case 32:
                          v = "";
                          break;
                        default:
                          32 !== p && (v = " ")
                      }
                      break;
                    case 0:
                      v = "\\0";
                      break;
                    case 12:
                      v = "\\f";
                      break;
                    case 11:
                      v = "\\v";
                      break;
                    case 38:
                      0 === _ + S + x && (z = N = 1, v = "\f" + v);
                      break;
                    case 108:
                      if (0 === _ + S + x + T && 0 < P) switch (R - P) {
                        case 2:
                          112 === E && 58 === l.charCodeAt(R - 3) && (T = E);
                        case 8:
                          111 === F && (T = F)
                      }
                      break;
                    case 58:
                      0 === _ + S + x && (P = R);
                      break;
                    case 44:
                      0 === S + C + _ + x && (z = 1, v += "\r");
                      break;
                    case 34:
                    case 39:
                      0 === S && (_ = _ === p ? 0 : 0 === _ ? p : _);
                      break;
                    case 91:
                      0 === _ + S + C && x++;
                      break;
                    case 93:
                      0 === _ + S + C && x--;
                      break;
                    case 41:
                      0 === _ + S + x && C--;
                      break;
                    case 40:
                      0 === _ + S + x && (0 === f && (2 * E + 3 * F == 533 || (f = 1)), C++);
                      break;
                    case 64:
                      0 === S + C + _ + x + P + m && (m = 1);
                      break;
                    case 42:
                    case 47:
                      if (!(0 < _ + x + C)) switch (S) {
                        case 0:
                          switch (2 * p + 3 * l.charCodeAt(R + 1)) {
                            case 235:
                              S = 47;
                              break;
                            case 220:
                              D = R, S = 42
                          }
                          break;
                        case 42:
                          47 === p && 42 === E && D + 2 !== R && (33 === l.charCodeAt(D + 2) && (W += l.substring(D, R + 1)), v = "", S = 0)
                      }
                  }
                  0 === S && (H += v)
              }
              F = E, E = p, R++
            }
            if (0 < (D = W.length)) {
              if (z = a, 0 < I && void 0 !== (A = o(2, W, z, r, k, O, D, d, h, d)) && 0 === (W = A).length) return q + W + U;
              if (W = z.join(",") + "{" + W + "}", 0 != j * T) {
                switch (2 !== j || n(W, 2) || (T = 0), T) {
                  case 111:
                    W = W.replace(b, ":-moz-$1") + W;
                    break;
                  case 112:
                    W = W.replace(y, "::-webkit-input-$1") + W.replace(y, "::-moz-$1") + W.replace(y, ":-ms-input-$1") + W
                }
                T = 0
              }
            }
            return q + W + U
          }(L, a, r, 0, 0);
          return 0 < I && void 0 !== (l = o(-2, d, a, a, k, O, d.length, 0, 0, 0)) && (d = l), T = 0, O = k = 1, d
        }
        var c = /^\0+/g,
          u = /[\0\r\f]/g,
          d = /: */g,
          h = /zoo|gra/,
          f = /([,: ])(transform)/g,
          p = /,\r+?/g,
          m = /([\t\r\n ])*\f?&/g,
          g = /@(k\w+)\s*(\S*)\s*/,
          y = /::(place)/g,
          b = /:(read-only)/g,
          v = /[svh]\w+-[tblr]{2}/,
          w = /\(\s*(.*)\s*\)/g,
          A = /([\s\S]*?);/g,
          x = /-self|flex-/g,
          S = /[^]*?(:[rp][el]a[\w-]+)[^]*/,
          C = /stretch|:\s*\w+\-(?:conte|avail)/,
          _ = /([^-])(image-set\()/,
          O = 1,
          k = 1,
          T = 0,
          j = 1,
          L = [],
          E = [],
          I = 0,
          F = null,
          M = 0;
        return l.use = function e(t) {
          switch (t) {
            case void 0:
            case null:
              I = E.length = 0;
              break;
            default:
              if ("function" == typeof t) E[I++] = t;
              else if ("object" == typeof t)
                for (var r = 0, i = t.length; r < i; ++r) e(t[r]);
              else M = 0 | !!t
          }
          return e
        }, l.set = a, void 0 !== e && a(e), l
      }
    },
    17103(e, t, r) {
      "use strict";
      r.d(t, {
        A: () => i
      });
      let i = {
        animationIterationCount: 1,
        borderImageOutset: 1,
        borderImageSlice: 1,
        borderImageWidth: 1,
        boxFlex: 1,
        boxFlexGroup: 1,
        boxOrdinalGroup: 1,
        columnCount: 1,
        columns: 1,
        flex: 1,
        flexGrow: 1,
        flexPositive: 1,
        flexShrink: 1,
        flexNegative: 1,
        flexOrder: 1,
        gridRow: 1,
        gridRowEnd: 1,
        gridRowSpan: 1,
        gridRowStart: 1,
        gridColumn: 1,
        gridColumnEnd: 1,
        gridColumnSpan: 1,
        gridColumnStart: 1,
        msGridRow: 1,
        msGridRowSpan: 1,
        msGridColumn: 1,
        msGridColumnSpan: 1,
        fontWeight: 1,
        lineHeight: 1,
        opacity: 1,
        order: 1,
        orphans: 1,
        tabSize: 1,
        widows: 1,
        zIndex: 1,
        zoom: 1,
        WebkitLineClamp: 1,
        fillOpacity: 1,
        floodOpacity: 1,
        stopOpacity: 1,
        strokeDasharray: 1,
        strokeDashoffset: 1,
        strokeMiterlimit: 1,
        strokeOpacity: 1,
        strokeWidth: 1
      }
    },
    14744(e) {
      "use strict";
      var t = function(e) {
          var t, i, n;
          return !!(t = e) && "object" == typeof t && (i = e, "[object RegExp]" !== (n = Object.prototype.toString.call(i)) && "[object Date]" !== n && i.$$typeof !== r)
        },
        r = "function" == typeof Symbol && Symbol.for ? Symbol.for("react.element") : 60103;

      function i(e, t) {
        return !1 !== t.clone && t.isMergeableObject(e) ? a(Array.isArray(e) ? [] : {}, e, t) : e
      }

      function n(e, t, r) {
        return e.concat(t).map(function(e) {
          return i(e, r)
        })
      }

      function s(e) {
        return Object.keys(e).concat(Object.getOwnPropertySymbols ? Object.getOwnPropertySymbols(e).filter(function(t) {
          return Object.propertyIsEnumerable.call(e, t)
        }) : [])
      }

      function o(e, t) {
        try {
          return t in e
        } catch (e) {
          return !1
        }
      }

      function a(e, r, l) {
        (l = l || {}).arrayMerge = l.arrayMerge || n, l.isMergeableObject = l.isMergeableObject || t, l.cloneUnlessOtherwiseSpecified = i;
        var c, u, d = Array.isArray(r);
        return d !== Array.isArray(e) ? i(r, l) : d ? l.arrayMerge(e, r, l) : (u = {}, (c = l).isMergeableObject(e) && s(e).forEach(function(t) {
          u[t] = i(e[t], c)
        }), s(r).forEach(function(t) {
          o(e, t) && !(Object.hasOwnProperty.call(e, t) && Object.propertyIsEnumerable.call(e, t)) || (o(e, t) && c.isMergeableObject(r[t]) ? u[t] = (function(e, t) {
            if (!t.customMerge) return a;
            var r = t.customMerge(e);
            return "function" == typeof r ? r : a
          })(t, c)(e[t], r[t], c) : u[t] = i(r[t], c))
        }), u)
      }
      a.all = function(e, t) {
        if (!Array.isArray(e)) throw Error("first argument should be an array");
        return e.reduce(function(e, r) {
          return a(e, r, t)
        }, {})
      }, e.exports = a
    },
    43842() {
      ! function() {
        "use strict";

        function e(e) {
          var t = !0,
            r = !1,
            i = null,
            n = {
              text: !0,
              search: !0,
              url: !0,
              tel: !0,
              email: !0,
              password: !0,
              number: !0,
              date: !0,
              month: !0,
              week: !0,
              time: !0,
              datetime: !0,
              "datetime-local": !0
            };

          function s(e) {
            return !!e && e !== document && "HTML" !== e.nodeName && "BODY" !== e.nodeName && "classList" in e && "contains" in e.classList
          }

          function o(e) {
            e.classList.contains("focus-visible") || (e.classList.add("focus-visible"), e.setAttribute("data-focus-visible-added", ""))
          }

          function a(e) {
            t = !1
          }

          function l() {
            document.addEventListener("mousemove", c), document.addEventListener("mousedown", c), document.addEventListener("mouseup", c), document.addEventListener("pointermove", c), document.addEventListener("pointerdown", c), document.addEventListener("pointerup", c), document.addEventListener("touchmove", c), document.addEventListener("touchstart", c), document.addEventListener("touchend", c)
          }

          function c(e) {
            e.target.nodeName && "html" === e.target.nodeName.toLowerCase() || (t = !1, document.removeEventListener("mousemove", c), document.removeEventListener("mousedown", c), document.removeEventListener("mouseup", c), document.removeEventListener("pointermove", c), document.removeEventListener("pointerdown", c), document.removeEventListener("pointerup", c), document.removeEventListener("touchmove", c), document.removeEventListener("touchstart", c), document.removeEventListener("touchend", c))
          }
          document.addEventListener("keydown", function(r) {
            r.metaKey || r.altKey || r.ctrlKey || (s(e.activeElement) && o(e.activeElement), t = !0)
          }, !0), document.addEventListener("mousedown", a, !0), document.addEventListener("pointerdown", a, !0), document.addEventListener("touchstart", a, !0), document.addEventListener("visibilitychange", function(e) {
            "hidden" === document.visibilityState && (r && (t = !0), l())
          }, !0), l(), e.addEventListener("focus", function(e) {
            if (s(e.target)) {
              var r, i, a;
              (t || (i = (r = e.target).type, "INPUT" === (a = r.tagName) && n[i] && !r.readOnly || "TEXTAREA" === a && !r.readOnly || r.isContentEditable || 0)) && o(e.target)
            }
          }, !0), e.addEventListener("blur", function(e) {
            if (s(e.target) && (e.target.classList.contains("focus-visible") || e.target.hasAttribute("data-focus-visible-added"))) {
              var t;
              r = !0, window.clearTimeout(i), i = window.setTimeout(function() {
                r = !1
              }, 100), (t = e.target).hasAttribute("data-focus-visible-added") && (t.classList.remove("focus-visible"), t.removeAttribute("data-focus-visible-added"))
            }
          }, !0), e.nodeType === Node.DOCUMENT_FRAGMENT_NODE && e.host ? e.host.setAttribute("data-js-focus-visible", "") : e.nodeType === Node.DOCUMENT_NODE && (document.documentElement.classList.add("js-focus-visible"), document.documentElement.setAttribute("data-js-focus-visible", ""))
        }
        if ("u" > typeof window && "u" > typeof document) {
          var t;
          window.applyFocusVisiblePolyfill = e;
          try {
            t = new CustomEvent("focus-visible-polyfill-ready")
          } catch (e) {
            (t = document.createEvent("CustomEvent")).initCustomEvent("focus-visible-polyfill-ready", !1, !1, {})
          }
          window.dispatchEvent(t)
        }
        "u" > typeof document && e(document)
      }()
    },
    4146(e, t, r) {
      "use strict";
      var i = r(44363),
        n = {
          childContextTypes: !0,
          contextType: !0,
          contextTypes: !0,
          defaultProps: !0,
          displayName: !0,
          getDefaultProps: !0,
          getDerivedStateFromError: !0,
          getDerivedStateFromProps: !0,
          mixins: !0,
          propTypes: !0,
          type: !0
        },
        s = {
          name: !0,
          length: !0,
          prototype: !0,
          caller: !0,
          callee: !0,
          arguments: !0,
          arity: !0
        },
        o = {
          $$typeof: !0,
          compare: !0,
          defaultProps: !0,
          displayName: !0,
          propTypes: !0,
          type: !0
        },
        a = {};

      function l(e) {
        return i.isMemo(e) ? o : a[e.$$typeof] || n
      }
      a[i.ForwardRef] = {
        $$typeof: !0,
        render: !0,
        defaultProps: !0,
        displayName: !0,
        propTypes: !0
      }, a[i.Memo] = o;
      var c = Object.defineProperty,
        u = Object.getOwnPropertyNames,
        d = Object.getOwnPropertySymbols,
        h = Object.getOwnPropertyDescriptor,
        f = Object.getPrototypeOf,
        p = Object.prototype;
      e.exports = function e(t, r, i) {
        if ("string" != typeof r) {
          if (p) {
            var n = f(r);
            n && n !== p && e(t, n, i)
          }
          var o = u(r);
          d && (o = o.concat(d(r)));
          for (var a = l(t), m = l(r), g = 0; g < o.length; ++g) {
            var y = o[g];
            if (!s[y] && !(i && i[y]) && !(m && m[y]) && !(a && a[y])) {
              var b = h(r, y);
              try {
                c(t, y, b)
              } catch (e) {}
            }
          }
        }
        return t
      }
    },
    62383(e, t, r) {
      e = r.nmd(e);
      var i, n, s, o = "[object Map]",
        a = "[object Promise]",
        l = "[object Set]",
        c = "[object WeakMap]",
        u = "[object DataView]",
        d = /^\[object .+?Constructor\]$/,
        h = "object" == typeof r.g && r.g && r.g.Object === Object && r.g,
        f = "object" == typeof self && self && self.Object === Object && self,
        p = h || f || Function("return this")(),
        m = t && !t.nodeType && t,
        g = m && e && !e.nodeType && e,
        y = g && g.exports === m,
        b = Function.prototype,
        v = Object.prototype,
        w = p["__core-js_shared__"],
        A = (i = /[^.]+$/.exec(w && w.keys && w.keys.IE_PROTO || "")) ? "Symbol(src)_1." + i : "",
        x = b.toString,
        S = v.hasOwnProperty,
        C = v.toString,
        _ = RegExp("^" + x.call(S).replace(/[\\^$.*+?()[\]{}|]/g, "\\$&").replace(/hasOwnProperty|(function).*?(?=\\\()| for .+?(?=\\\])/g, "$1.*?") + "$"),
        O = y ? p.Buffer : void 0,
        k = v.propertyIsEnumerable,
        T = O ? O.isBuffer : void 0,
        j = (n = Object.keys, s = Object, function(e) {
          return n(s(e))
        }),
        L = B(p, "DataView"),
        E = B(p, "Map"),
        I = B(p, "Promise"),
        F = B(p, "Set"),
        M = B(p, "WeakMap"),
        P = !k.call({
          valueOf: 1
        }, "valueOf"),
        R = W(L),
        z = W(E),
        N = W(I),
        D = W(F),
        $ = W(M);

      function B(e, t) {
        var r, i = null == e ? void 0 : e[t];
        return !(!K(i) || (r = i, A && A in r)) && (G(i) || function(e) {
          var t = !1;
          if (null != e && "function" != typeof e.toString) try {
            t = !!(e + "")
          } catch (e) {}
          return t
        }(i) ? _ : d).test(W(i)) ? i : void 0
      }
      var H = function(e) {
        return C.call(e)
      };

      function W(e) {
        if (null != e) {
          try {
            return x.call(e)
          } catch (e) {}
          try {
            return e + ""
          } catch (e) {}
        }
        return ""
      }(L && H(new L(new ArrayBuffer(1))) != u || E && H(new E) != o || I && H(I.resolve()) != a || F && H(new F) != l || M && H(new M) != c) && (H = function(e) {
        var t = C.call(e),
          r = "[object Object]" == t ? e.constructor : void 0,
          i = r ? W(r) : void 0;
        if (i) switch (i) {
          case R:
            return u;
          case z:
            return o;
          case N:
            return a;
          case D:
            return l;
          case $:
            return c
        }
        return t
      });
      var U = Array.isArray;

      function q(e) {
        var t;
        return null != e && "number" == typeof(t = e.length) && t > -1 && t % 1 == 0 && t <= 0x1fffffffffffff && !G(e)
      }
      var V = T || function() {
        return !1
      };

      function G(e) {
        var t = K(e) ? C.call(e) : "";
        return "[object Function]" == t || "[object GeneratorFunction]" == t
      }

      function K(e) {
        var t = typeof e;
        return !!e && ("object" == t || "function" == t)
      }
      e.exports = function(e) {
        if (q(e) && (U(e) || "string" == typeof e || "function" == typeof e.splice || V(e) || (r = t = e) && "object" == typeof r && q(t) && S.call(e, "callee") && (!k.call(e, "callee") || "[object Arguments]" == C.call(e)))) return !e.length;
        var t, r, i, n = H(e);
        if (n == o || n == l) return !e.size;
        if (P || (i = e && e.constructor, e === ("function" == typeof i && i.prototype || v))) return !j(e).length;
        for (var s in e)
          if (S.call(e, s)) return !1;
        return !0
      }
    },
    61669(e) {
      e.exports = function(e) {
        var t = typeof e;
        return !!e && ("object" == t || "function" == t)
      }
    },
    45228(e) {
      "use strict";
      var t = Object.getOwnPropertySymbols,
        r = Object.prototype.hasOwnProperty,
        i = Object.prototype.propertyIsEnumerable;
      e.exports = ! function() {
        try {
          if (!Object.assign) return !1;
          var e = new String("abc");
          if (e[5] = "de", "5" === Object.getOwnPropertyNames(e)[0]) return !1;
          for (var t = {}, r = 0; r < 10; r++) t["_" + String.fromCharCode(r)] = r;
          var i = Object.getOwnPropertyNames(t).map(function(e) {
            return t[e]
          });
          if ("0123456789" !== i.join("")) return !1;
          var n = {};
          if ("abcdefghijklmnopqrst".split("").forEach(function(e) {
              n[e] = e
            }), "abcdefghijklmnopqrst" !== Object.keys(Object.assign({}, n)).join("")) return !1;
          return !0
        } catch (e) {
          return !1
        }
      }() ? function(e, n) {
        for (var s, o, a = function(e) {
            if (null == e) throw TypeError("Object.assign cannot be called with null or undefined");
            return Object(e)
          }(e), l = 1; l < arguments.length; l++) {
          for (var c in s = Object(arguments[l])) r.call(s, c) && (a[c] = s[c]);
          if (t) {
            o = t(s);
            for (var u = 0; u < o.length; u++) i.call(s, o[u]) && (a[o[u]] = s[o[u]])
          }
        }
        return a
      } : Object.assign
    },
    54405(e, t) {
      "use strict";
      var r = Symbol.for("react.transitional.element"),
        i = Symbol.for("react.portal"),
        n = Symbol.for("react.fragment"),
        s = Symbol.for("react.strict_mode"),
        o = Symbol.for("react.profiler"),
        a = Symbol.for("react.consumer"),
        l = Symbol.for("react.context"),
        c = Symbol.for("react.forward_ref"),
        u = Symbol.for("react.suspense"),
        d = Symbol.for("react.suspense_list"),
        h = Symbol.for("react.memo"),
        f = Symbol.for("react.lazy"),
        p = Symbol.for("react.view_transition"),
        m = Symbol.for("react.client.reference");

      function g(e) {
        if ("object" == typeof e && null !== e) {
          var t = e.$$typeof;
          switch (t) {
            case r:
              switch (e = e.type) {
                case n:
                case o:
                case s:
                case u:
                case d:
                case p:
                  return e;
                default:
                  switch (e = e && e.$$typeof) {
                    case l:
                    case c:
                    case f:
                    case h:
                    case a:
                      return e;
                    default:
                      return t
                  }
              }
            case i:
              return t
          }
        }
      }
      t.ContextConsumer = a, t.ContextProvider = l, t.Element = r, t.ForwardRef = c, t.Fragment = n, t.Lazy = f, t.Memo = h, t.Portal = i, t.Profiler = o, t.StrictMode = s, t.Suspense = u, t.SuspenseList = d, t.isContextConsumer = function(e) {
        return g(e) === a
      }, t.isContextProvider = function(e) {
        return g(e) === l
      }, t.isElement = function(e) {
        return "object" == typeof e && null !== e && e.$$typeof === r
      }, t.isForwardRef = function(e) {
        return g(e) === c
      }, t.isFragment = function(e) {
        return g(e) === n
      }, t.isLazy = function(e) {
        return g(e) === f
      }, t.isMemo = function(e) {
        return g(e) === h
      }, t.isPortal = function(e) {
        return g(e) === i
      }, t.isProfiler = function(e) {
        return g(e) === o
      }, t.isStrictMode = function(e) {
        return g(e) === s
      }, t.isSuspense = function(e) {
        return g(e) === u
      }, t.isSuspenseList = function(e) {
        return g(e) === d
      }, t.isValidElementType = function(e) {
        return "string" == typeof e || "function" == typeof e || e === n || e === o || e === s || e === u || e === d || "object" == typeof e && null !== e && (e.$$typeof === f || e.$$typeof === h || e.$$typeof === l || e.$$typeof === a || e.$$typeof === c || e.$$typeof === m || void 0 !== e.getModuleId) || !1
      }, t.typeOf = g
    },
    44363(e, t, r) {
      "use strict";
      e.exports = r(54405)
    },
    2833(e) {
      e.exports = function(e, t, r, i) {
        var n = r ? r.call(i, e, t) : void 0;
        if (void 0 !== n) return !!n;
        if (e === t) return !0;
        if ("object" != typeof e || !e || "object" != typeof t || !t) return !1;
        var s = Object.keys(e),
          o = Object.keys(t);
        if (s.length !== o.length) return !1;
        for (var a = Object.prototype.hasOwnProperty.bind(t), l = 0; l < s.length; l++) {
          var c = s[l];
          if (!a(c)) return !1;
          var u = e[c],
            d = t[c];
          if (!1 === (n = r ? r.call(i, u, d, c) : void 0) || void 0 === n && u !== d) return !1
        }
        return !0
      }
    },
    57304(e, t, r) {
      "use strict";
      r.d(t, {
        G1: () => d.G,
        Il: () => o.I,
        Jt: () => i.Jt,
        PQ: () => c.P,
        Tp: () => u.T,
        Vg: () => l.V,
        Zp: () => n.Z,
        pn: () => a.p,
        r7: () => f.r,
        xe: () => h.xe,
        yW: () => s.y
      });
      var i = r(49236),
        n = r(75447),
        s = r(77638),
        o = r(3962),
        a = r(58523),
        l = r(96069),
        c = r(84995),
        u = r(43581),
        d = r(59756),
        h = r(89165),
        f = r(42049);
      r(38144), n.A.width, n.A.height, n.A.minWidth, n.A.minHeight, n.A.maxWidth, n.A.maxHeight, n.A.size, n.A.verticalAlign, n.A.display, n.A.overflow, n.A.overflowX, n.A.overflowY, s.A.opacity, o.A.fontSize, o.A.fontFamily, o.A.fontWeight, o.A.lineHeight, o.A.textAlign, o.A.fontStyle, o.A.letterSpacing, a.A.alignItems, a.A.alignContent, a.A.justifyItems, a.A.justifyContent, a.A.flexWrap, a.A.flexDirection, a.A.flex, a.A.flexGrow, a.A.flexShrink, a.A.flexBasis, a.A.justifySelf, a.A.alignSelf, a.A.order, l.A.gridGap, l.A.gridColumnGap, l.A.gridRowGap, l.A.gridColumn, l.A.gridRow, l.A.gridAutoFlow, l.A.gridAutoColumns, l.A.gridAutoRows, l.A.gridTemplateColumns, l.A.gridTemplateRows, l.A.gridTemplateAreas, l.A.gridArea, c.A.borderWidth, c.A.borderStyle, c.A.borderColor, c.A.borderTop, c.A.borderRight, c.A.borderBottom, c.A.borderLeft, c.A.borderRadius, u.A.backgroundImage, u.A.backgroundSize, u.A.backgroundPosition, u.A.backgroundRepeat, d.A.zIndex, d.A.top, d.A.right, d.A.bottom, d.A.left
    },
    11937(e, t, r) {
      "use strict";
      r.d(t, {
        K1: () => i.K1,
        U0: () => n.U,
        Z0: () => i.Z0,
        tp: () => i.tp
      });
      var i = r(55966),
        n = r(84366);
      r(23635)
    },
    45846(e, t, r) {
      "use strict";
      r.d(t, {
        a: () => o
      });
      var i = r(38267),
        n = r(57304),
        s = r(49539);
      let o = i.Ay.div.withConfig({
        displayName: "Box",
        componentId: "sc-62in7e-0"
      })(n.xe, n.yW, n.Il, n.Zp, n.pn, n.Vg, n.Tp, n.PQ, n.G1, n.r7, s.sx)
    },
    85203(e, t, r) {
      "use strict";
      r.d(t, {
        l: () => g
      });
      var i = r(61398),
        n = r(49539),
        s = r(38267),
        o = r(96540),
        a = r(74848);
      let l = (0, s.Ay)(i.l).withConfig({
          shouldForwardProp: e => "sx" !== e
        }).withConfig({
          displayName: "Dialog__StyledDialog",
          componentId: "sc-19zph8h-0"
        })(["", ""], n.sx),
        c = (0, o.forwardRef)(function({
          as: e,
          ...t
        }, r) {
          return (0, a.jsx)(l, {
            ref: r,
            ...e ? {
              forwardedAs: e
            } : {},
            ...t
          })
        }),
        u = (0, s.Ay)(i.l.Header).withConfig({
          shouldForwardProp: e => "sx" !== e
        }).withConfig({
          displayName: "Dialog__StyledDialogHeader",
          componentId: "sc-19zph8h-1"
        })(["", ""], n.sx),
        d = (0, o.forwardRef)(function({
          as: e,
          ...t
        }, r) {
          return (0, a.jsx)(u, {
            ref: r,
            ...e ? {
              forwardedAs: e
            } : {},
            ...t
          })
        }),
        h = (0, s.Ay)(i.l.Body).withConfig({
          shouldForwardProp: e => "sx" !== e
        }).withConfig({
          displayName: "Dialog__StyledDialogBody",
          componentId: "sc-19zph8h-2"
        })(["", ""], n.sx),
        f = (0, o.forwardRef)(function({
          as: e,
          ...t
        }, r) {
          return (0, a.jsx)(h, {
            ref: r,
            ...e ? {
              forwardedAs: e
            } : {},
            ...t
          })
        }),
        p = (0, s.Ay)(i.l.Footer).withConfig({
          shouldForwardProp: e => "sx" !== e
        }).withConfig({
          displayName: "Dialog__StyledDialogFooter",
          componentId: "sc-19zph8h-3"
        })(["", ""], n.sx),
        m = (0, o.forwardRef)(function({
          as: e,
          ...t
        }, r) {
          return (0, a.jsx)(p, {
            ref: r,
            ...e ? {
              forwardedAs: e
            } : {},
            ...t
          })
        });
      d.__SLOT__ = i.l.Header.__SLOT__, f.__SLOT__ = i.l.Body.__SLOT__, m.__SLOT__ = i.l.Footer.__SLOT__;
      let g = Object.assign(c, {
        __SLOT__: i.l.__SLOT__,
        Buttons: i.l.Buttons,
        Header: d,
        Body: f,
        Footer: m
      })
    },
    65729(e, t, r) {
      "use strict";
      r.d(t, {
        z: () => f
      });
      var i = r(31356),
        n = r(38267),
        s = r(49539),
        o = r(45846),
        a = r(96540),
        l = r(74848);
      let c = (0, n.Ay)(i.z).withConfig({
          shouldForwardProp: e => "sx" !== e
        }).withConfig({
          displayName: "PageHeader__StyledPageHeader",
          componentId: "sc-1g9symn-0"
        })(["", ""], s.sx),
        u = a.forwardRef(({
          as: e,
          ...t
        }, r) => (0, l.jsx)(c, {
          ...t,
          ...e ? {
            forwardedAs: e
          } : {},
          ref: r
        }));

      function d({
        sx: e,
        ...t
      }) {
        let r = {};
        if (e) {
          let {
            fontSize: t,
            lineHeight: i,
            fontWeight: n
          } = e;
          t && (r["--custom-font-size"] = t), i && (r["--custom-line-height"] = i), n && (r["--custom-font-weight"] = n)
        }
        return (0, l.jsx)(o.a, {
          ...t,
          as: i.z.Title,
          style: r,
          sx: e
        })
      }
      let h = (0, n.Ay)(i.z.TitleArea).withConfig({
          shouldForwardProp: e => "sx" !== e
        }).withConfig({
          displayName: "PageHeader__PageHeaderTitleArea",
          componentId: "sc-1g9symn-1"
        })(["", ""], s.sx),
        f = Object.assign(u, {
          Actions: function({
            sx: e,
            ...t
          }) {
            let r = {};
            if (e) {
              let {
                height: t
              } = e;
              t && (r["--custom-height"] = t)
            }
            return (0, l.jsx)(o.a, {
              ...t,
              as: i.z.Actions,
              style: r,
              sx: e
            })
          },
          ContextArea: i.z.ContextArea,
          ParentLink: i.z.ParentLink,
          ContextBar: i.z.ContextBar,
          TitleArea: h,
          ContextAreaActions: i.z.ContextAreaActions,
          LeadingAction: i.z.LeadingAction,
          Breadcrumbs: i.z.Breadcrumbs,
          LeadingVisual: i.z.LeadingVisual,
          Title: ({
            as: e,
            ...t
          }) => (0, l.jsx)(d, {
            ...t,
            ...e ? {
              forwardedAs: e
            } : {}
          }),
          TrailingVisual: i.z.TrailingVisual,
          Description: i.z.Description,
          TrailingAction: i.z.TrailingAction
        })
    },
    49716(e, t, r) {
      "use strict";
      r.d(t, {
        m: () => a
      });
      var i = r(55717),
        n = r(45846),
        s = r(96540),
        o = r(74848);
      let a = (0, s.forwardRef)(function(e, t) {
        return (0, o.jsx)(n.a, {
          as: i.m,
          ref: t,
          ...e
        })
      });
      a.__SLOT__ = i.m.__SLOT__
    },
    94709(e, t, r) {
      "use strict";
      r.d(t, {
        eu: () => q,
        JU: () => eb,
        MJ: () => es,
        NP: () => f,
        BI: () => Q,
        lF: () => $,
        zY: () => e_.z,
        TM: () => eR,
        Hx: () => ei,
        m_: () => eU.m,
        $n: () => Y,
        ou: () => eG,
        K0: () => em,
        z9: () => eS,
        $c: () => et,
        EY: () => eF,
        N_: () => eA,
        sx: () => C.sx,
        Wy: () => W,
        DZ: () => eh,
        DP: () => p,
        h1: () => u,
        PA: () => eQ,
        y$: () => eL,
        yB: () => x,
        az: () => i.a,
        Kf: () => eW,
        cA: () => v,
        Ou: () => e0,
        ks: () => eB
      });
      var i = r(45846),
        n = r(96540),
        s = r(40961),
        o = r(38267),
        a = r(92166),
        l = r(49021),
        c = r(36293),
        u = r(14744),
        d = r(74848);
      let h = n.createContext({
          setColorMode: () => null,
          setDayScheme: () => null,
          setNightScheme: () => null
        }),
        f = ({
          children: e,
          ...t
        }) => {
          let {
            theme: r,
            colorMode: i,
            dayScheme: f,
            nightScheme: y
          } = p(), b = t.theme ?? r ?? a.A, v = (0, l.B)(), {
            resolvedServerColorMode: w
          } = (e => {
            try {
              let t = document.getElementById(`__PRIMER_DATA_${e}__`)?.textContent;
              if (t) return JSON.parse(t)
            } catch (e) {}
            return {}
          })(v), A = n.useRef(w), [x, S] = (0, c.N)(t.colorMode ?? i ?? "day"), [C, _] = (0, c.N)(t.dayScheme ?? f ?? "light"), [O, k] = (0, c.N)(t.nightScheme ?? y ?? "dark"), T = function() {
            let [e, t] = n.useState(m);
            return n.useEffect(() => {
              let e = window?.matchMedia?.("(prefers-color-scheme: dark)");

              function r(e) {
                return e ? "night" : "day"
              }

              function i(e) {
                t(r(e.matches))
              }
              if (e) {
                if (t(r(e.matches)), void 0 !== e.addEventListener) return e.addEventListener("change", i),
                  function() {
                    e.removeEventListener("change", i)
                  };
                if (void 0 !== e.addListener) return e.addListener(i),
                  function() {
                    e.removeListener(i)
                  }
              }
            }, []), e
          }(), j = A.current || g(x, T), L = function(e, t, r) {
            switch (e) {
              case "day":
              case "light":
                return t;
              case "dark":
              case "night":
                return r
            }
          }(j, C, O), {
            resolvedTheme: E,
            resolvedColorScheme: I
          } = n.useMemo(() => (function(e, t) {
            if (!e.colorSchemes) return {
              resolvedTheme: e,
              resolvedColorScheme: void 0
            };
            if (!e.colorSchemes[t]) {
              console.error(`\`${t}\` scheme not defined in \`theme.colorSchemes\``);
              let r = Object.keys(e.colorSchemes)[0];
              return {
                resolvedTheme: u(e, e.colorSchemes[r]),
                resolvedColorScheme: r
              }
            }
            return {
              resolvedTheme: u(e, e.colorSchemes[t]),
              resolvedColorScheme: t
            }
          })(b, L), [b, L]);
          return n.useEffect(function() {
            let e = g(x, T);
            A.current && (A.current !== e && window.setTimeout(() => {
              s.flushSync(() => {
                S(e)
              }), S(x)
            }), A.current = null)
          }, [x, T, S]), (0, d.jsx)(h.Provider, {
            value: {
              theme: E,
              colorScheme: L,
              colorMode: x,
              resolvedColorMode: j,
              resolvedColorScheme: I,
              dayScheme: C,
              nightScheme: O,
              setColorMode: S,
              setDayScheme: _,
              setNightScheme: k
            },
            children: (0, d.jsxs)(o.NP, {
              theme: E,
              children: [e, t.preventSSRMismatch ? (0, d.jsx)("script", {
                type: "application/json",
                id: `__PRIMER_DATA_${v}__`,
                dangerouslySetInnerHTML: {
                  __html: JSON.stringify({
                    resolvedServerColorMode: j
                  })
                }
              }) : null]
            })
          })
        };

      function p() {
        return n.useContext(h)
      }

      function m() {
        return "u" > typeof window && window.matchMedia?.("(prefers-color-scheme: dark)")?.matches ? "night" : "day"
      }

      function g(e, t) {
        return "auto" === e ? t : e
      }
      var y = r(34164);
      r(43842);
      let b = (0, o.DU)(["*{box-sizing:border-box;}body{margin:0;}table{border-collapse:collapse;}[data-color-mode='light'] input{color-scheme:light;}[data-color-mode='dark'] input{color-scheme:dark;}@media (prefers-color-scheme:light){[data-color-mode='auto'][data-light-theme*='light']{color-scheme:light;}}@media (prefers-color-scheme:dark){[data-color-mode='auto'][data-dark-theme*='dark']{color-scheme:dark;}}[role='button']:focus:not(:focus-visible):not(:global(.focus-visible)),[role='tabpanel'][tabindex='0']:focus:not(:focus-visible):not(:global(.focus-visible)),button:focus:not(:focus-visible):not(:global(.focus-visible)),summary:focus:not(:focus-visible):not(:global(.focus-visible)),a:focus:not(:focus-visible):not(:global(.focus-visible)){outline:none;box-shadow:none;}[tabindex='0']:focus:not(:focus-visible):not(:global(.focus-visible)),details-dialog:focus:not(:focus-visible):not(:global(.focus-visible)){outline:none;}.BaseStyles{font-family:var(--BaseStyles-fontFamily,var(--fontStack-system));line-height:var(--BaseStyles-lineHeight,1.5);color:var(--BaseStyles-fgColor,var(--fgColor-default));&:has([data-color-mode='light']){input &{color-scheme:light;}}&:has([data-color-mode='dark']){input &{color-scheme:dark;}}:where(a:not([class*='prc-']):not([class*='PRC-']):not([class*='Primer_Brand__'])){color:var(--fgColor-accent,var(--color-accent-fg));text-decoration:none;&:hover{text-decoration:underline;}}}"]);

      function v({
        children: e,
        color: t,
        fontFamily: r,
        lineHeight: i,
        className: n,
        as: s = "div",
        style: o,
        ...a
      }) {
        let {
          colorMode: l,
          colorScheme: c,
          dayScheme: u,
          nightScheme: h
        } = p();
        return (0, d.jsxs)(s, {
          className: (0, y.$)("BaseStyles", n),
          "data-portal-root": !0,
          "data-color-mode": "auto" === l ? "auto" : c?.includes("dark") ? "dark" : "light",
          "data-light-theme": u,
          "data-dark-theme": h,
          style: {
            "--BaseStyles-fgColor": t,
            "--BaseStyles-fontFamily": r,
            "--BaseStyles-lineHeight": i,
            ...o
          },
          ...a,
          children: [(0, d.jsx)(b, {
            colorScheme: c?.includes("dark") ? "dark" : "light"
          }), e]
        })
      }
      var w = r(57227);
      let {
        Jt: A
      } = r(57304), x = e => (0, w.y)(e, A(a.A, e));
      var S = r(18990),
        C = r(49539);
      let _ = (0, o.Ay)(S.l).withConfig({
          shouldForwardProp: e => "sx" !== e
        }).withConfig({
          displayName: "ActionList__StyledActionList",
          componentId: "sc-hw2362-0"
        })(["", ""], C.sx),
        O = n.forwardRef(function({
          as: e,
          ...t
        }, r) {
          return (0, d.jsx)(_, {
            ref: r,
            ...t,
            ...e ? {
              forwardedAs: e
            } : {}
          })
        }),
        k = (0, o.Ay)(S.l.LinkItem).withConfig({
          shouldForwardProp: e => "sx" !== e
        }).withConfig({
          displayName: "ActionList__StyledActionListLinkItem",
          componentId: "sc-hw2362-1"
        })(["", ""], C.sx),
        T = n.forwardRef(({
          children: e,
          as: t,
          ...r
        }, i) => (0, d.jsx)(k, {
          ref: i,
          ...r,
          ...t ? {
            forwardedAs: t
          } : {},
          children: e
        }));
      T.displayName = "ActionList.LinkItem";
      let j = (0, o.Ay)(S.l.TrailingAction).withConfig({
          shouldForwardProp: e => "sx" !== e
        }).withConfig({
          displayName: "ActionList__StyledActionListTrailingAction",
          componentId: "sc-hw2362-2"
        })(["", ""], C.sx),
        L = n.forwardRef((e, t) => {
          let {
            as: r,
            ...i
          } = e;
          return (0, d.jsx)(j, {
            ...i,
            ...r ? {
              forwardedAs: r
            } : {},
            ref: t
          })
        }),
        E = (0, o.Ay)(S.l.Item).withConfig({
          shouldForwardProp: e => "sx" !== e
        }).withConfig({
          displayName: "ActionList__StyledActionListItem",
          componentId: "sc-hw2362-3"
        })(["", ""], C.sx),
        I = n.forwardRef(({
          children: e,
          as: t,
          ...r
        }, i) => (0, d.jsx)(E, {
          ref: i,
          ...r,
          ...t ? {
            forwardedAs: t
          } : {},
          children: e
        })),
        F = (0, o.Ay)(S.l.Group).withConfig({
          shouldForwardProp: e => "sx" !== e
        }).withConfig({
          displayName: "ActionList__StyledActionListGroup",
          componentId: "sc-hw2362-4"
        })(["", ""], C.sx),
        M = ({
          children: e,
          as: t,
          ...r
        }) => (0, d.jsx)(F, {
          ...r,
          ...t ? {
            forwardedAs: t
          } : {},
          children: e
        });
      M.displayName = "ActionList.Group";
      let P = (0, o.Ay)(S.l.Divider).withConfig({
          shouldForwardProp: e => "sx" !== e
        }).withConfig({
          displayName: "ActionList__ActionListDivider",
          componentId: "sc-hw2362-5"
        })(["", ""], C.sx),
        R = (0, o.Ay)(S.l.LeadingVisual).withConfig({
          shouldForwardProp: e => "sx" !== e
        }).withConfig({
          displayName: "ActionList__StyledActionListLeadingVisual",
          componentId: "sc-hw2362-6"
        })(["", ""], C.sx),
        z = ({
          children: e,
          as: t,
          ...r
        }) => (0, d.jsx)(R, {
          ...r,
          ...t ? {
            forwardedAs: t
          } : {},
          children: e
        });
      z.displayName = "ActionList.LeadingVisual";
      let N = (0, o.Ay)(S.l.TrailingVisual).withConfig({
          shouldForwardProp: e => "sx" !== e
        }).withConfig({
          displayName: "ActionList__StyledActionListTrailingVisual",
          componentId: "sc-hw2362-7"
        })(["", ""], C.sx),
        D = ({
          children: e,
          as: t,
          ...r
        }) => (0, d.jsx)(N, {
          ...r,
          ...t ? {
            forwardedAs: t
          } : {},
          children: e
        });
      D.displayName = "ActionList.TrailingVisual";
      let $ = Object.assign(O, {
        Item: I,
        LinkItem: T,
        Group: M,
        GroupHeading: S.l.GroupHeading,
        Divider: P,
        Description: S.l.Description,
        LeadingVisual: z,
        TrailingVisual: D,
        Heading: S.l.Heading,
        TrailingAction: L
      });
      I.__SLOT__ = S.l.Item.__SLOT__, T.__SLOT__ = S.l.LinkItem.__SLOT__, M.__SLOT__ = S.l.Group.__SLOT__, P.__SLOT__ = S.l.Divider.__SLOT__, z.__SLOT__ = S.l.LeadingVisual.__SLOT__, D.__SLOT__ = S.l.TrailingVisual.__SLOT__, L.__SLOT__ = S.l.TrailingAction.__SLOT__;
      var B = r(67323);
      let H = (0, o.Ay)(B.W.Overlay).withConfig({
          shouldForwardProp: e => "sx" !== e
        }).withConfig({
          displayName: "ActionMenu__ActionMenuOverlay",
          componentId: "sc-w5s60e-0"
        })(["", ""], C.sx),
        W = Object.assign(B.W, {
          Button: B.W.Button,
          Anchor: B.W.Anchor,
          Overlay: H,
          Divider: B.W.Divider
        });
      H.__SLOT__ = B.W.Overlay.__SLOT__;
      var U = r(35490);
      let q = (0, n.forwardRef)(function(e, t) {
        return (0, d.jsx)(i.a, {
          as: U.A,
          ref: t,
          ...e
        })
      });
      var V = r(30022);
      let G = (0, o.Ay)(V.A).withConfig({
          shouldForwardProp: e => "sx" !== e
        }).withConfig({
          displayName: "Breadcrumbs__BreadcrumbsImpl",
          componentId: "sc-1qj8pw-0"
        })(["", ""], C.sx),
        K = (0, o.Ay)(V.A.Item).withConfig({
          shouldForwardProp: e => "sx" !== e
        }).withConfig({
          displayName: "Breadcrumbs__StyledBreadcrumbsItem",
          componentId: "sc-1qj8pw-1"
        })(["", ""], C.sx),
        Q = Object.assign(G, {
          Item: function({
            as: e,
            ...t
          }) {
            return (0, d.jsx)(K, {
              ...t,
              ...e ? {
                forwardedAs: e
              } : {}
            })
          }
        });
      var Z = r(21373);
      let X = (0, o.Ay)(Z.Q).withConfig({
          shouldForwardProp: e => "sx" !== e
        }).withConfig({
          displayName: "Button__StyledButtonComponent",
          componentId: "sc-vqy3e4-0"
        })(["", ""], C.sx),
        Y = (0, n.forwardRef)(({
          as: e,
          sx: t,
          style: r,
          ...i
        }, n) => {
          let {
            block: s,
            size: o = "medium",
            leadingVisual: a,
            trailingVisual: l,
            trailingAction: c
          } = i, u = {}, h = {
            ...r || {}
          };
          if (null !== t && Object.keys(t || {}).length > 0) {
            u = J({
              block: s,
              size: o,
              leadingVisual: a,
              trailingVisual: l,
              trailingAction: c
            }, t);
            let {
              color: e
            } = t;
            e && (h["--button-color"] = e)
          }
          return (0, d.jsx)(X, {
            style: h,
            sx: u,
            ref: n,
            ...i,
            ...e ? {
              forwardedAs: e
            } : {}
          })
        });

      function J(e, t) {
        let r = `[data-size="${e.size}"]`,
          i = e.block ? '[data-block="block"]' : "",
          n = e.leadingVisual || e.trailingVisual || e.trailingAction ? "" : "[data-no-visuals]",
          s = `&${r}${i}${n}`,
          o = {};
        return t && (o[s] = t), o
      }
      Y.displayName = "Button", Y.__SLOT__ = Z.Q.__SLOT__;
      var ee = r(7771);
      let et = (0, n.forwardRef)(function(e, t) {
        return (0, d.jsx)(i.a, {
          as: ee.A,
          ref: t,
          ...e
        })
      });
      r(85203);
      var er = r(59134);
      let ei = (0, o.Ay)(er.A).withConfig({
        shouldForwardProp: e => "sx" !== e
      }).withConfig({
        displayName: "Flash",
        componentId: "sc-413izo-0"
      })(["", ""], C.sx);
      var en = r(7624);
      let es = Object.assign((0, o.Ay)(en.A).withConfig({
        shouldForwardProp: e => "sx" !== e
      }).withConfig({
        displayName: "FormControl__FormControlImpl",
        componentId: "sc-1642wfe-0"
      })(["", ""], C.sx), {
        __SLOT__: en.A.__SLOT__,
        Caption: en.A.Caption,
        LeadingVisual: en.A.LeadingVisual,
        Validation: en.A.Validation,
        Label: en.A.Label
      });
      var eo = r(47703);
      let ea = (0, n.forwardRef)(function(e, t) {
          return (0, d.jsx)(i.a, {
            as: eo.A,
            ref: t,
            ...e
          })
        }),
        el = (0, n.forwardRef)(({
          as: e,
          ...t
        }, r) => (0, d.jsx)(ea, {
          ...t,
          ...e ? {
            forwardedAs: e
          } : {},
          ref: r
        })),
        ec = (0, n.forwardRef)(function(e, t) {
          return (0, d.jsx)(i.a, {
            as: eo.A.Item,
            ref: t,
            ...e
          })
        }),
        eu = (0, n.forwardRef)(function(e, t) {
          return (0, d.jsx)(i.a, {
            as: eo.A.Link,
            ref: t,
            ...e
          })
        });
      Object.assign(el, {
        Item: ec,
        Link: (0, n.forwardRef)(({
          as: e,
          ...t
        }, r) => (0, d.jsx)(eu, {
          ...t,
          ...e ? {
            forwardedAs: e
          } : {},
          ref: r
        }))
      });
      var ed = r(46249);
      let eh = (0, o.Ay)(ed.A).withConfig({
        shouldForwardProp: e => "sx" !== e
      }).withConfig({
        displayName: "Heading",
        componentId: "sc-1vc165i-0"
      })(["", ""], C.sx);
      var ef = r(26108);
      let ep = (0, o.Ay)(ef.K).withConfig({
          shouldForwardProp: e => "sx" !== e
        }).withConfig({
          displayName: "IconButton__StyledIconButton",
          componentId: "sc-i53dt6-0"
        })(["", ""], C.sx),
        em = (0, n.forwardRef)(({
          as: e,
          sx: t,
          ...r
        }, i) => {
          let n = t,
            {
              size: s = "medium"
            } = r;
          return null != t && Object.keys(t).length > 0 && (n = J({
            size: s
          }, t)), (0, d.jsx)(ep, {
            sx: n,
            ...r,
            ...e ? {
              forwardedAs: e
            } : {},
            ref: i
          })
        });
      em.__SLOT__ = ef.K.__SLOT__;
      var eg = r(4925);
      let ey = (0, o.Ay)(eg.A).withConfig({
          shouldForwardProp: e => "sx" !== e
        }).withConfig({
          displayName: "Label__StyledLabel",
          componentId: "sc-1cpass9-0"
        })(["", ""], C.sx),
        eb = (0, n.forwardRef)(({
          as: e,
          ...t
        }, r) => (0, d.jsx)(ey, {
          ...t,
          ...e ? {
            forwardedAs: e
          } : {},
          ref: r
        }));
      var ev = r(83223);
      let ew = (0, o.Ay)(ev.A).withConfig({
          shouldForwardProp: e => "sx" !== e
        }).withConfig({
          displayName: "Link__StyledLink",
          componentId: "sc-1syctfj-0"
        })(["", ""], C.sx),
        eA = (0, n.forwardRef)(({
          as: e,
          ...t
        }, r) => (0, d.jsx)(ew, {
          ...t,
          ...e ? {
            forwardedAs: e
          } : {},
          ref: r
        }));
      var ex = r(73077);
      let eS = (0, o.Ay)(ex.z).withConfig({
        shouldForwardProp: e => "sx" !== e
      }).withConfig({
        displayName: "LinkButton",
        componentId: "sc-1v6zkmg-0"
      })(["", ""], C.sx);
      var eC = r(72889);
      (0, o.Ay)(eC.Ay).withConfig({
        shouldForwardProp: e => "sx" !== e
      }).withConfig({
        displayName: "Overlay",
        componentId: "sc-tjbd74-0"
      })(["", ""], C.sx);
      var e_ = r(65729),
        eO = r(89823);
      let ek = e => (0, d.jsx)(i.a, {
          as: eO.I.Button,
          ...e
        }),
        eT = e => (0, d.jsx)(i.a, {
          as: eO.I.IconButton,
          ...e
        });
      Object.assign(e => (0, d.jsx)(i.a, {
        as: eO.I,
        ...e
      }), {
        __SLOT__: eO.I.__SLOT__,
        Button: ek,
        IconButton: eT
      }), ek.__SLOT__ = eO.I.Button.__SLOT__, eT.__SLOT__ = eO.I.IconButton.__SLOT__;
      var ej = r(7478);
      let eL = (0, o.Ay)(ej.A).withConfig({
        shouldForwardProp: e => "sx" !== e
      }).withConfig({
        displayName: "Spinner",
        componentId: "sc-jbw2a0-0"
      })(["", ""], C.sx);
      var eE = r(36007);
      let eI = (0, o.Ay)(eE.A).withConfig({
          shouldForwardProp: e => "sx" !== e
        }).withConfig({
          displayName: "Text__StyledText",
          componentId: "sc-1klmep6-0"
        })(["", ""], C.sx),
        eF = (0, n.forwardRef)(({
          as: e,
          ...t
        }, r) => (0, d.jsx)(eI, {
          ...t,
          ...e ? {
            forwardedAs: e
          } : {},
          ref: r
        }));
      var eM = r(65820);
      let eP = (0, o.Ay)(eM.Ay).withConfig({
          shouldForwardProp: e => "sx" !== e
        }).withConfig({
          displayName: "Textarea__StyledTextarea",
          componentId: "sc-40d1gp-0"
        })(["", ""], C.sx),
        eR = (0, n.forwardRef)(({
          as: e,
          ...t
        }, r) => (0, d.jsx)(eP, {
          ...t,
          ...e ? {
            forwardedAs: e
          } : {},
          ref: r
        }));
      var ez = r(38750);
      let eN = (0, o.Ay)(ez.A).withConfig({
          shouldForwardProp: e => "sx" !== e
        }).withConfig({
          displayName: "TextInput__StyledTextInput",
          componentId: "sc-ttxlvl-0"
        })(["", ""], C.sx),
        eD = (0, n.forwardRef)(({
          as: e,
          ...t
        }, r) => (0, d.jsx)(eN, {
          ref: r,
          ...t,
          ...e ? {
            forwardedAs: e
          } : {}
        })),
        e$ = (0, o.Ay)(ez.A.Action).withConfig({
          shouldForwardProp: e => "sx" !== e
        }).withConfig({
          displayName: "TextInput__TextInputAction",
          componentId: "sc-ttxlvl-1"
        })(["", ""], C.sx),
        eB = Object.assign(eD, {
          __SLOT__: ez.A.__SLOT__,
          Action: e$
        });
      e$.displayName = "TextInputAction", eD.displayName = "TextInput";
      var eH = r(53716);
      let eW = Object.assign((0, n.forwardRef)(function(e, t) {
        return (0, d.jsx)(i.a, {
          as: eH.A,
          ref: t,
          ...e
        })
      }), {
        Item: (0, n.forwardRef)(function(e, t) {
          return (0, d.jsx)(i.a, {
            as: eH.A.Item,
            ref: t,
            ...e
          })
        }),
        Badge: function(e) {
          return (0, d.jsx)(i.a, {
            as: eH.A.Badge,
            ...e
          })
        },
        Body: (0, n.forwardRef)(function(e, t) {
          return (0, d.jsx)(i.a, {
            as: eH.A.Body,
            ref: t,
            ...e
          })
        }),
        Break: (0, n.forwardRef)(function(e, t) {
          return (0, d.jsx)(i.a, {
            as: eH.A.Break,
            ref: t,
            ...e
          })
        })
      });
      var eU = r(49716),
        eq = r(39656);
      let eV = (0, o.Ay)(eq.A).withConfig({
          shouldForwardProp: e => "sx" !== e
        }).withConfig({
          displayName: "Token__StyledToken",
          componentId: "sc-ldn0r8-0"
        })(["", ""], C.sx),
        eG = (0, n.forwardRef)(({
          as: e,
          ...t
        }, r) => (0, d.jsx)(eV, {
          ...t,
          ...e ? {
            forwardedAs: e
          } : {},
          ref: r
        }));
      var eK = r(39775);
      let eQ = (0, o.Ay)(eK.A).withConfig({
        shouldForwardProp: e => "sx" !== e
      }).withConfig({
        displayName: "Truncate",
        componentId: "sc-x3i4it-0"
      })(["", ""], C.sx);
      var eZ = r(1761);
      let eX = (0, n.forwardRef)(function(e, t) {
          return (0, d.jsx)(i.a, {
            as: eZ.O,
            ref: t,
            ...e
          })
        }),
        eY = (0, n.forwardRef)(({
          as: e,
          ...t
        }, r) => (0, d.jsx)(eX, {
          ...t,
          ...e ? {
            forwardedAs: e
          } : {},
          ref: r
        })),
        eJ = (0, o.Ay)(eZ.O.Item).withConfig({
          shouldForwardProp: e => "sx" !== e
        }).withConfig({
          displayName: "UnderlineNav__StyledUnderlineNavItem",
          componentId: "sc-dx6br2-0"
        })(["", ""], C.sx),
        e0 = Object.assign(eY, {
          Item: (0, n.forwardRef)(({
            as: e,
            ...t
          }, r) => (0, d.jsx)(eJ, {
            ...t,
            ...e ? {
              forwardedAs: e
            } : {},
            ref: r
          }))
        })
    },
    49539(e, t, r) {
      "use strict";
      r.d(t, {
        sx: () => n
      });
      var i = r(50402);
      r(14744);
      let n = e => (0, i.Ay)(e.sx)
    },
    29658(e, t, r) {
      "use strict";
      r.d(t, {
        m: () => s
      });
      var i = r(66500),
        n = r(24880),
        s = new class extends i.Q {
          #e;
          #t;
          #r;
          constructor() {
            super(), this.#r = e => {
              if (!n.S$ && window.addEventListener) {
                let t = () => e();
                return window.addEventListener("visibilitychange", t, !1), () => {
                  window.removeEventListener("visibilitychange", t)
                }
              }
            }
          }
          onSubscribe() {
            this.#t || this.setEventListener(this.#r)
          }
          onUnsubscribe() {
            this.hasListeners() || (this.#t?.(), this.#t = void 0)
          }
          setEventListener(e) {
            this.#r = e, this.#t?.(), this.#t = e(e => {
              "boolean" == typeof e ? this.setFocused(e) : this.onFocus()
            })
          }
          setFocused(e) {
            this.#e !== e && (this.#e = e, this.onFocus())
          }
          onFocus() {
            let e = this.isFocused();
            this.listeners.forEach(t => {
              t(e)
            })
          }
          isFocused() {
            return "boolean" == typeof this.#e ? this.#e : globalThis.document?.visibilityState !== "hidden"
          }
        }
    },
    26261(e, t, r) {
      "use strict";
      let i, n, s, o, a, l;
      r.d(t, {
        jG: () => u,
        x3: () => c
      });
      var c = r(52775).Zq,
        u = (i = [], n = 0, s = e => {
          e()
        }, o = e => {
          e()
        }, a = c, {
          batch: e => {
            let t;
            n++;
            try {
              t = e()
            } finally {
              let e;
              --n || (e = i, i = [], e.length && a(() => {
                o(() => {
                  e.forEach(e => {
                    s(e)
                  })
                })
              }))
            }
            return t
          },
          batchCalls: e => (...t) => {
            l(() => {
              e(...t)
            })
          },
          schedule: l = e => {
            n ? i.push(e) : a(() => {
              s(e)
            })
          },
          setNotifyFunction: e => {
            s = e
          },
          setBatchNotifyFunction: e => {
            o = e
          },
          setScheduler: e => {
            a = e
          }
        })
    },
    96035(e, t, r) {
      "use strict";
      r.d(t, {
        t: () => s
      });
      var i = r(66500),
        n = r(24880),
        s = new class extends i.Q {
          #i = !0;
          #t;
          #r;
          constructor() {
            super(), this.#r = e => {
              if (!n.S$ && window.addEventListener) {
                let t = () => e(!0),
                  r = () => e(!1);
                return window.addEventListener("online", t, !1), window.addEventListener("offline", r, !1), () => {
                  window.removeEventListener("online", t), window.removeEventListener("offline", r)
                }
              }
            }
          }
          onSubscribe() {
            this.#t || this.setEventListener(this.#r)
          }
          onUnsubscribe() {
            this.hasListeners() || (this.#t?.(), this.#t = void 0)
          }
          setEventListener(e) {
            this.#r = e, this.#t?.(), this.#t = e(this.setOnline.bind(this))
          }
          setOnline(e) {
            this.#i !== e && (this.#i = e, this.listeners.forEach(t => {
              t(e)
            }))
          }
          isOnline() {
            return this.#i
          }
        }
    },
    79757(e, t, r) {
      "use strict";
      r.d(t, {
        X: () => a,
        k: () => l
      });
      var i = r(24880),
        n = r(26261),
        s = r(58904),
        o = r(71692),
        a = class extends o.k {
          #n;
          #s;
          #o;
          #a;
          #l;
          #c;
          #u;
          constructor(e) {
            super(), this.#u = !1, this.#c = e.defaultOptions, this.setOptions(e.options), this.observers = [], this.#a = e.client, this.#o = this.#a.getQueryCache(), this.queryKey = e.queryKey, this.queryHash = e.queryHash, this.#n = u(this.options), this.state = e.state ?? this.#n, this.scheduleGc()
          }
          get meta() {
            return this.options.meta
          }
          get promise() {
            return this.#l?.promise
          }
          setOptions(e) {
            if (this.options = {
                ...this.#c,
                ...e
              }, this.updateGcTime(this.options.gcTime), this.state && void 0 === this.state.data) {
              let e = u(this.options);
              void 0 !== e.data && (this.setState(c(e.data, e.dataUpdatedAt)), this.#n = e)
            }
          }
          optionalRemove() {
            this.observers.length || "idle" !== this.state.fetchStatus || this.#o.remove(this)
          }
          setData(e, t) {
            let r = (0, i.pl)(this.state.data, e, this.options);
            return this.#d({
              data: r,
              type: "success",
              dataUpdatedAt: t?.updatedAt,
              manual: t?.manual
            }), r
          }
          setState(e, t) {
            this.#d({
              type: "setState",
              state: e,
              setStateOptions: t
            })
          }
          cancel(e) {
            let t = this.#l?.promise;
            return this.#l?.cancel(e), t ? t.then(i.lQ).catch(i.lQ) : Promise.resolve()
          }
          destroy() {
            super.destroy(), this.cancel({
              silent: !0
            })
          }
          reset() {
            this.destroy(), this.setState(this.#n)
          }
          isActive() {
            return this.observers.some(e => !1 !== (0, i.Eh)(e.options.enabled, this))
          }
          isDisabled() {
            return this.getObserversCount() > 0 ? !this.isActive() : this.options.queryFn === i.hT || this.state.dataUpdateCount + this.state.errorUpdateCount === 0
          }
          isStatic() {
            return this.getObserversCount() > 0 && this.observers.some(e => "static" === (0, i.d2)(e.options.staleTime, this))
          }
          isStale() {
            return this.getObserversCount() > 0 ? this.observers.some(e => e.getCurrentResult().isStale) : void 0 === this.state.data || this.state.isInvalidated
          }
          isStaleByTime(e = 0) {
            return void 0 === this.state.data || "static" !== e && (!!this.state.isInvalidated || !(0, i.j3)(this.state.dataUpdatedAt, e))
          }
          onFocus() {
            let e = this.observers.find(e => e.shouldFetchOnWindowFocus());
            e?.refetch({
              cancelRefetch: !1
            }), this.#l?.continue()
          }
          onOnline() {
            let e = this.observers.find(e => e.shouldFetchOnReconnect());
            e?.refetch({
              cancelRefetch: !1
            }), this.#l?.continue()
          }
          addObserver(e) {
            this.observers.includes(e) || (this.observers.push(e), this.clearGcTimeout(), this.#o.notify({
              type: "observerAdded",
              query: this,
              observer: e
            }))
          }
          removeObserver(e) {
            this.observers.includes(e) && (this.observers = this.observers.filter(t => t !== e), this.observers.length || (this.#l && (this.#u ? this.#l.cancel({
              revert: !0
            }) : this.#l.cancelRetry()), this.scheduleGc()), this.#o.notify({
              type: "observerRemoved",
              query: this,
              observer: e
            }))
          }
          getObserversCount() {
            return this.observers.length
          }
          invalidate() {
            this.state.isInvalidated || this.#d({
              type: "invalidate"
            })
          }
          async fetch(e, t) {
            let r;
            if ("idle" !== this.state.fetchStatus && this.#l?.status() !== "rejected") {
              if (void 0 !== this.state.data && t?.cancelRefetch) this.cancel({
                silent: !0
              });
              else if (this.#l) return this.#l.continueRetry(), this.#l.promise
            }
            if (e && this.setOptions(e), !this.options.queryFn) {
              let e = this.observers.find(e => e.options.queryFn);
              e && this.setOptions(e.options)
            }
            let n = new AbortController,
              o = e => {
                Object.defineProperty(e, "signal", {
                  enumerable: !0,
                  get: () => (this.#u = !0, n.signal)
                })
              },
              a = () => {
                let e, r = (0, i.ZM)(this.options, t),
                  n = (o(e = {
                    client: this.#a,
                    queryKey: this.queryKey,
                    meta: this.meta
                  }), e);
                return (this.#u = !1, this.options.persister) ? this.options.persister(r, n, this) : r(n)
              },
              l = (o(r = {
                fetchOptions: t,
                options: this.options,
                queryKey: this.queryKey,
                client: this.#a,
                state: this.state,
                fetchFn: a
              }), r);
            this.options.behavior?.onFetch(l, this), this.#s = this.state, ("idle" === this.state.fetchStatus || this.state.fetchMeta !== l.fetchOptions?.meta) && this.#d({
              type: "fetch",
              meta: l.fetchOptions?.meta
            }), this.#l = (0, s.II)({
              initialPromise: t?.initialPromise,
              fn: l.fetchFn,
              onCancel: e => {
                e instanceof s.cc && e.revert && this.setState({
                  ...this.#s,
                  fetchStatus: "idle"
                }), n.abort()
              },
              onFail: (e, t) => {
                this.#d({
                  type: "failed",
                  failureCount: e,
                  error: t
                })
              },
              onPause: () => {
                this.#d({
                  type: "pause"
                })
              },
              onContinue: () => {
                this.#d({
                  type: "continue"
                })
              },
              retry: l.options.retry,
              retryDelay: l.options.retryDelay,
              networkMode: l.options.networkMode,
              canRun: () => !0
            });
            try {
              let e = await this.#l.start();
              if (void 0 === e) throw Error(`${this.queryHash} data is undefined`);
              return this.setData(e), this.#o.config.onSuccess?.(e, this), this.#o.config.onSettled?.(e, this.state.error, this), e
            } catch (e) {
              if (e instanceof s.cc) {
                if (e.silent) return this.#l.promise;
                else if (e.revert) {
                  if (void 0 === this.state.data) throw e;
                  return this.state.data
                }
              }
              throw this.#d({
                type: "error",
                error: e
              }), this.#o.config.onError?.(e, this), this.#o.config.onSettled?.(this.state.data, e, this), e
            } finally {
              this.scheduleGc()
            }
          }
          #d(e) {
            let t = t => {
              switch (e.type) {
                case "failed":
                  return {
                    ...t, fetchFailureCount: e.failureCount, fetchFailureReason: e.error
                  };
                case "pause":
                  return {
                    ...t, fetchStatus: "paused"
                  };
                case "continue":
                  return {
                    ...t, fetchStatus: "fetching"
                  };
                case "fetch":
                  return {
                    ...t, ...l(t.data, this.options), fetchMeta: e.meta ?? null
                  };
                case "success":
                  let r = {
                    ...t,
                    ...c(e.data, e.dataUpdatedAt),
                    dataUpdateCount: t.dataUpdateCount + 1,
                    ...!e.manual && {
                      fetchStatus: "idle",
                      fetchFailureCount: 0,
                      fetchFailureReason: null
                    }
                  };
                  return this.#s = e.manual ? r : void 0, r;
                case "error":
                  let i = e.error;
                  return {
                    ...t, error: i, errorUpdateCount: t.errorUpdateCount + 1, errorUpdatedAt: Date.now(), fetchFailureCount: t.fetchFailureCount + 1, fetchFailureReason: i, fetchStatus: "idle", status: "error", isInvalidated: !0
                  };
                case "invalidate":
                  return {
                    ...t, isInvalidated: !0
                  };
                case "setState":
                  return {
                    ...t, ...e.state
                  }
              }
            };
            this.state = t(this.state), n.jG.batch(() => {
              this.observers.forEach(e => {
                e.onQueryUpdate()
              }), this.#o.notify({
                query: this,
                type: "updated",
                action: e
              })
            })
          }
        };

      function l(e, t) {
        return {
          fetchFailureCount: 0,
          fetchFailureReason: null,
          fetchStatus: (0, s.v_)(t.networkMode) ? "fetching" : "paused",
          ...void 0 === e && {
            error: null,
            status: "pending"
          }
        }
      }

      function c(e, t) {
        return {
          data: e,
          dataUpdatedAt: t ?? Date.now(),
          error: null,
          isInvalidated: !1,
          status: "success"
        }
      }

      function u(e) {
        let t = "function" == typeof e.initialData ? e.initialData() : e.initialData,
          r = void 0 !== t,
          i = r ? "function" == typeof e.initialDataUpdatedAt ? e.initialDataUpdatedAt() : e.initialDataUpdatedAt : 0;
        return {
          data: t,
          dataUpdateCount: 0,
          dataUpdatedAt: r ? i ?? Date.now() : 0,
          error: null,
          errorUpdateCount: 0,
          errorUpdatedAt: 0,
          fetchFailureCount: 0,
          fetchFailureReason: null,
          fetchMeta: null,
          isInvalidated: !1,
          status: r ? "success" : "pending",
          fetchStatus: "idle"
        }
      }
    },
    71692(e, t, r) {
      "use strict";
      r.d(t, {
        k: () => s
      });
      var i = r(52775),
        n = r(24880),
        s = class {
          #h;
          destroy() {
            this.clearGcTimeout()
          }
          scheduleGc() {
            this.clearGcTimeout(), (0, n.gn)(this.gcTime) && (this.#h = i.zs.setTimeout(() => {
              this.optionalRemove()
            }, this.gcTime))
          }
          updateGcTime(e) {
            this.gcTime = Math.max(this.gcTime || 0, e ?? (n.S$ ? 1 / 0 : 3e5))
          }
          clearGcTimeout() {
            this.#h && (i.zs.clearTimeout(this.#h), this.#h = void 0)
          }
        }
    },
    58904(e, t, r) {
      "use strict";
      r.d(t, {
        II: () => d,
        cc: () => c,
        v_: () => l,
        wm: () => u
      });
      var i = r(29658),
        n = r(96035),
        s = r(94658),
        o = r(24880);

      function a(e) {
        return Math.min(1e3 * 2 ** e, 3e4)
      }

      function l(e) {
        return (e ?? "online") !== "online" || n.t.isOnline()
      }
      var c = class extends Error {
        constructor(e) {
          super("CancelledError"), this.revert = e?.revert, this.silent = e?.silent
        }
      };

      function u(e) {
        return e instanceof c
      }

      function d(e) {
        let t, r = !1,
          u = 0,
          d = (0, s.T)(),
          h = () => i.m.isFocused() && ("always" === e.networkMode || n.t.isOnline()) && e.canRun(),
          f = () => l(e.networkMode) && e.canRun(),
          p = e => {
            "pending" === d.status && (t?.(), d.resolve(e))
          },
          m = e => {
            "pending" === d.status && (t?.(), d.reject(e))
          },
          g = () => new Promise(r => {
            t = e => {
              ("pending" !== d.status || h()) && r(e)
            }, e.onPause?.()
          }).then(() => {
            t = void 0, "pending" === d.status && e.onContinue?.()
          }),
          y = () => {
            let t;
            if ("pending" !== d.status) return;
            let i = 0 === u ? e.initialPromise : void 0;
            try {
              t = i ?? e.fn()
            } catch (e) {
              t = Promise.reject(e)
            }
            Promise.resolve(t).then(p).catch(t => {
              if ("pending" !== d.status) return;
              let i = e.retry ?? 3 * !o.S$,
                n = e.retryDelay ?? a,
                s = "function" == typeof n ? n(u, t) : n,
                l = !0 === i || "number" == typeof i && u < i || "function" == typeof i && i(u, t);
              r || !l ? m(t) : (u++, e.onFail?.(u, t), (0, o.yy)(s).then(() => h() ? void 0 : g()).then(() => {
                r ? m(t) : y()
              }))
            })
          };
        return {
          promise: d,
          status: () => d.status,
          cancel: t => {
            if ("pending" === d.status) {
              let r = new c(t);
              m(r), e.onCancel?.(r)
            }
          },
          continue: () => (t?.(), d),
          cancelRetry: () => {
            r = !0
          },
          continueRetry: () => {
            r = !1
          },
          canStart: f,
          start: () => (f() ? y() : g().then(y), d)
        }
      }
    },
    66500(e, t, r) {
      "use strict";
      r.d(t, {
        Q: () => i
      });
      var i = class {
        constructor() {
          this.listeners = new Set, this.subscribe = this.subscribe.bind(this)
        }
        subscribe(e) {
          return this.listeners.add(e), this.onSubscribe(), () => {
            this.listeners.delete(e), this.onUnsubscribe()
          }
        }
        hasListeners() {
          return this.listeners.size > 0
        }
        onSubscribe() {}
        onUnsubscribe() {}
      }
    },
    94658(e, t, r) {
      "use strict";
      r.d(t, {
        T: () => n,
        b: () => s
      });
      var i = r(24880);

      function n() {
        let e, t, r = new Promise((r, i) => {
          e = r, t = i
        });

        function i(e) {
          Object.assign(r, e), delete r.resolve, delete r.reject
        }
        return r.status = "pending", r.catch(() => {}), r.resolve = t => {
          i({
            status: "fulfilled",
            value: t
          }), e(t)
        }, r.reject = e => {
          i({
            status: "rejected",
            reason: e
          }), t(e)
        }, r
      }

      function s(e) {
        let t;
        if (e.then(e => (t = e, e), i.lQ)?.catch(i.lQ), void 0 !== t) return {
          data: t
        }
      }
    },
    52775(e, t, r) {
      "use strict";
      r.d(t, {
        Zq: () => s,
        zs: () => n
      });
      var i = {
          setTimeout: (e, t) => setTimeout(e, t),
          clearTimeout: e => clearTimeout(e),
          setInterval: (e, t) => setInterval(e, t),
          clearInterval: e => clearInterval(e)
        },
        n = new class {
          #f = i;
          #p = !1;
          setTimeoutProvider(e) {
            this.#f = e
          }
          setTimeout(e, t) {
            return this.#f.setTimeout(e, t)
          }
          clearTimeout(e) {
            this.#f.clearTimeout(e)
          }
          setInterval(e, t) {
            return this.#f.setInterval(e, t)
          }
          clearInterval(e) {
            this.#f.clearInterval(e)
          }
        };

      function s(e) {
        setTimeout(e, 0)
      }
    },
    24880(e, t, r) {
      "use strict";
      r.d(t, {
        BH: () => y,
        Cp: () => m,
        EN: () => p,
        Eh: () => u,
        F$: () => f,
        GU: () => j,
        MK: () => d,
        S$: () => n,
        ZM: () => T,
        ZZ: () => O,
        Zw: () => o,
        d2: () => c,
        f8: () => b,
        gn: () => a,
        hT: () => k,
        j3: () => l,
        lQ: () => s,
        nJ: () => h,
        ox: () => L,
        pl: () => S,
        rX: () => C,
        y9: () => _,
        yy: () => x
      });
      var i = r(52775),
        n = "u" < typeof window || "Deno" in globalThis;

      function s() {}

      function o(e, t) {
        return "function" == typeof e ? e(t) : e
      }

      function a(e) {
        return "number" == typeof e && e >= 0 && e !== 1 / 0
      }

      function l(e, t) {
        return Math.max(e + (t || 0) - Date.now(), 0)
      }

      function c(e, t) {
        return "function" == typeof e ? e(t) : e
      }

      function u(e, t) {
        return "function" == typeof e ? e(t) : e
      }

      function d(e, t) {
        let {
          type: r = "all",
          exact: i,
          fetchStatus: n,
          predicate: s,
          queryKey: o,
          stale: a
        } = e;
        if (o) {
          if (i) {
            if (t.queryHash !== f(o, t.options)) return !1
          } else if (!m(t.queryKey, o)) return !1
        }
        if ("all" !== r) {
          let e = t.isActive();
          if ("active" === r && !e || "inactive" === r && e) return !1
        }
        return ("boolean" != typeof a || t.isStale() === a) && (!n || n === t.state.fetchStatus) && (!s || !!s(t))
      }

      function h(e, t) {
        let {
          exact: r,
          status: i,
          predicate: n,
          mutationKey: s
        } = e;
        if (s) {
          if (!t.options.mutationKey) return !1;
          if (r) {
            if (p(t.options.mutationKey) !== p(s)) return !1
          } else if (!m(t.options.mutationKey, s)) return !1
        }
        return (!i || t.state.status === i) && (!n || !!n(t))
      }

      function f(e, t) {
        return (t?.queryKeyHashFn || p)(e)
      }

      function p(e) {
        return JSON.stringify(e, (e, t) => w(t) ? Object.keys(t).sort().reduce((e, r) => (e[r] = t[r], e), {}) : t)
      }

      function m(e, t) {
        return e === t || typeof e == typeof t && !!e && !!t && "object" == typeof e && "object" == typeof t && Object.keys(t).every(r => m(e[r], t[r]))
      }
      var g = Object.prototype.hasOwnProperty;

      function y(e, t) {
        if (e === t) return e;
        let r = v(e) && v(t);
        if (!r && !(w(e) && w(t))) return t;
        let i = (r ? e : Object.keys(e)).length,
          n = r ? t : Object.keys(t),
          s = n.length,
          o = r ? Array(s) : {},
          a = 0;
        for (let l = 0; l < s; l++) {
          let s = r ? l : n[l],
            c = e[s],
            u = t[s];
          if (c === u) {
            o[s] = c, (r ? l < i : g.call(e, s)) && a++;
            continue
          }
          if (null === c || null === u || "object" != typeof c || "object" != typeof u) {
            o[s] = u;
            continue
          }
          let d = y(c, u);
          o[s] = d, d === c && a++
        }
        return i === s && a === i ? e : o
      }

      function b(e, t) {
        if (!t || Object.keys(e).length !== Object.keys(t).length) return !1;
        for (let r in e)
          if (e[r] !== t[r]) return !1;
        return !0
      }

      function v(e) {
        return Array.isArray(e) && e.length === Object.keys(e).length
      }

      function w(e) {
        if (!A(e)) return !1;
        let t = e.constructor;
        if (void 0 === t) return !0;
        let r = t.prototype;
        return !!A(r) && !!r.hasOwnProperty("isPrototypeOf") && Object.getPrototypeOf(e) === Object.prototype
      }

      function A(e) {
        return "[object Object]" === Object.prototype.toString.call(e)
      }

      function x(e) {
        return new Promise(t => {
          i.zs.setTimeout(t, e)
        })
      }

      function S(e, t, r) {
        return "function" == typeof r.structuralSharing ? r.structuralSharing(e, t) : !1 !== r.structuralSharing ? y(e, t) : t
      }

      function C(e) {
        return e
      }

      function _(e, t, r = 0) {
        let i = [...e, t];
        return r && i.length > r ? i.slice(1) : i
      }

      function O(e, t, r = 0) {
        let i = [t, ...e];
        return r && i.length > r ? i.slice(0, -1) : i
      }
      var k = Symbol();

      function T(e, t) {
        return !e.queryFn && t?.initialPromise ? () => t.initialPromise : e.queryFn && e.queryFn !== k ? e.queryFn : () => Promise.reject(Error(`Missing queryFn: '${e.queryHash}'`))
      }

      function j(e, t) {
        return "function" == typeof e ? e(...t) : !!e
      }

      function L(e, t, r) {
        let i, n = !1;
        return Object.defineProperty(e, "signal", {
          enumerable: !0,
          get: () => (i ??= t(), n || (n = !0, i.aborted ? r() : i.addEventListener("abort", r, {
            once: !0
          })), i)
        }), e
      }
    },
    51220(e, t, r) {
      "use strict";
      r.d(t, {
        Te: () => l,
        XW: () => c
      });
      var i = r(96540),
        n = r(40961),
        s = r(36895);
      let o = "u" > typeof document ? i.useLayoutEffect : i.useEffect;

      function a({
        useFlushSync: e = !0,
        ...t
      }) {
        let r = i.useReducer(() => ({}), {})[1],
          l = {
            ...t,
            onChange: (i, s) => {
              var o;
              e && s ? (0, n.flushSync)(r) : r(), null == (o = t.onChange) || o.call(t, i, s)
            }
          },
          [c] = i.useState(() => new s.YV(l));
        return c.setOptions(l), o(() => c._didMount(), []), o(() => c._willUpdate()), c
      }

      function l(e) {
        return a({
          observeElementRect: s.T6,
          observeElementOffset: s.AO,
          scrollToFn: s.Ox,
          ...e
        })
      }

      function c(e) {
        return a({
          getScrollElement: () => "u" > typeof document ? window : null,
          observeElementRect: s.TH,
          observeElementOffset: s.MH,
          scrollToFn: s.e8,
          initialOffset: () => "u" > typeof document ? window.scrollY : 0,
          ...e
        })
      }
    },
    36895(e, t, r) {
      "use strict";

      function i(e, t, r) {
        let i, n = r.initialDeps ?? [],
          s = !0;

        function o() {
          var o, a, l;
          let c, u;
          r.key && (null == (o = r.debug) ? void 0 : o.call(r)) && (c = Date.now());
          let d = e();
          if (!(d.length !== n.length || d.some((e, t) => n[t] !== e))) return i;
          if (n = d, r.key && (null == (a = r.debug) ? void 0 : a.call(r)) && (u = Date.now()), i = t(...d), r.key && (null == (l = r.debug) ? void 0 : l.call(r))) {
            let e = Math.round((Date.now() - c) * 100) / 100,
              t = Math.round((Date.now() - u) * 100) / 100,
              i = t / 16,
              n = (e, t) => {
                for (e = String(e); e.length < t;) e = " " + e;
                return e
              };
            console.info(`%c\u{23F1} ${n(t,5)} /${n(e,5)} ms`, `
            font-size: .6rem;
            font-weight: bold;
            color: hsl(${Math.max(0,Math.min(120-120*i,120))}deg 100% 31%);`, null == r ? void 0 : r.key)
          }
          return (null == r ? void 0 : r.onChange) && !(s && r.skipInitialOnChange) && r.onChange(i), s = !1, i
        }
        return o.updateDeps = e => {
          n = e
        }, o
      }

      function n(e, t) {
        if (void 0 !== e) return e;
        throw Error(`Unexpected undefined${t?`: ${t}`:""}`)
      }
      r.d(t, {
        T6: () => c,
        vp: () => l,
        e8: () => g,
        AO: () => f,
        Ox: () => y,
        TH: () => d,
        YV: () => b,
        MH: () => p
      });
      let s = (e, t, r) => {
          let i;
          return function(...n) {
            e.clearTimeout(i), i = e.setTimeout(() => t.apply(this, n), r)
          }
        },
        o = e => {
          let {
            offsetWidth: t,
            offsetHeight: r
          } = e;
          return {
            width: t,
            height: r
          }
        },
        a = e => e,
        l = e => {
          let t = Math.max(e.startIndex - e.overscan, 0),
            r = Math.min(e.endIndex + e.overscan, e.count - 1),
            i = [];
          for (let e = t; e <= r; e++) i.push(e);
          return i
        },
        c = (e, t) => {
          let r = e.scrollElement;
          if (!r) return;
          let i = e.targetWindow;
          if (!i) return;
          let n = e => {
            let {
              width: r,
              height: i
            } = e;
            t({
              width: Math.round(r),
              height: Math.round(i)
            })
          };
          if (n(o(r)), !i.ResizeObserver) return () => {};
          let s = new i.ResizeObserver(t => {
            let i = () => {
              let e = t[0];
              if (null == e ? void 0 : e.borderBoxSize) {
                let t = e.borderBoxSize[0];
                if (t) return void n({
                  width: t.inlineSize,
                  height: t.blockSize
                })
              }
              n(o(r))
            };
            e.options.useAnimationFrameWithResizeObserver ? requestAnimationFrame(i) : i()
          });
          return s.observe(r, {
            box: "border-box"
          }), () => {
            s.unobserve(r)
          }
        },
        u = {
          passive: !0
        },
        d = (e, t) => {
          let r = e.scrollElement;
          if (!r) return;
          let i = () => {
            t({
              width: r.innerWidth,
              height: r.innerHeight
            })
          };
          return i(), r.addEventListener("resize", i, u), () => {
            r.removeEventListener("resize", i)
          }
        },
        h = "u" < typeof window || "onscrollend" in window,
        f = (e, t) => {
          let r = e.scrollElement;
          if (!r) return;
          let i = e.targetWindow;
          if (!i) return;
          let n = 0,
            o = e.options.useScrollendEvent && h ? () => void 0 : s(i, () => {
              t(n, !1)
            }, e.options.isScrollingResetDelay),
            a = i => () => {
              let {
                horizontal: s,
                isRtl: a
              } = e.options;
              n = s ? r.scrollLeft * (a && -1 || 1) : r.scrollTop, o(), t(n, i)
            },
            l = a(!0),
            c = a(!1);
          r.addEventListener("scroll", l, u);
          let d = e.options.useScrollendEvent && h;
          return d && r.addEventListener("scrollend", c, u), () => {
            r.removeEventListener("scroll", l), d && r.removeEventListener("scrollend", c)
          }
        },
        p = (e, t) => {
          let r = e.scrollElement;
          if (!r) return;
          let i = e.targetWindow;
          if (!i) return;
          let n = 0,
            o = e.options.useScrollendEvent && h ? () => void 0 : s(i, () => {
              t(n, !1)
            }, e.options.isScrollingResetDelay),
            a = i => () => {
              n = r[e.options.horizontal ? "scrollX" : "scrollY"], o(), t(n, i)
            },
            l = a(!0),
            c = a(!1);
          r.addEventListener("scroll", l, u);
          let d = e.options.useScrollendEvent && h;
          return d && r.addEventListener("scrollend", c, u), () => {
            r.removeEventListener("scroll", l), d && r.removeEventListener("scrollend", c)
          }
        },
        m = (e, t, r) => {
          if (null == t ? void 0 : t.borderBoxSize) {
            let e = t.borderBoxSize[0];
            if (e) return Math.round(e[r.options.horizontal ? "inlineSize" : "blockSize"])
          }
          return e[r.options.horizontal ? "offsetWidth" : "offsetHeight"]
        },
        g = (e, {
          adjustments: t = 0,
          behavior: r
        }, i) => {
          var n, s;
          null == (s = null == (n = i.scrollElement) ? void 0 : n.scrollTo) || s.call(n, {
            [i.options.horizontal ? "left" : "top"]: e + t,
            behavior: r
          })
        },
        y = (e, {
          adjustments: t = 0,
          behavior: r
        }, i) => {
          var n, s;
          null == (s = null == (n = i.scrollElement) ? void 0 : n.scrollTo) || s.call(n, {
            [i.options.horizontal ? "left" : "top"]: e + t,
            behavior: r
          })
        };
      class b {
        constructor(e) {
          this.unsubs = [], this.scrollElement = null, this.targetWindow = null, this.isScrolling = !1, this.currentScrollToIndex = null, this.measurementsCache = [], this.itemSizeCache = new Map, this.laneAssignments = new Map, this.pendingMeasuredCacheIndexes = [], this.prevLanes = void 0, this.lanesChangedFlag = !1, this.lanesSettling = !1, this.scrollRect = null, this.scrollOffset = null, this.scrollDirection = null, this.scrollAdjustments = 0, this.elementsCache = new Map, this.observer = (() => {
            let e = null,
              t = () => e || (this.targetWindow && this.targetWindow.ResizeObserver ? e = new this.targetWindow.ResizeObserver(e => {
                e.forEach(e => {
                  let t = () => {
                    this._measureElement(e.target, e)
                  };
                  this.options.useAnimationFrameWithResizeObserver ? requestAnimationFrame(t) : t()
                })
              }) : null);
            return {
              disconnect: () => {
                var r;
                null == (r = t()) || r.disconnect(), e = null
              },
              observe: e => {
                var r;
                return null == (r = t()) ? void 0 : r.observe(e, {
                  box: "border-box"
                })
              },
              unobserve: e => {
                var r;
                return null == (r = t()) ? void 0 : r.unobserve(e)
              }
            }
          })(), this.range = null, this.setOptions = e => {
            Object.entries(e).forEach(([t, r]) => {
              void 0 === r && delete e[t]
            }), this.options = {
              debug: !1,
              initialOffset: 0,
              overscan: 1,
              paddingStart: 0,
              paddingEnd: 0,
              scrollPaddingStart: 0,
              scrollPaddingEnd: 0,
              horizontal: !1,
              getItemKey: a,
              rangeExtractor: l,
              onChange: () => {},
              measureElement: m,
              initialRect: {
                width: 0,
                height: 0
              },
              scrollMargin: 0,
              gap: 0,
              indexAttribute: "data-index",
              initialMeasurementsCache: [],
              lanes: 1,
              isScrollingResetDelay: 150,
              enabled: !0,
              isRtl: !1,
              useScrollendEvent: !1,
              useAnimationFrameWithResizeObserver: !1,
              ...e
            }
          }, this.notify = e => {
            var t, r;
            null == (r = (t = this.options).onChange) || r.call(t, this, e)
          }, this.maybeNotify = i(() => (this.calculateRange(), [this.isScrolling, this.range ? this.range.startIndex : null, this.range ? this.range.endIndex : null]), e => {
            this.notify(e)
          }, {
            key: !1,
            debug: () => this.options.debug,
            initialDeps: [this.isScrolling, this.range ? this.range.startIndex : null, this.range ? this.range.endIndex : null]
          }), this.cleanup = () => {
            this.unsubs.filter(Boolean).forEach(e => e()), this.unsubs = [], this.observer.disconnect(), this.scrollElement = null, this.targetWindow = null
          }, this._didMount = () => () => {
            this.cleanup()
          }, this._willUpdate = () => {
            var e;
            let t = this.options.enabled ? this.options.getScrollElement() : null;
            if (this.scrollElement !== t) {
              if (this.cleanup(), !t) return void this.maybeNotify();
              this.scrollElement = t, this.scrollElement && "ownerDocument" in this.scrollElement ? this.targetWindow = this.scrollElement.ownerDocument.defaultView : this.targetWindow = (null == (e = this.scrollElement) ? void 0 : e.window) ?? null, this.elementsCache.forEach(e => {
                this.observer.observe(e)
              }), this.unsubs.push(this.options.observeElementRect(this, e => {
                this.scrollRect = e, this.maybeNotify()
              })), this.unsubs.push(this.options.observeElementOffset(this, (e, t) => {
                this.scrollAdjustments = 0, this.scrollDirection = t ? this.getScrollOffset() < e ? "forward" : "backward" : null, this.scrollOffset = e, this.isScrolling = t, this.maybeNotify()
              })), this._scrollToOffset(this.getScrollOffset(), {
                adjustments: void 0,
                behavior: void 0
              })
            }
          }, this.getSize = () => this.options.enabled ? (this.scrollRect = this.scrollRect ?? this.options.initialRect, this.scrollRect[this.options.horizontal ? "width" : "height"]) : (this.scrollRect = null, 0), this.getScrollOffset = () => this.options.enabled ? (this.scrollOffset = this.scrollOffset ?? ("function" == typeof this.options.initialOffset ? this.options.initialOffset() : this.options.initialOffset), this.scrollOffset) : (this.scrollOffset = null, 0), this.getFurthestMeasurement = (e, t) => {
            let r = new Map,
              i = new Map;
            for (let n = t - 1; n >= 0; n--) {
              let t = e[n];
              if (r.has(t.lane)) continue;
              let s = i.get(t.lane);
              if (null == s || t.end > s.end ? i.set(t.lane, t) : t.end < s.end && r.set(t.lane, !0), r.size === this.options.lanes) break
            }
            return i.size === this.options.lanes ? Array.from(i.values()).sort((e, t) => e.end === t.end ? e.index - t.index : e.end - t.end)[0] : void 0
          }, this.getMeasurementOptions = i(() => [this.options.count, this.options.paddingStart, this.options.scrollMargin, this.options.getItemKey, this.options.enabled, this.options.lanes], (e, t, r, i, n, s) => (void 0 !== this.prevLanes && this.prevLanes !== s && (this.lanesChangedFlag = !0), this.prevLanes = s, this.pendingMeasuredCacheIndexes = [], {
            count: e,
            paddingStart: t,
            scrollMargin: r,
            getItemKey: i,
            enabled: n,
            lanes: s
          }), {
            key: !1
          }), this.getMeasurements = i(() => [this.getMeasurementOptions(), this.itemSizeCache], ({
            count: e,
            paddingStart: t,
            scrollMargin: r,
            getItemKey: i,
            enabled: n,
            lanes: s
          }, o) => {
            if (!n) return this.measurementsCache = [], this.itemSizeCache.clear(), this.laneAssignments.clear(), [];
            if (this.laneAssignments.size > e)
              for (let t of this.laneAssignments.keys()) t >= e && this.laneAssignments.delete(t);
            this.lanesChangedFlag && (this.lanesChangedFlag = !1, this.lanesSettling = !0, this.measurementsCache = [], this.itemSizeCache.clear(), this.laneAssignments.clear(), this.pendingMeasuredCacheIndexes = []), 0 !== this.measurementsCache.length || this.lanesSettling || (this.measurementsCache = this.options.initialMeasurementsCache, this.measurementsCache.forEach(e => {
              this.itemSizeCache.set(e.key, e.size)
            }));
            let a = this.lanesSettling ? 0 : this.pendingMeasuredCacheIndexes.length > 0 ? Math.min(...this.pendingMeasuredCacheIndexes) : 0;
            this.pendingMeasuredCacheIndexes = [], this.lanesSettling && this.measurementsCache.length === e && (this.lanesSettling = !1);
            let l = this.measurementsCache.slice(0, a),
              c = Array(s).fill(void 0);
            for (let e = 0; e < a; e++) {
              let t = l[e];
              t && (c[t.lane] = e)
            }
            for (let n = a; n < e; n++) {
              let e, s, a = i(n),
                u = this.laneAssignments.get(n);
              if (void 0 !== u && this.options.lanes > 1) {
                let i = c[e = u],
                  n = void 0 !== i ? l[i] : void 0;
                s = n ? n.end + this.options.gap : t + r
              } else {
                let i = 1 === this.options.lanes ? l[n - 1] : this.getFurthestMeasurement(l, n);
                s = i ? i.end + this.options.gap : t + r, e = i ? i.lane : n % this.options.lanes, this.options.lanes > 1 && this.laneAssignments.set(n, e)
              }
              let d = o.get(a),
                h = "number" == typeof d ? d : this.options.estimateSize(n),
                f = s + h;
              l[n] = {
                index: n,
                start: s,
                size: h,
                end: f,
                key: a,
                lane: e
              }, c[e] = n
            }
            return this.measurementsCache = l, l
          }, {
            key: !1,
            debug: () => this.options.debug
          }), this.calculateRange = i(() => [this.getMeasurements(), this.getSize(), this.getScrollOffset(), this.options.lanes], (e, t, r, i) => this.range = e.length > 0 && t > 0 ? function({
            measurements: e,
            outerSize: t,
            scrollOffset: r,
            lanes: i
          }) {
            let n = e.length - 1;
            if (e.length <= i) return {
              startIndex: 0,
              endIndex: n
            };
            let s = v(0, n, t => e[t].start, r),
              o = s;
            if (1 === i)
              for (; o < n && e[o].end < r + t;) o++;
            else if (i > 1) {
              let a = Array(i).fill(0);
              for (; o < n && a.some(e => e < r + t);) {
                let t = e[o];
                a[t.lane] = t.end, o++
              }
              let l = Array(i).fill(r + t);
              for (; s >= 0 && l.some(e => e >= r);) {
                let t = e[s];
                l[t.lane] = t.start, s--
              }
              s = Math.max(0, s - s % i), o = Math.min(n, o + (i - 1 - o % i))
            }
            return {
              startIndex: s,
              endIndex: o
            }
          }({
            measurements: e,
            outerSize: t,
            scrollOffset: r,
            lanes: i
          }) : null, {
            key: !1,
            debug: () => this.options.debug
          }), this.getVirtualIndexes = i(() => {
            let e = null,
              t = null,
              r = this.calculateRange();
            return r && (e = r.startIndex, t = r.endIndex), this.maybeNotify.updateDeps([this.isScrolling, e, t]), [this.options.rangeExtractor, this.options.overscan, this.options.count, e, t]
          }, (e, t, r, i, n) => null === i || null === n ? [] : e({
            startIndex: i,
            endIndex: n,
            overscan: t,
            count: r
          }), {
            key: !1,
            debug: () => this.options.debug
          }), this.indexFromElement = e => {
            let t = this.options.indexAttribute,
              r = e.getAttribute(t);
            return r ? parseInt(r, 10) : (console.warn(`Missing attribute name '${t}={index}' on measured element.`), -1)
          }, this._measureElement = (e, t) => {
            let r = this.indexFromElement(e),
              i = this.measurementsCache[r];
            if (!i) return;
            let n = i.key,
              s = this.elementsCache.get(n);
            s !== e && (s && this.observer.unobserve(s), this.observer.observe(e), this.elementsCache.set(n, e)), e.isConnected && this.resizeItem(r, this.options.measureElement(e, t, this))
          }, this.resizeItem = (e, t) => {
            let r = this.measurementsCache[e];
            if (!r) return;
            let i = t - (this.itemSizeCache.get(r.key) ?? r.size);
            0 !== i && ((void 0 !== this.shouldAdjustScrollPositionOnItemSizeChange ? this.shouldAdjustScrollPositionOnItemSizeChange(r, i, this) : r.start < this.getScrollOffset() + this.scrollAdjustments) && this._scrollToOffset(this.getScrollOffset(), {
              adjustments: this.scrollAdjustments += i,
              behavior: void 0
            }), this.pendingMeasuredCacheIndexes.push(r.index), this.itemSizeCache = new Map(this.itemSizeCache.set(r.key, t)), this.notify(!1))
          }, this.measureElement = e => {
            e ? this._measureElement(e, void 0) : this.elementsCache.forEach((e, t) => {
              e.isConnected || (this.observer.unobserve(e), this.elementsCache.delete(t))
            })
          }, this.getVirtualItems = i(() => [this.getVirtualIndexes(), this.getMeasurements()], (e, t) => {
            let r = [];
            for (let i = 0, n = e.length; i < n; i++) {
              let n = t[e[i]];
              r.push(n)
            }
            return r
          }, {
            key: !1,
            debug: () => this.options.debug
          }), this.getVirtualItemForOffset = e => {
            let t = this.getMeasurements();
            if (0 !== t.length) return n(t[v(0, t.length - 1, e => n(t[e]).start, e)])
          }, this.getMaxScrollOffset = () => {
            if (!this.scrollElement) return 0;
            if ("scrollHeight" in this.scrollElement) return this.options.horizontal ? this.scrollElement.scrollWidth - this.scrollElement.clientWidth : this.scrollElement.scrollHeight - this.scrollElement.clientHeight;
            {
              let e = this.scrollElement.document.documentElement;
              return this.options.horizontal ? e.scrollWidth - this.scrollElement.innerWidth : e.scrollHeight - this.scrollElement.innerHeight
            }
          }, this.getOffsetForAlignment = (e, t, r = 0) => {
            if (!this.scrollElement) return 0;
            let i = this.getSize(),
              n = this.getScrollOffset();
            return "auto" === t && (t = e >= n + i ? "end" : "start"), "center" === t ? e += (r - i) / 2 : "end" === t && (e -= i), Math.max(Math.min(this.getMaxScrollOffset(), e), 0)
          }, this.getOffsetForIndex = (e, t = "auto") => {
            e = Math.max(0, Math.min(e, this.options.count - 1));
            let r = this.measurementsCache[e];
            if (!r) return;
            let i = this.getSize(),
              n = this.getScrollOffset();
            if ("auto" === t)
              if (r.end >= n + i - this.options.scrollPaddingEnd) t = "end";
              else {
                if (!(r.start <= n + this.options.scrollPaddingStart)) return [n, t];
                t = "start"
              } if ("end" === t && e === this.options.count - 1) return [this.getMaxScrollOffset(), t];
            let s = "end" === t ? r.end + this.options.scrollPaddingEnd : r.start - this.options.scrollPaddingStart;
            return [this.getOffsetForAlignment(s, t, r.size), t]
          }, this.isDynamicMode = () => this.elementsCache.size > 0, this.scrollToOffset = (e, {
            align: t = "start",
            behavior: r
          } = {}) => {
            "smooth" === r && this.isDynamicMode() && console.warn("The `smooth` scroll behavior is not fully supported with dynamic size."), this._scrollToOffset(this.getOffsetForAlignment(e, t), {
              adjustments: void 0,
              behavior: r
            })
          }, this.scrollToIndex = (e, {
            align: t = "auto",
            behavior: r
          } = {}) => {
            "smooth" === r && this.isDynamicMode() && console.warn("The `smooth` scroll behavior is not fully supported with dynamic size."), e = Math.max(0, Math.min(e, this.options.count - 1)), this.currentScrollToIndex = e;
            let i = 0,
              n = t => {
                if (!this.targetWindow) return;
                let i = this.getOffsetForIndex(e, t);
                if (!i) return void console.warn("Failed to get offset for index:", e);
                let [n, o] = i;
                this._scrollToOffset(n, {
                  adjustments: void 0,
                  behavior: r
                }), this.targetWindow.requestAnimationFrame(() => {
                  let t = () => {
                    if (this.currentScrollToIndex !== e) return;
                    let t = this.getScrollOffset(),
                      r = this.getOffsetForIndex(e, o);
                    r ? 1.01 > Math.abs(r[0] - t) || s(o) : console.warn("Failed to get offset for index:", e)
                  };
                  this.isDynamicMode() ? this.targetWindow.requestAnimationFrame(t) : t()
                })
              },
              s = t => {
                this.targetWindow && this.currentScrollToIndex === e && (++i < 10 ? this.targetWindow.requestAnimationFrame(() => n(t)) : console.warn(`Failed to scroll to index ${e} after 10 attempts.`))
              };
            n(t)
          }, this.scrollBy = (e, {
            behavior: t
          } = {}) => {
            "smooth" === t && this.isDynamicMode() && console.warn("The `smooth` scroll behavior is not fully supported with dynamic size."), this._scrollToOffset(this.getScrollOffset() + e, {
              adjustments: void 0,
              behavior: t
            })
          }, this.getTotalSize = () => {
            var e;
            let t, r = this.getMeasurements();
            if (0 === r.length) t = this.options.paddingStart;
            else if (1 === this.options.lanes) t = (null == (e = r[r.length - 1]) ? void 0 : e.end) ?? 0;
            else {
              let e = Array(this.options.lanes).fill(null),
                i = r.length - 1;
              for (; i >= 0 && e.some(e => null === e);) {
                let t = r[i];
                null === e[t.lane] && (e[t.lane] = t.end), i--
              }
              t = Math.max(...e.filter(e => null !== e))
            }
            return Math.max(t - this.options.scrollMargin + this.options.paddingEnd, 0)
          }, this._scrollToOffset = (e, {
            adjustments: t,
            behavior: r
          }) => {
            this.options.scrollToFn(e, {
              behavior: r,
              adjustments: t
            }, this)
          }, this.measure = () => {
            this.itemSizeCache = new Map, this.laneAssignments = new Map, this.notify(!1)
          }, this.setOptions(e)
        }
      }
      let v = (e, t, r, i) => {
        for (; e <= t;) {
          let n = (e + t) / 2 | 0,
            s = r(n);
          if (s < i) e = n + 1;
          else {
            if (!(s > i)) return n;
            t = n - 1
          }
        }
        return e > 0 ? e - 1 : 0
      }
    }
  }
]);
//# sourceMappingURL=17383-e0b14a829f4de8f1-7838eae36f394988.js.map