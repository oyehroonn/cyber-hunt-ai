performance.mark("js-parse-end:49957-e3bf0e20ef9a29eb.js");
"use strict";
(globalThis.webpackChunk_github_ui_github_ui = globalThis.webpackChunk_github_ui_github_ui || []).push([
  ["49957"], {
    72681(a, e, n) {
      n.d(e, {
        H: () => h
      });
      var l = n(74848),
        i = n(38621),
        t = n(55368),
        m = n(34164);

      function r(a) {
        return (0, l.jsx)("div", {
          role: "alert",
          "aria-atomic": !0,
          children: a.children
        })
      }

      function h({
        children: a,
        hidden: e,
        variant: n
      }) {
        return e ? (0, l.jsx)(r, {}) : (0, l.jsx)(r, {
          children: (0, l.jsx)(t.AnimationProvider, {
            runOnce: !0,
            children: (0, l.jsx)(t.Animate, {
              animate: "fade-in",
              children: (0, l.jsxs)(t.Stack, {
                className: (0, m.$)("Flash-module__Flash__UrsO0", "error" === n ? "Flash-module__FlashError__VXgn5" : "Flash-module__FlashSuccess___kbo4"),
                direction: "horizontal",
                justifyContent: "flex-start",
                gap: 16,
                children: [(0, l.jsx)("div", {
                  className: "success" === n ? "Flash-module__FlashIconSuccess__PuITA" : "Flash-module__FlashIconError__H5NN7",
                  children: "success" === n ? (0, l.jsx)(i.CheckIcon, {
                    size: 16
                  }) : (0, l.jsx)(i.StopIcon, {
                    size: 16
                  })
                }), (0, l.jsx)("div", {
                  children: a
                })]
              })
            })
          })
        })
      }
      r.displayName = "FlashWrapper", h.displayName = "Flash"
    },
    91207(a, e, n) {
      n.d(e, {
        K: () => am,
        t: () => ar
      });
      var l = n(74848),
        i = n(4240),
        t = n(45871),
        m = n(55368),
        r = n(96540),
        h = n(56825),
        o = n(46569),
        p = n(51587),
        s = n(33470);
      let d = (0, r.createContext)(void 0);
      d.displayName = "FormContext";
      var c = n(72681),
        u = n(27119);

      function f({
        fieldName: a,
        hasPhone: e = !1,
        privacyStatementHref: n,
        emailSubscriptionSettingsLinkHref: i,
        children: t
      }) {
        return (0, l.jsxs)(m.FormControl, {
          children: [(0, l.jsx)(m.FormControl.Label, {
            htmlFor: a,
            "data-testid": "label",
            children: (0, l.jsxs)(m.Text, {
              weight: "semibold",
              children: [(0, u.t)(e ? "Yes, please, I\u2019d like to hear from GitHub and its family of companies via email and phone for personalized communications, targeted advertising, and campaign effectiveness. To withdraw consent or manage your contact preferences, visit the" : "Yes, please, I\u2019d like to hear from GitHub and its family of companies via email for personalized communications, targeted advertising, and campaign effectiveness. To withdraw consent or manage your contact preferences, visit the"), " ", (0, l.jsx)(m.InlineLink, {
                ...(0, p.$C)({
                  action: (0, u.t)("Promotional Communications Manager"),
                  tag: "hyperlink",
                  context: "consent_language_canada",
                  location: "form"
                }),
                href: i,
                children: (0, u.t)("Promotional Communications Manager")
              }), ".", " ", (0, l.jsx)(m.InlineLink, {
                ...(0, p.$C)({
                  action: (0, u.t)("GitHub Privacy Statement"),
                  tag: "hyperlink",
                  context: "consent_language_canada",
                  location: "form"
                }),
                href: n,
                children: (0, u.t)("GitHub Privacy Statement")
              }), "."]
            })
          }), t]
        })
      }

      function g({
        fieldName: a,
        privacyStatementHref: e,
        children: n
      }) {
        return (0, l.jsxs)(m.Stack, {
          direction: "vertical",
          padding: "none",
          gap: "condensed",
          children: [(0, l.jsxs)(m.FormControl, {
            children: [(0, l.jsx)(m.FormControl.Label, {
              htmlFor: a,
              "data-testid": "label",
              children: (0, l.jsxs)(m.Text, {
                weight: "semibold",
                children: [(0, u.t)("Yes please, I\u2019d like GitHub and affiliates to use my information for personalized communications, targeted advertising and campaign effectiveness. See the"), " ", (0, l.jsx)(m.InlineLink, {
                  ...(0, p.$C)({
                    action: (0, u.t)("GitHub Privacy Statement"),
                    tag: "hyperlink",
                    context: "consent_language_china",
                    location: "form"
                  }),
                  href: e,
                  children: (0, u.t)("GitHub Privacy Statement")
                }), " ", (0, u.t)("for more details.")]
              })
            }), n]
          }), (0, l.jsx)(m.Text, {
            variant: "muted",
            children: (0, u.t)("Participation requires transferring your personal data to other countries in which GitHub operates, including the United States. By submitting this form, you agree to the transfer of your data outside of China.")
          })]
        })
      }

      function C({
        fieldName: a,
        privacyStatementHref: e,
        children: n
      }) {
        return (0, l.jsxs)(m.FormControl, {
          children: [n, (0, l.jsx)(m.FormControl.Label, {
            htmlFor: a,
            "data-testid": "label",
            children: (0, l.jsxs)(m.Text, {
              weight: "semibold",
              children: [(0, u.t)("Yes please, I\u2019d like GitHub and affiliates to use my information for personalized communications, targeted advertising and campaign effectiveness. See the"), " ", (0, l.jsx)(m.InlineLink, {
                ...(0, p.$C)({
                  action: (0, u.t)("GitHub Privacy Statement"),
                  tag: "hyperlink",
                  context: "consent_language_default",
                  location: "form"
                }),
                href: e,
                children: (0, u.t)("GitHub Privacy Statement")
              }), " ", (0, u.t)("for more details.")]
            })
          })]
        })
      }
      f.displayName = "Canada", g.displayName = "China", C.displayName = "Default";
      var S = n(38621);

      function x({
        fieldName: a,
        exampleFields: e = [],
        privacyStatementHref: n,
        children: i,
        onValidationChange: t
      }) {
        let h = e.map(a => (0, u.t)(a)).join(", "),
          o = (0, r.use)(d),
          {
            ref: c,
            onChange: f,
            id: g,
            ...C
          } = o?.register("primaryConsent", {
            label: "Required Consent",
            required: !0,
            validations: [{
              message: "You need to accept the required checkboxes to continue.",
              schema: s.eu("true")
            }]
          }) ?? {},
          [b, v] = (0, r.useState)(!1);
        return (0, r.useEffect)(() => (o?.register("primaryConsent", {
          label: "Required Consent",
          required: !0,
          validations: [{
            message: "You need to accept the required checkboxes to continue.",
            schema: s.eu("true")
          }]
        }), function() {
          o?.unregister?.("primaryConsent")
        }), []), (0, r.useEffect)(() => {
          t && t(b)
        }, [t, b]), (0, l.jsxs)(m.Stack, {
          direction: "vertical",
          padding: "none",
          gap: "condensed",
          children: [(0, l.jsxs)(m.FormControl, {
            children: [(0, l.jsxs)(m.FormControl.Label, {
              htmlFor: "south-korea-primary-consent",
              children: [(0, l.jsx)(m.Text, {
                children: (0, u.t)("I agree to the collection and use of my personal information (required)*.")
              }), (0, l.jsxs)(m.UnorderedList, {
                children: [(0, l.jsx)(m.UnorderedList.Item, {
                  leadingVisual: S.DotFillIcon,
                  leadingVisualFill: "default",
                  children: (0, l.jsx)(m.Text, {
                    children: (0, u.t)("Items of Personal Information to be Collected: {fields}, and any other fields visible on this form.").replace("{fields}", h)
                  })
                }), (0, l.jsx)(m.UnorderedList.Item, {
                  leadingVisual: S.DotFillIcon,
                  leadingVisualFill: "default",
                  children: (0, l.jsx)(m.Text, {
                    children: (0, u.t)("Purpose of Collection and Use: GitHub will use the data for the purpose described on this form.")
                  })
                }), (0, l.jsx)(m.UnorderedList.Item, {
                  leadingVisual: S.DotFillIcon,
                  leadingVisualFill: "default",
                  children: (0, l.jsx)(m.Text, {
                    children: (0, u.t)("Retention/Use Period of Personal Information: As long as needed to provide the service(s) you are requesting")
                  })
                })]
              })]
            }), (0, l.jsx)(m.Checkbox, {
              value: "true",
              type: "checkbox",
              id: "south-korea-primary-consent",
              checked: b,
              onChange: a => {
                f?.(a), v(!b)
              },
              required: !0,
              ref: c,
              "aria-describedby": g && `${g}-validation`,
              ...(0, p.$C)({
                action: "primary_consent_south_korea",
                tag: "checkbox",
                context: "form_submit",
                location: "form"
              }),
              ...C
            })]
          }), (0, l.jsxs)(m.FormControl, {
            children: [(0, l.jsxs)(m.FormControl.Label, {
              htmlFor: a,
              "data-testid": "label",
              children: [(0, l.jsx)(m.Text, {
                children: (0, u.t)("I agree to receiving marketing information and use of my personal information for marketing purposes (optional).")
              }), (0, l.jsxs)(m.UnorderedList, {
                children: [(0, l.jsx)(m.UnorderedList.Item, {
                  leadingVisual: S.DotFillIcon,
                  leadingVisualFill: "default",
                  children: (0, l.jsx)(m.Text, {
                    children: (0, l.jsx)(m.Text, {
                      as: "span",
                      size: "350",
                      weight: "bold",
                      children: (0, u.t)("Consent to Receive Marketing: The information collected may be used for GitHub for personalized communications, targeted advertising and campaign effectiveness.")
                    })
                  })
                }), (0, l.jsx)(m.UnorderedList.Item, {
                  leadingVisual: S.DotFillIcon,
                  leadingVisualFill: "default",
                  children: (0, l.jsx)(m.Text, {
                    children: (0, u.t)("Items of Personal Information to be Collected: {fields}, and any other fields visible on this form.").replace("{fields}", h)
                  })
                }), (0, l.jsx)(m.UnorderedList.Item, {
                  leadingVisual: S.DotFillIcon,
                  leadingVisualFill: "default",
                  children: (0, l.jsx)(m.Text, {
                    children: (0, u.t)("Purpose of Collection and Use: To contact you for marketing purposes.")
                  })
                }), (0, l.jsx)(m.UnorderedList.Item, {
                  leadingVisual: S.DotFillIcon,
                  leadingVisualFill: "default",
                  children: (0, l.jsx)(m.Text, {
                    children: (0, u.t)("Retention/Use Period of Personal Information: As long as needed to provide the service(s) you are requesting.")
                  })
                })]
              })]
            }), i]
          }), (0, l.jsxs)(m.Text, {
            variant: "muted",
            children: [(0, u.t)("You have the right to refuse the collection and use of your personal information, use of personal information or marketing purposes, and receiving marketing information as set forth above. However, if you refuse, you may not be able to receive the benefits described under Purpose of Collection & Use."), " ", (0, l.jsx)(m.InlineLink, {
              ...(0, p.$C)({
                action: (0, u.t)("GitHub Privacy Statement"),
                tag: "hyperlink",
                context: "consent_language_south_korea",
                location: "form"
              }),
              href: n,
              children: (0, u.t)("GitHub Privacy Statement")
            }), "."]
          })]
        })
      }

      function b({
        children: a,
        privacyStatementHref: e
      }) {
        return (0, l.jsxs)(l.Fragment, {
          children: [a, (0, l.jsxs)(m.Text, {
            children: [(0, u.t)("I will receive personalized communications and targeted advertising from GitHub and affiliates. See the"), " ", (0, l.jsx)(m.InlineLink, {
              ...(0, p.$C)({
                action: (0, u.t)("GitHub Privacy Statement"),
                tag: "hyperlink",
                context: "consent_language_united_states",
                location: "form"
              }),
              href: e,
              children: (0, u.t)("GitHub Privacy Statement")
            }), " ", (0, u.t)("for more details.")]
          })]
        })
      }
      x.displayName = "SouthKorea", b.displayName = "UnitedStates";
      var v = n(51678);

      function M({
        children: a,
        implicitOptIn: e,
        ...n
      }) {
        let {
          selectedCountry: i
        } = (0, r.use)(v.G), t = function(a, e) {
          switch (a) {
            case "CA":
              return f;
            case "CN":
              return g;
            case "KR":
              return x;
            case "US":
              if (e.implicitOptIn) return b;
              return C;
            default:
              return C
          }
        }(i?.alpha || "", {
          implicitOptIn: e
        });
        return (0, l.jsx)(t, {
          ...n,
          children: a
        })
      }
      M.displayName = "ConsentLanguage";
      var y = n(27226);
      let I = ["US"];

      function T({
        selectedCountry: a,
        fieldName: e,
        onValidationChange: n,
        implicitOptIn: i,
        ...t
      }) {
        let [h, o] = (0, r.useState)(!1), [s, c] = (0, r.useState)(!0), u = (0, r.use)(d), {
          onChange: f,
          ref: g,
          ...C
        } = u?.register(e, {
          label: "Marketing Email Opt In",
          required: !1
        }) ?? {};
        return (0, r.useEffect)(() => {
          n && n(!0)
        }, [n]), (0, r.useEffect)(() => {
          i && (I.includes(a.alpha) ? c(!1) : c(!0))
        }, [a, i]), (0, l.jsx)("div", {
          "data-testid": "consent-experience",
          children: (0, l.jsx)(M, {
            fieldName: e,
            onValidationChange: n,
            implicitOptIn: i,
            ...t,
            children: s ? (0, l.jsx)(m.Checkbox, {
              value: y.u.EXPLICIT,
              checked: h,
              hidden: !s,
              onChange: a => {
                f?.(a), o(!h)
              },
              ref: g,
              ...(0, p.$C)({
                action: "consent_language",
                tag: "checkbox",
                context: "form_control",
                location: "form"
              }),
              ...C
            }) : (0, l.jsx)("input", {
              type: "hidden",
              name: e,
              value: y.u.IMPLICIT,
              ref: g
            })
          })
        })
      }
      T.displayName = "ConsentExperienceInput";
      let N = ({
        implicitOptIn: a = !0
      }) => {
        let e = (0, r.use)(d),
          n = (0, r.use)(v.G),
          i = e?.errors.primaryConsent,
          t = e?.formFields?.primaryConsent?.id;
        return (0, l.jsx)(m.Stack, {
          direction: "vertical",
          gap: "condensed",
          padding: "none",
          children: (0, l.jsxs)(m.FormControl, {
            id: "form-field-consent-experience",
            validationStatus: "string" == typeof i ? "error" : void 0,
            fullWidth: !0,
            children: [(0, l.jsx)(T, {
              selectedCountry: n.selectedCountry ?? {
                name: "",
                alpha: ""
              },
              emailSubscriptionSettingsLinkHref: "/settings/emails/subscriptions/link-request/new",
              exampleFields: ["first name", "last name", "company", "email"],
              fieldName: "marketing_email_opt_in",
              privacyStatementHref: "https://docs.github.com/articles/github-privacy-statement",
              implicitOptIn: a
            }), "string" == typeof i ? (0, l.jsx)(m.FormControl.Validation, {
              id: `${t}-validation`,
              children: i
            }) : null]
          })
        })
      };
      N.displayName = "ConsentExperience";
      var G = n(57766);

      function j(a) {
        let {
          hostName: e,
          originPage: n,
          locale: i
        } = (0, r.use)(G.x), [t, m] = (0, r.useState)(void 0), [h, o] = (0, r.useState)(!1), [p, s] = (0, r.useState)(!1), [d, c] = (0, r.useState)(!1), [u, f] = (0, r.useState)(""), g = (0, r.useCallback)(() => {
          h || p || (c(!0), void 0 !== a.onLoadError && a.onLoadError(Error("Octocaptcha did not load and timed out")))
        }, [h, p, a]), C = (0, r.useCallback)(n => {
          if (new URL(n.origin, window.location.origin).host !== e) return;
          let {
            data: l
          } = n;
          "captcha-complete" === l.event && (f(l.sessionToken), void 0 !== a.onComplete && a.onComplete({
            token: l.sessionToken
          })), "captcha-loaded" === l.event && o(!0), "captcha-suppressed" === l.event && s(!0)
        }, [a, e]);
        return (0, r.useEffect)(() => {
          let a = new URLSearchParams({
            origin: window.location.origin,
            responsive: "true",
            require_ack: "true"
          });
          void 0 !== n && a.append("origin_page", n), void 0 !== i && a.append("locale", i);
          let l = e.includes("localhost") ? "http" : "https",
            t = new URL(`${l}://${e}`, window.location.origin);
          t.search = a.toString(), m(t.toString())
        }, [n, e, i]), (0, r.useEffect)(() => (window.addEventListener("message", C), () => {
          window.removeEventListener("message", C)
        }), [C]), (0, r.useEffect)(() => {
          let e = setTimeout(g, a.timeoutAfter ?? 3e4);
          return () => {
            clearTimeout(e)
          }
        }, [a.timeoutAfter, g]), (0, l.jsxs)("div", {
          className: `position-relative ${a.className??""}`,
          style: {
            height: 310
          },
          children: [!h && (0, l.jsx)(F, {
            children: (0, l.jsx)("img", {
              src: "/images/spinners/octocat-spinner-128.gif",
              alt: "Loading CAPTCHA...",
              width: 64,
              height: 64
            })
          }), p && (0, l.jsx)(F, {
            children: (0, l.jsx)(S.CheckCircleIcon, {
              size: 64,
              "aria-label": "Account has been verified. Please continue."
            })
          }), void 0 !== t && (0, l.jsx)("iframe", {
            src: t,
            title: "Please verify by completing this captcha.",
            className: "d-block position-absolute height-full width-full top-0 left-0 border-0",
            style: h && !p ? {} : {
              height: 0,
              visibility: "hidden"
            }
          }), d ? (0, l.jsx)("input", {
            type: "hidden",
            id: "error_loading_captcha",
            name: "error_loading_captcha",
            defaultValue: "1"
          }) : (0, l.jsx)("input", {
            className: "d-none",
            name: "octocaptcha-token",
            required: !0,
            defaultValue: u
          })]
        })
      }
      j.displayName = "Octocaptcha";
      let F = a => (0, l.jsx)("div", {
        className: "position-absolute height-full width-full top-0 left-0 d-flex flex-justify-center flex-items-center border rounded-2",
        style: {
          backgroundColor: "var(--brand-color-canvas-default)",
          color: "var(--brand-color-success-fg)"
        },
        children: a.children
      });
      F.displayName = "LoadingSkeleton";
      let E = [{
          alpha: "AF",
          name: "Afganist\xe1n"
        }, {
          alpha: "AX",
          name: "\xc5land"
        }, {
          alpha: "AL",
          name: "Albania"
        }, {
          alpha: "DE",
          name: "Alemania"
        }, {
          alpha: "AD",
          name: "Andorra"
        }, {
          alpha: "AO",
          name: "Angola"
        }, {
          alpha: "AI",
          name: "Anguilla"
        }, {
          alpha: "AQ",
          name: "Ant\xe1rtida"
        }, {
          alpha: "AG",
          name: "Antigua y Barbuda"
        }, {
          alpha: "SA",
          name: "Arabia Saudita"
        }, {
          alpha: "DZ",
          name: "Argelia"
        }, {
          alpha: "AR",
          name: "Argentina"
        }, {
          alpha: "AM",
          name: "Armenia"
        }, {
          alpha: "AW",
          name: "Aruba"
        }, {
          alpha: "AU",
          name: "Australia"
        }, {
          alpha: "AT",
          name: "Austria"
        }, {
          alpha: "AZ",
          name: "Azerbaiy\xe1n"
        }, {
          alpha: "BS",
          name: "Bahamas"
        }, {
          alpha: "BD",
          name: "Banglad\xe9s"
        }, {
          alpha: "BB",
          name: "Barbados"
        }, {
          alpha: "BH",
          name: "Bar\xe9in"
        }, {
          alpha: "BE",
          name: "B\xe9lgica"
        }, {
          alpha: "BZ",
          name: "Belice"
        }, {
          alpha: "BJ",
          name: "Ben\xedn"
        }, {
          alpha: "BM",
          name: "Bermudas"
        }, {
          alpha: "BY",
          name: "Bielorrusia"
        }, {
          alpha: "BO",
          name: "Bolivia"
        }, {
          alpha: "BQ",
          name: "Bonaire, San Eustaquio y Saba"
        }, {
          alpha: "BA",
          name: "Bosnia y Herzegovina"
        }, {
          alpha: "BW",
          name: "Botsuana"
        }, {
          alpha: "BR",
          name: "Brasil"
        }, {
          alpha: "BN",
          name: "Brun\xe9i Darussalam"
        }, {
          alpha: "BG",
          name: "Bulgaria"
        }, {
          alpha: "BF",
          name: "Burkina Faso"
        }, {
          alpha: "BI",
          name: "Burundi"
        }, {
          alpha: "BT",
          name: "But\xe1n"
        }, {
          alpha: "CV",
          name: "Cabo Verde"
        }, {
          alpha: "KH",
          name: "Camboya"
        }, {
          alpha: "CM",
          name: "Camer\xfan"
        }, {
          alpha: "CA",
          name: "Canad\xe1"
        }, {
          alpha: "QA",
          name: "Catar"
        }, {
          alpha: "TD",
          name: "Chad"
        }, {
          alpha: "CL",
          name: "Chile"
        }, {
          alpha: "CN",
          name: "China"
        }, {
          alpha: "CY",
          name: "Chipre"
        }, {
          alpha: "VA",
          name: "Ciudad del Vaticano"
        }, {
          alpha: "CO",
          name: "Colombia"
        }, {
          alpha: "KM",
          name: "Comoras"
        }, {
          alpha: "CG",
          name: "Congo (Brazzaville)"
        }, {
          alpha: "CD",
          name: "Congo (Kinsasa)"
        }, {
          alpha: "KR",
          name: "Corea del Sur"
        }, {
          alpha: "CI",
          name: "Costa de Marfil"
        }, {
          alpha: "CR",
          name: "Costa Rica"
        }, {
          alpha: "HR",
          name: "Croacia"
        }, {
          alpha: "CW",
          name: "Curazao"
        }, {
          alpha: "DK",
          name: "Dinamarca"
        }, {
          alpha: "DM",
          name: "Dominica"
        }, {
          alpha: "EC",
          name: "Ecuador"
        }, {
          alpha: "EG",
          name: "Egipto"
        }, {
          alpha: "SV",
          name: "El Salvador"
        }, {
          alpha: "AE",
          name: "Emiratos \xc1rabes Unidos"
        }, {
          alpha: "ER",
          name: "Eritrea"
        }, {
          alpha: "SK",
          name: "Eslovaquia"
        }, {
          alpha: "SI",
          name: "Eslovenia"
        }, {
          alpha: "ES",
          name: "Espa\xf1a"
        }, {
          alpha: "US",
          name: "Estados Unidos de Am\xe9rica"
        }, {
          alpha: "EE",
          name: "Estonia"
        }, {
          alpha: "ET",
          name: "Etiop\xeda"
        }, {
          alpha: "PH",
          name: "Filipinas"
        }, {
          alpha: "FI",
          name: "Finlandia"
        }, {
          alpha: "FJ",
          name: "Fiyi"
        }, {
          alpha: "FR",
          name: "Francia"
        }, {
          alpha: "GA",
          name: "Gab\xf3n"
        }, {
          alpha: "GM",
          name: "Gambia"
        }, {
          alpha: "GE",
          name: "Georgia"
        }, {
          alpha: "GH",
          name: "Ghana"
        }, {
          alpha: "GI",
          name: "Gibraltar"
        }, {
          alpha: "GD",
          name: "Granada"
        }, {
          alpha: "GR",
          name: "Grecia"
        }, {
          alpha: "GL",
          name: "Groenlandia"
        }, {
          alpha: "GP",
          name: "Guadalupe"
        }, {
          alpha: "GU",
          name: "Guam"
        }, {
          alpha: "GT",
          name: "Guatemala"
        }, {
          alpha: "GF",
          name: "Guayana Francesa"
        }, {
          alpha: "GG",
          name: "Guernesey"
        }, {
          alpha: "GN",
          name: "Guinea"
        }, {
          alpha: "GQ",
          name: "Guinea Ecuatorial"
        }, {
          alpha: "GW",
          name: "Guinea-Bis\xe1u"
        }, {
          alpha: "GY",
          name: "Guyana"
        }, {
          alpha: "HT",
          name: "Hait\xed"
        }, {
          alpha: "HN",
          name: "Honduras"
        }, {
          alpha: "HK",
          name: "Hong Kong"
        }, {
          alpha: "HU",
          name: "Hungr\xeda"
        }, {
          alpha: "IN",
          name: "India"
        }, {
          alpha: "ID",
          name: "Indonesia"
        }, {
          alpha: "IQ",
          name: "Irak"
        }, {
          alpha: "IR",
          name: "Ir\xe1n"
        }, {
          alpha: "IE",
          name: "Irlanda"
        }, {
          alpha: "BV",
          name: "Isla Bouvet"
        }, {
          alpha: "IM",
          name: "Isla de Man"
        }, {
          alpha: "CX",
          name: "Isla de Navidad"
        }, {
          alpha: "NF",
          name: "Isla Norfolk"
        }, {
          alpha: "SH",
          name: "Isla Santa Elena"
        }, {
          alpha: "IS",
          name: "Islandia"
        }, {
          alpha: "KY",
          name: "Islas Caim\xe1n"
        }, {
          alpha: "CC",
          name: "Islas Cocos"
        }, {
          alpha: "CK",
          name: "Islas Cook"
        }, {
          alpha: "FO",
          name: "Islas Feroe"
        }, {
          alpha: "GS",
          name: "Islas Georgias del Sur y Sandwich del Sur"
        }, {
          alpha: "HM",
          name: "Islas Heard y McDonald"
        }, {
          alpha: "FK",
          name: "Islas Malvinas"
        }, {
          alpha: "MP",
          name: "Islas Marianas del Norte"
        }, {
          alpha: "MH",
          name: "Islas Marshall"
        }, {
          alpha: "PN",
          name: "Islas Pitcairn"
        }, {
          alpha: "SB",
          name: "Islas Salom\xf3n"
        }, {
          alpha: "TC",
          name: "Islas Turcas y Caicos"
        }, {
          alpha: "UM",
          name: "Islas Ultramarinas Menores de los Estados Unidos"
        }, {
          alpha: "VG",
          name: "Islas V\xedrgenes Brit\xe1nicas"
        }, {
          alpha: "VI",
          name: "Islas V\xedrgenes de los Estados Unidos"
        }, {
          alpha: "IL",
          name: "Israel"
        }, {
          alpha: "IT",
          name: "Italia"
        }, {
          alpha: "JM",
          name: "Jamaica"
        }, {
          alpha: "JP",
          name: "Jap\xf3n"
        }, {
          alpha: "JE",
          name: "Jersey"
        }, {
          alpha: "JO",
          name: "Jordania"
        }, {
          alpha: "KZ",
          name: "Kazajist\xe1n"
        }, {
          alpha: "KE",
          name: "Kenia"
        }, {
          alpha: "KG",
          name: "Kirguist\xe1n"
        }, {
          alpha: "KI",
          name: "Kiribati"
        }, {
          alpha: "KW",
          name: "Kuwait"
        }, {
          alpha: "LA",
          name: "Laos"
        }, {
          alpha: "LS",
          name: "Lesoto"
        }, {
          alpha: "LV",
          name: "Letonia"
        }, {
          alpha: "LB",
          name: "L\xedbano"
        }, {
          alpha: "LR",
          name: "Liberia"
        }, {
          alpha: "LY",
          name: "Libia"
        }, {
          alpha: "LI",
          name: "Liechtenstein"
        }, {
          alpha: "LT",
          name: "Lituania"
        }, {
          alpha: "LU",
          name: "Luxemburgo"
        }, {
          alpha: "MO",
          name: "Macao"
        }, {
          alpha: "MK",
          name: "Macedonia"
        }, {
          alpha: "MG",
          name: "Madagascar"
        }, {
          alpha: "MY",
          name: "Malasia"
        }, {
          alpha: "MW",
          name: "Malaui"
        }, {
          alpha: "MV",
          name: "Maldivas"
        }, {
          alpha: "ML",
          name: "Mal\xed"
        }, {
          alpha: "MT",
          name: "Malta"
        }, {
          alpha: "MA",
          name: "Marruecos"
        }, {
          alpha: "MQ",
          name: "Martinica"
        }, {
          alpha: "MU",
          name: "Mauricio"
        }, {
          alpha: "MR",
          name: "Mauritania"
        }, {
          alpha: "YT",
          name: "Mayotte"
        }, {
          alpha: "MX",
          name: "M\xe9xico"
        }, {
          alpha: "FM",
          name: "Micronesia"
        }, {
          alpha: "MD",
          name: "Moldavia"
        }, {
          alpha: "MC",
          name: "M\xf3naco"
        }, {
          alpha: "MN",
          name: "Mongolia"
        }, {
          alpha: "ME",
          name: "Montenegro"
        }, {
          alpha: "MS",
          name: "Montserrat"
        }, {
          alpha: "MZ",
          name: "Mozambique"
        }, {
          alpha: "MM",
          name: "Myanmar"
        }, {
          alpha: "NA",
          name: "Namibia"
        }, {
          alpha: "NR",
          name: "Nauru"
        }, {
          alpha: "NP",
          name: "Nepal"
        }, {
          alpha: "NI",
          name: "Nicaragua"
        }, {
          alpha: "NE",
          name: "N\xedger"
        }, {
          alpha: "NG",
          name: "Nigeria"
        }, {
          alpha: "NU",
          name: "Niue"
        }, {
          alpha: "NO",
          name: "Noruega"
        }, {
          alpha: "NC",
          name: "Nueva Caledonia"
        }, {
          alpha: "NZ",
          name: "Nueva Zelanda"
        }, {
          alpha: "OM",
          name: "Om\xe1n"
        }, {
          alpha: "NL",
          name: "Pa\xedses Bajos"
        }, {
          alpha: "PK",
          name: "Pakist\xe1n"
        }, {
          alpha: "PW",
          name: "Palaos"
        }, {
          alpha: "PS",
          name: "Palestina"
        }, {
          alpha: "PA",
          name: "Panam\xe1"
        }, {
          alpha: "PG",
          name: "Pap\xfaa Nueva Guinea"
        }, {
          alpha: "PY",
          name: "Paraguay"
        }, {
          alpha: "PE",
          name: "Per\xfa"
        }, {
          alpha: "PF",
          name: "Polinesia Francesa"
        }, {
          alpha: "PL",
          name: "Polonia"
        }, {
          alpha: "PT",
          name: "Portugal"
        }, {
          alpha: "PR",
          name: "Puerto Rico"
        }, {
          alpha: "GB",
          name: "Reino Unido"
        }, {
          alpha: "CF",
          name: "Rep\xfablica Centroafricana"
        }, {
          alpha: "CZ",
          name: "Rep\xfablica Checa"
        }, {
          alpha: "DO",
          name: "Rep\xfablica Dominicana"
        }, {
          alpha: "RE",
          name: "Reuni\xf3n"
        }, {
          alpha: "RW",
          name: "Ruanda"
        }, {
          alpha: "RO",
          name: "Ruman\xeda"
        }, {
          alpha: "WS",
          name: "Samoa"
        }, {
          alpha: "AS",
          name: "Samoa Americana"
        }, {
          alpha: "BL",
          name: "San Bartolom\xe9"
        }, {
          alpha: "KN",
          name: "San Crist\xf3bal y Nieves"
        }, {
          alpha: "SM",
          name: "San Marino"
        }, {
          alpha: "SX",
          name: "San Mart\xedn (Pa\xedses Bajos)"
        }, {
          alpha: "MF",
          name: "San Mart\xedn (parte francesa)"
        }, {
          alpha: "PM",
          name: "San Pedro y Miquel\xf3n"
        }, {
          alpha: "VC",
          name: "San Vicente y las Granadinas"
        }, {
          alpha: "LC",
          name: "Santa Luc\xeda"
        }, {
          alpha: "ST",
          name: "Santo Tom\xe9 y Pr\xedncipe"
        }, {
          alpha: "SN",
          name: "Senegal"
        }, {
          alpha: "RS",
          name: "Serbia"
        }, {
          alpha: "SC",
          name: "Seychelles"
        }, {
          alpha: "SL",
          name: "Sierra Leona"
        }, {
          alpha: "SG",
          name: "Singapur"
        }, {
          alpha: "SY",
          name: "Siria"
        }, {
          alpha: "SO",
          name: "Somalia"
        }, {
          alpha: "LK",
          name: "Sri Lanka"
        }, {
          alpha: "SZ",
          name: "Suazilandia"
        }, {
          alpha: "ZA",
          name: "Sud\xe1frica"
        }, {
          alpha: "SD",
          name: "Sud\xe1n"
        }, {
          alpha: "SS",
          name: "Sud\xe1n del Sur"
        }, {
          alpha: "SE",
          name: "Suecia"
        }, {
          alpha: "CH",
          name: "Suiza"
        }, {
          alpha: "SR",
          name: "Surinam"
        }, {
          alpha: "SJ",
          name: "Svalbard y Jan Mayen"
        }, {
          alpha: "TH",
          name: "Tailandia"
        }, {
          alpha: "TW",
          name: "Taiw\xe1n"
        }, {
          alpha: "TZ",
          name: "Tanzania"
        }, {
          alpha: "TJ",
          name: "Tayikist\xe1n"
        }, {
          alpha: "IO",
          name: "Territorio Brit\xe1nico del Oc\xe9ano \xcdndico"
        }, {
          alpha: "TF",
          name: "Tierras Australes Francesas"
        }, {
          alpha: "TL",
          name: "Timor Oriental"
        }, {
          alpha: "TG",
          name: "Togo"
        }, {
          alpha: "TK",
          name: "Tokelau"
        }, {
          alpha: "TO",
          name: "Tonga"
        }, {
          alpha: "TT",
          name: "Trinidad y Tobago"
        }, {
          alpha: "TN",
          name: "T\xfanez"
        }, {
          alpha: "TM",
          name: "Turkmenist\xe1n"
        }, {
          alpha: "TR",
          name: "Turqu\xeda"
        }, {
          alpha: "TV",
          name: "Tuvalu"
        }, {
          alpha: "UA",
          name: "Ucrania"
        }, {
          alpha: "UG",
          name: "Uganda"
        }, {
          alpha: "UY",
          name: "Uruguay"
        }, {
          alpha: "UZ",
          name: "Uzbekist\xe1n"
        }, {
          alpha: "VU",
          name: "Vanuatu"
        }, {
          alpha: "VE",
          name: "Venezuela"
        }, {
          alpha: "VN",
          name: "Vietnam"
        }, {
          alpha: "WF",
          name: "Wallis y Futuna"
        }, {
          alpha: "YE",
          name: "Yemen"
        }, {
          alpha: "DJ",
          name: "Yibuti"
        }, {
          alpha: "ZM",
          name: "Zambia"
        }, {
          alpha: "ZW",
          name: "Zimbabue"
        }],
        A = [{
          alpha: "GH",
          name: "\uAC00\uB098"
        }, {
          alpha: "GA",
          name: "\uAC00\uBD09"
        }, {
          alpha: "GY",
          name: "\uAC00\uC774\uC544\uB098"
        }, {
          alpha: "GM",
          name: "\uAC10\uBE44\uC544"
        }, {
          alpha: "GG",
          name: "\uAC74\uC9C0"
        }, {
          alpha: "GP",
          name: "\uACFC\uB4E4\uB8E8\uD504"
        }, {
          alpha: "GT",
          name: "\uACFC\uD14C\uB9D0\uB77C"
        }, {
          alpha: "GU",
          name: "\uAD0C"
        }, {
          alpha: "GD",
          name: "\uADF8\uB808\uB098\uB2E4"
        }, {
          alpha: "GR",
          name: "\uADF8\uB9AC\uC2A4"
        }, {
          alpha: "GL",
          name: "\uADF8\uB9B0\uB780\uB4DC"
        }, {
          alpha: "GN",
          name: "\uAE30\uB2C8"
        }, {
          alpha: "GW",
          name: "\uAE30\uB2C8\uBE44\uC0AC\uC6B0"
        }, {
          alpha: "NA",
          name: "\uB098\uBBF8\uBE44\uC544"
        }, {
          alpha: "NR",
          name: "\uB098\uC6B0\uB8E8"
        }, {
          alpha: "NG",
          name: "\uB098\uC774\uC9C0\uB9AC\uC544"
        }, {
          alpha: "AQ",
          name: "\uB0A8\uADF9 \uB300\uB959"
        }, {
          alpha: "SS",
          name: "\uB0A8\uC218\uB2E8"
        }, {
          alpha: "ZA",
          name: "\uB0A8\uC544\uD504\uB9AC\uCE74 \uACF5\uD654\uAD6D"
        }, {
          alpha: "NL",
          name: "\uB124\uB35C\uB780\uB4DC"
        }, {
          alpha: "NP",
          name: "\uB124\uD314"
        }, {
          alpha: "NO",
          name: "\uB178\uB974\uC6E8\uC774"
        }, {
          alpha: "NF",
          name: "\uB178\uD37D \uC12C"
        }, {
          alpha: "NZ",
          name: "\uB274\uC9C8\uB79C\uB4DC"
        }, {
          alpha: "NC",
          name: "\uB274\uCE7C\uB808\uB3C4\uB2C8\uC544"
        }, {
          alpha: "NU",
          name: "\uB2C8\uC6B0\uC5D0"
        }, {
          alpha: "NE",
          name: "\uB2C8\uC81C\uB974"
        }, {
          alpha: "NI",
          name: "\uB2C8\uCE74\uB77C\uACFC"
        }, {
          alpha: "TW",
          name: "\uB300\uB9CC"
        }, {
          alpha: "KR",
          name: "\uB300\uD55C\uBBFC\uAD6D"
        }, {
          alpha: "DK",
          name: "\uB374\uB9C8\uD06C"
        }, {
          alpha: "DM",
          name: "\uB3C4\uBBF8\uB2C8\uCE74"
        }, {
          alpha: "DO",
          name: "\uB3C4\uBBF8\uB2C8\uCE74 \uACF5\uD654\uAD6D"
        }, {
          alpha: "DE",
          name: "\uB3C5\uC77C"
        }, {
          alpha: "TL",
          name: "\uB3D9\uD2F0\uBAA8\uB974"
        }, {
          alpha: "LA",
          name: "\uB77C\uC624\uC2A4"
        }, {
          alpha: "LR",
          name: "\uB77C\uC774\uBCA0\uB9AC\uC544"
        }, {
          alpha: "LV",
          name: "\uB77C\uD2B8\uBE44\uC544"
        }, {
          alpha: "LB",
          name: "\uB808\uBC14\uB17C"
        }, {
          alpha: "LS",
          name: "\uB808\uC18C\uD1A0"
        }, {
          alpha: "RE",
          name: "\uB808\uC704\uB2C8\uC639"
        }, {
          alpha: "RO",
          name: "\uB8E8\uB9C8\uB2C8\uC544"
        }, {
          alpha: "LU",
          name: "\uB8E9\uC148\uBD80\uB974\uD06C"
        }, {
          alpha: "RW",
          name: "\uB974\uC644\uB2E4"
        }, {
          alpha: "LY",
          name: "\uB9AC\uBE44\uC544"
        }, {
          alpha: "LT",
          name: "\uB9AC\uD22C\uC544\uB2C8\uC544"
        }, {
          alpha: "LI",
          name: "\uB9AC\uD788\uD150\uC288\uD0C0\uC778"
        }, {
          alpha: "MG",
          name: "\uB9C8\uB2E4\uAC00\uC2A4\uCE74\uB974"
        }, {
          alpha: "MQ",
          name: "\uB9C8\uB974\uD2F0\uB2C8\uD06C"
        }, {
          alpha: "MH",
          name: "\uB9C8\uC15C \uC81C\uB3C4"
        }, {
          alpha: "YT",
          name: "\uB9C8\uC694\uD2B8"
        }, {
          alpha: "MO",
          name: "\uB9C8\uCE74\uC624"
        }, {
          alpha: "MW",
          name: "\uB9D0\uB77C\uC704"
        }, {
          alpha: "MY",
          name: "\uB9D0\uB808\uC774\uC2DC\uC544"
        }, {
          alpha: "ML",
          name: "\uB9D0\uB9AC"
        }, {
          alpha: "IM",
          name: "\uB9E8 \uC12C"
        }, {
          alpha: "MX",
          name: "\uBA55\uC2DC\uCF54"
        }, {
          alpha: "MC",
          name: "\uBAA8\uB098\uCF54"
        }, {
          alpha: "MA",
          name: "\uBAA8\uB85C\uCF54"
        }, {
          alpha: "MU",
          name: "\uBAA8\uB9AC\uC154\uC2A4"
        }, {
          alpha: "MR",
          name: "\uBAA8\uB9AC\uD0C0\uB2C8"
        }, {
          alpha: "MZ",
          name: "\uBAA8\uC7A0\uBE44\uD06C"
        }, {
          alpha: "ME",
          name: "\uBAAC\uD14C\uB124\uADF8\uB85C"
        }, {
          alpha: "MS",
          name: "\uBAAC\uD2B8\uC138\uB77C\uD2B8"
        }, {
          alpha: "MD",
          name: "\uBAB0\uB3C4\uBC14"
        }, {
          alpha: "MV",
          name: "\uBAB0\uB514\uBE0C"
        }, {
          alpha: "MT",
          name: "\uBAB0\uD0C0"
        }, {
          alpha: "MN",
          name: "\uBABD\uACE8"
        }, {
          alpha: "US",
          name: "\uBBF8\uAD6D"
        }, {
          alpha: "UM",
          name: "\uBBF8\uAD6D\uB839 \uAD70\uC18C \uC81C\uB3C4"
        }, {
          alpha: "VI",
          name: "\uBBF8\uAD6D\uB839 \uBC84\uC9C4\uC544\uC77C\uB79C\uB4DC"
        }, {
          alpha: "AS",
          name: "\uBBF8\uAD6D\uB839 \uC0AC\uBAA8\uC544"
        }, {
          alpha: "MM",
          name: "\uBBF8\uC580\uB9C8"
        }, {
          alpha: "FM",
          name: "\uBBF8\uD06C\uB85C\uB124\uC2DC\uC544"
        }, {
          alpha: "VU",
          name: "\uBC14\uB204\uC544\uD22C"
        }, {
          alpha: "BH",
          name: "\uBC14\uB808\uC778"
        }, {
          alpha: "BB",
          name: "\uBC14\uBCA0\uC774\uB3C4\uC2A4"
        }, {
          alpha: "VA",
          name: "\uBC14\uD2F0\uCE78 \uC2DC\uAD6D"
        }, {
          alpha: "BS",
          name: "\uBC14\uD558\uB9C8"
        }, {
          alpha: "BD",
          name: "\uBC29\uAE00\uB77C\uB370\uC2DC"
        }, {
          alpha: "BM",
          name: "\uBC84\uBBA4\uB2E4"
        }, {
          alpha: "BJ",
          name: "\uBCA0\uB0C9"
        }, {
          alpha: "VE",
          name: "\uBCA0\uB124\uC218\uC5D8\uB77C"
        }, {
          alpha: "VN",
          name: "\uBCA0\uD2B8\uB0A8"
        }, {
          alpha: "BE",
          name: "\uBCA8\uAE30\uC5D0"
        }, {
          alpha: "BY",
          name: "\uBCA8\uB77C\uB8E8\uC2A4"
        }, {
          alpha: "BZ",
          name: "\uBCA8\uB9AC\uC988"
        }, {
          alpha: "BQ",
          name: "\uBCF4\uB124\uB974, \uC2E0\uD2B8\uC678\uC2A4\uD0C0\uD2F0\uC6B0\uC2A4, \uC0AC\uBC14"
        }, {
          alpha: "BA",
          name: "\uBCF4\uC2A4\uB2C8\uC544 \uD5E4\uB974\uCCB4\uACE0\uBE44\uB098"
        }, {
          alpha: "BW",
          name: "\uBCF4\uCE20\uC640\uB098"
        }, {
          alpha: "BO",
          name: "\uBCFC\uB9AC\uBE44\uC544"
        }, {
          alpha: "BI",
          name: "\uBD80\uB8EC\uB514"
        }, {
          alpha: "BF",
          name: "\uBD80\uB974\uD0A4\uB098\uD30C\uC18C"
        }, {
          alpha: "BV",
          name: "\uBD80\uBCA0 \uC12C"
        }, {
          alpha: "BT",
          name: "\uBD80\uD0C4"
        }, {
          alpha: "MP",
          name: "\uBD81\uB9C8\uB9AC\uC544\uB098 \uC81C\uB3C4"
        }, {
          alpha: "MK",
          name: "\uBD81\uB9C8\uCF00\uB3C4\uB2C8\uC544"
        }, {
          alpha: "BG",
          name: "\uBD88\uAC00\uB9AC\uC544"
        }, {
          alpha: "BR",
          name: "\uBE0C\uB77C\uC9C8"
        }, {
          alpha: "BN",
          name: "\uBE0C\uB8E8\uB098\uC774 \uB2E4\uB8E8\uC0B4\uB78C"
        }, {
          alpha: "WS",
          name: "\uC0AC\uBAA8\uC544"
        }, {
          alpha: "SA",
          name: "\uC0AC\uC6B0\uB514\uC544\uB77C\uBE44\uC544"
        }, {
          alpha: "GS",
          name: "\uC0AC\uC6B0\uC2A4\uC870\uC9C0\uC544 \uC0AC\uC6B0\uC2A4 \uC0CC\uB4DC\uC704\uCE58 \uC81C\uB3C4"
        }, {
          alpha: "SM",
          name: "\uC0B0\uB9C8\uB9AC\uB178"
        }, {
          alpha: "ST",
          name: "\uC0C1\uD22C\uBA54 \uD504\uB9B0\uC2DC\uD398"
        }, {
          alpha: "BL",
          name: "\uC0DD\uBC14\uB974\uD154\uB808\uBBF8"
        }, {
          alpha: "PM",
          name: "\uC0DD\uD53C\uC5D0\uB974 \uBBF8\uD074\uB871"
        }, {
          alpha: "SN",
          name: "\uC138\uB124\uAC08"
        }, {
          alpha: "RS",
          name: "\uC138\uB974\uBE44\uC544"
        }, {
          alpha: "SC",
          name: "\uC138\uC774\uC178"
        }, {
          alpha: "LC",
          name: "\uC138\uC778\uD2B8 \uB8E8\uC2DC\uC544"
        }, {
          alpha: "MF",
          name: "\uC138\uC778\uD2B8 \uB9C8\uD2F4(\uD504\uB791\uC2A4\uB839)"
        }, {
          alpha: "VC",
          name: "\uC138\uC778\uD2B8 \uBE48\uC13C\uD2B8 \uADF8\uB808\uB098\uB518"
        }, {
          alpha: "SH",
          name: "\uC138\uC778\uD2B8 \uD5EC\uB808\uB098"
        }, {
          alpha: "KN",
          name: "\uC138\uC778\uD2B8\uD0A4\uCE20 \uB124\uBE44\uC2A4"
        }, {
          alpha: "SO",
          name: "\uC18C\uB9D0\uB9AC\uC544"
        }, {
          alpha: "SB",
          name: "\uC194\uB85C\uBAAC \uC81C\uB3C4"
        }, {
          alpha: "SD",
          name: "\uC218\uB2E8"
        }, {
          alpha: "SR",
          name: "\uC218\uB9AC\uB0A8"
        }, {
          alpha: "LK",
          name: "\uC2A4\uB9AC\uB791\uCE74"
        }, {
          alpha: "SJ",
          name: "\uC2A4\uBC1C\uBC14\uB974\uC580 \uB9C8\uC60C \uC81C\uB3C4"
        }, {
          alpha: "SE",
          name: "\uC2A4\uC6E8\uB374"
        }, {
          alpha: "CH",
          name: "\uC2A4\uC704\uC2A4"
        }, {
          alpha: "ES",
          name: "\uC2A4\uD398\uC778"
        }, {
          alpha: "SK",
          name: "\uC2AC\uB85C\uBC14\uD0A4\uC544"
        }, {
          alpha: "SI",
          name: "\uC2AC\uB85C\uBCA0\uB2C8\uC544"
        }, {
          alpha: "SY",
          name: "\uC2DC\uB9AC\uC544"
        }, {
          alpha: "SL",
          name: "\uC2DC\uC5D0\uB77C\uB9AC\uC628"
        }, {
          alpha: "SX",
          name: "\uC2E0\uD2B8\uB9C8\uB974\uD134(\uB124\uB35C\uB780\uB4DC\uB839)"
        }, {
          alpha: "SG",
          name: "\uC2F1\uAC00\uD3EC\uB974"
        }, {
          alpha: "AE",
          name: "\uC544\uB78D\uC5D0\uBBF8\uB9AC\uD2B8"
        }, {
          alpha: "AW",
          name: "\uC544\uB8E8\uBC14"
        }, {
          alpha: "AM",
          name: "\uC544\uB974\uBA54\uB2C8\uC544"
        }, {
          alpha: "AR",
          name: "\uC544\uB974\uD5E8\uD2F0\uB098"
        }, {
          alpha: "IS",
          name: "\uC544\uC774\uC2AC\uB780\uB4DC"
        }, {
          alpha: "HT",
          name: "\uC544\uC774\uD2F0"
        }, {
          alpha: "IE",
          name: "\uC544\uC77C\uB79C\uB4DC"
        }, {
          alpha: "AZ",
          name: "\uC544\uC81C\uB974\uBC14\uC774\uC794"
        }, {
          alpha: "AF",
          name: "\uC544\uD504\uAC00\uB2C8\uC2A4\uD0C4"
        }, {
          alpha: "AD",
          name: "\uC548\uB3C4\uB77C"
        }, {
          alpha: "AL",
          name: "\uC54C\uBC14\uB2C8\uC544"
        }, {
          alpha: "DZ",
          name: "\uC54C\uC81C\uB9AC"
        }, {
          alpha: "AO",
          name: "\uC559\uACE8\uB77C"
        }, {
          alpha: "AG",
          name: "\uC564\uD2F0\uAC00 \uBC14\uBD80\uB2E4"
        }, {
          alpha: "AI",
          name: "\uC575\uADC8\uB77C"
        }, {
          alpha: "ER",
          name: "\uC5D0\uB9AC\uD2B8\uB808\uC544"
        }, {
          alpha: "SZ",
          name: "\uC5D0\uC2A4\uC640\uD2F0\uB2C8"
        }, {
          alpha: "EE",
          name: "\uC5D0\uC2A4\uD1A0\uB2C8\uC544"
        }, {
          alpha: "EC",
          name: "\uC5D0\uCF70\uB3C4\uB974"
        }, {
          alpha: "ET",
          name: "\uC5D0\uD2F0\uC624\uD53C\uC544"
        }, {
          alpha: "SV",
          name: "\uC5D8\uC0B4\uBC14\uB3C4\uB974"
        }, {
          alpha: "GB",
          name: "\uC601\uAD6D"
        }, {
          alpha: "VG",
          name: "\uC601\uAD6D\uB839 \uBC84\uC9C4\uC544\uC77C\uB79C\uB4DC"
        }, {
          alpha: "IO",
          name: "\uC601\uAD6D\uB839 \uC778\uB3C4\uC591 \uC81C\uB3C4"
        }, {
          alpha: "YE",
          name: "\uC608\uBA58"
        }, {
          alpha: "OM",
          name: "\uC624\uB9CC"
        }, {
          alpha: "AU",
          name: "\uC624\uC2A4\uD2B8\uB808\uC77C\uB9AC\uC544"
        }, {
          alpha: "AT",
          name: "\uC624\uC2A4\uD2B8\uB9AC\uC544"
        }, {
          alpha: "HN",
          name: "\uC628\uB450\uB77C\uC2A4"
        }, {
          alpha: "AX",
          name: "\uC62C\uB780\uB4DC"
        }, {
          alpha: "WF",
          name: "\uC648\uB9AC\uC2A4 \uD478\uD22C\uB098 \uC81C\uB3C4"
        }, {
          alpha: "JO",
          name: "\uC694\uB974\uB2E8"
        }, {
          alpha: "UG",
          name: "\uC6B0\uAC04\uB2E4"
        }, {
          alpha: "UY",
          name: "\uC6B0\uB8E8\uACFC\uC774"
        }, {
          alpha: "UZ",
          name: "\uC6B0\uC988\uBCA0\uD0A4\uC2A4\uD0C4"
        }, {
          alpha: "UA",
          name: "\uC6B0\uD06C\uB77C\uC774\uB098"
        }, {
          alpha: "IQ",
          name: "\uC774\uB77C\uD06C"
        }, {
          alpha: "IR",
          name: "\uC774\uB780"
        }, {
          alpha: "IL",
          name: "\uC774\uC2A4\uB77C\uC5D8"
        }, {
          alpha: "EG",
          name: "\uC774\uC9D1\uD2B8"
        }, {
          alpha: "IT",
          name: "\uC774\uD0C8\uB9AC\uC544"
        }, {
          alpha: "IN",
          name: "\uC778\uB3C4"
        }, {
          alpha: "ID",
          name: "\uC778\uB3C4\uB124\uC2DC\uC544"
        }, {
          alpha: "JP",
          name: "\uC77C\uBCF8"
        }, {
          alpha: "JM",
          name: "\uC790\uBA54\uC774\uCE74"
        }, {
          alpha: "ZM",
          name: "\uC7A0\uBE44\uC544"
        }, {
          alpha: "JE",
          name: "\uC800\uC9C0"
        }, {
          alpha: "GQ",
          name: "\uC801\uB3C4 \uAE30\uB2C8"
        }, {
          alpha: "GE",
          name: "\uC870\uC9C0\uC544"
        }, {
          alpha: "CN",
          name: "\uC911\uAD6D"
        }, {
          alpha: "CF",
          name: "\uC911\uC559\uC544\uD504\uB9AC\uCE74\uACF5\uD654\uAD6D"
        }, {
          alpha: "DJ",
          name: "\uC9C0\uBD80\uD2F0"
        }, {
          alpha: "GI",
          name: "\uC9C0\uBE0C\uB864\uD130"
        }, {
          alpha: "ZW",
          name: "\uC9D0\uBC14\uBE0C\uC6E8"
        }, {
          alpha: "TD",
          name: "\uCC28\uB4DC"
        }, {
          alpha: "CZ",
          name: "\uCCB4\uCF54 \uACF5\uD654\uAD6D"
        }, {
          alpha: "CL",
          name: "\uCE60\uB808"
        }, {
          alpha: "CM",
          name: "\uCE74\uBA54\uB8EC"
        }, {
          alpha: "CV",
          name: "\uCE74\uBCF4\uBCA0\uB974\uB370"
        }, {
          alpha: "KY",
          name: "\uCE74\uC774\uB9CC \uC81C\uB3C4"
        }, {
          alpha: "KZ",
          name: "\uCE74\uC790\uD750\uC2A4\uD0C4"
        }, {
          alpha: "QA",
          name: "\uCE74\uD0C0\uB974"
        }, {
          alpha: "KH",
          name: "\uCE84\uBCF4\uB514\uC544"
        }, {
          alpha: "CA",
          name: "\uCE90\uB098\uB2E4"
        }, {
          alpha: "KE",
          name: "\uCF00\uB0D0"
        }, {
          alpha: "KM",
          name: "\uCF54\uBAA8\uB85C"
        }, {
          alpha: "CR",
          name: "\uCF54\uC2A4\uD0C0\uB9AC\uCE74"
        }, {
          alpha: "CC",
          name: "\uCF54\uCF54\uC2A4(\uD0AC\uB9C1) \uC81C\uB3C4"
        }, {
          alpha: "CI",
          name: "\uCF54\uD2B8\uB514\uBD80\uC544\uB974"
        }, {
          alpha: "CO",
          name: "\uCF5C\uB86C\uBE44\uC544"
        }, {
          alpha: "CG",
          name: "\uCF69\uACE0(\uACF5\uD654\uAD6D)"
        }, {
          alpha: "CD",
          name: "\uCF69\uACE0\uBBFC\uC8FC\uACF5\uD654\uAD6D"
        }, {
          alpha: "KW",
          name: "\uCFE0\uC6E8\uC774\uD2B8"
        }, {
          alpha: "CK",
          name: "\uCFE1 \uC81C\uB3C4"
        }, {
          alpha: "CW",
          name: "\uD034\uB77C\uC18C"
        }, {
          alpha: "HR",
          name: "\uD06C\uB85C\uC544\uD2F0\uC544"
        }, {
          alpha: "CX",
          name: "\uD06C\uB9AC\uC2A4\uB9C8\uC2A4 \uC12C"
        }, {
          alpha: "KG",
          name: "\uD0A4\uB974\uAE30\uC2A4\uC2A4\uD0C4"
        }, {
          alpha: "KI",
          name: "\uD0A4\uB9AC\uBC14\uC2DC"
        }, {
          alpha: "CY",
          name: "\uD0A4\uD504\uB85C\uC2A4"
        }, {
          alpha: "TJ",
          name: "\uD0C0\uC9C0\uD0A4\uC2A4\uD0C4"
        }, {
          alpha: "TZ",
          name: "\uD0C4\uC790\uB2C8\uC544"
        }, {
          alpha: "TH",
          name: "\uD0DC\uAD6D"
        }, {
          alpha: "TC",
          name: "\uD130\uD06C\uC2A4 \uCF00\uC774\uCEE4\uC2A4 \uC81C\uB3C4"
        }, {
          alpha: "TG",
          name: "\uD1A0\uACE0"
        }, {
          alpha: "TK",
          name: "\uD1A0\uCF08\uB77C\uC6B0"
        }, {
          alpha: "TO",
          name: "\uD1B5\uAC00"
        }, {
          alpha: "TM",
          name: "\uD22C\uB974\uD06C\uBA54\uB2C8\uC2A4\uD0C4"
        }, {
          alpha: "TV",
          name: "\uD22C\uBC1C\uB8E8"
        }, {
          alpha: "TN",
          name: "\uD280\uB2C8\uC9C0"
        }, {
          alpha: "TR",
          name: "\uD280\uB974\uD0A4\uC608"
        }, {
          alpha: "TT",
          name: "\uD2B8\uB9AC\uB2C8\uB2E4\uB4DC \uD1A0\uBC14\uACE0"
        }, {
          alpha: "PA",
          name: "\uD30C\uB098\uB9C8"
        }, {
          alpha: "PY",
          name: "\uD30C\uB77C\uACFC\uC774"
        }, {
          alpha: "PK",
          name: "\uD30C\uD0A4\uC2A4\uD0C4"
        }, {
          alpha: "PG",
          name: "\uD30C\uD478\uC544\uB274\uAE30\uB2C8"
        }, {
          alpha: "PW",
          name: "\uD314\uB77C\uC6B0"
        }, {
          alpha: "PS",
          name: "\uD314\uB808\uC2A4\uD0C0\uC778"
        }, {
          alpha: "FO",
          name: "\uD398\uB85C \uC81C\uB3C4"
        }, {
          alpha: "PE",
          name: "\uD398\uB8E8"
        }, {
          alpha: "PT",
          name: "\uD3EC\uB974\uD22C\uAC08"
        }, {
          alpha: "FK",
          name: "\uD3EC\uD074\uB79C\uB4DC \uC81C\uB3C4"
        }, {
          alpha: "PL",
          name: "\uD3F4\uB780\uB4DC"
        }, {
          alpha: "PR",
          name: "\uD478\uC5D0\uB974\uD1A0\uB9AC\uCF54"
        }, {
          alpha: "FR",
          name: "\uD504\uB791\uC2A4"
        }, {
          alpha: "GF",
          name: "\uD504\uB791\uC2A4\uB839 \uAE30\uC544\uB098"
        }, {
          alpha: "TF",
          name: "\uD504\uB791\uC2A4\uB839 \uB0A8\uADF9 \uC9C0\uC5ED"
        }, {
          alpha: "PF",
          name: "\uD504\uB791\uC2A4\uB839 \uD3F4\uB9AC\uB124\uC2DC\uC544"
        }, {
          alpha: "FJ",
          name: "\uD53C\uC9C0"
        }, {
          alpha: "FI",
          name: "\uD540\uB780\uB4DC"
        }, {
          alpha: "PH",
          name: "\uD544\uB9AC\uD540"
        }, {
          alpha: "PN",
          name: "\uD54F\uCF00\uC5B8"
        }, {
          alpha: "HM",
          name: "\uD5C8\uB4DC \uB9E5\uB3C4\uB110\uB4DC \uC81C\uB3C4"
        }, {
          alpha: "HU",
          name: "\uD5DD\uAC00\uB9AC"
        }, {
          alpha: "HK",
          name: "\uD64D\uCF69"
        }],
        L = [{
          alpha: "AF",
          name: "Afeganist\xe3o"
        }, {
          alpha: "ZA",
          name: "\xc1frica do Sul"
        }, {
          alpha: "AX",
          name: "\xc5land"
        }, {
          alpha: "AL",
          name: "Alb\xe2nia"
        }, {
          alpha: "DE",
          name: "Alemanha"
        }, {
          alpha: "AD",
          name: "Andorra"
        }, {
          alpha: "AO",
          name: "Angola"
        }, {
          alpha: "AI",
          name: "Anguila"
        }, {
          alpha: "AQ",
          name: "Ant\xe1rtica"
        }, {
          alpha: "AG",
          name: "Ant\xedgua e Barbuda"
        }, {
          alpha: "SA",
          name: "Ar\xe1bia Saudita"
        }, {
          alpha: "DZ",
          name: "Arg\xe9lia"
        }, {
          alpha: "AR",
          name: "Argentina"
        }, {
          alpha: "AM",
          name: "Arm\xeania"
        }, {
          alpha: "AW",
          name: "Aruba"
        }, {
          alpha: "AU",
          name: "Austr\xe1lia"
        }, {
          alpha: "AT",
          name: "\xc1ustria"
        }, {
          alpha: "AZ",
          name: "Azerbaij\xe3o"
        }, {
          alpha: "BS",
          name: "Bahamas"
        }, {
          alpha: "BH",
          name: "Bahrein"
        }, {
          alpha: "BD",
          name: "Bangladesh"
        }, {
          alpha: "BB",
          name: "Barbados"
        }, {
          alpha: "BY",
          name: "Belarus"
        }, {
          alpha: "BE",
          name: "B\xe9lgica"
        }, {
          alpha: "BZ",
          name: "Belize"
        }, {
          alpha: "BJ",
          name: "Benin"
        }, {
          alpha: "BM",
          name: "Bermuda"
        }, {
          alpha: "BO",
          name: "Bol\xedvia"
        }, {
          alpha: "BQ",
          name: "Bonaire, Santo Eust\xe1quio e Saba"
        }, {
          alpha: "BA",
          name: "B\xf3snia e Herzegovina"
        }, {
          alpha: "BW",
          name: "Botsuana"
        }, {
          alpha: "BR",
          name: "Brasil"
        }, {
          alpha: "BN",
          name: "Brunei Darussalam"
        }, {
          alpha: "BG",
          name: "Bulg\xe1ria"
        }, {
          alpha: "BF",
          name: "Burquina Faso"
        }, {
          alpha: "BI",
          name: "Burundi"
        }, {
          alpha: "BT",
          name: "But\xe3o"
        }, {
          alpha: "CV",
          name: "Cabo Verde"
        }, {
          alpha: "CM",
          name: "Camar\xf5es"
        }, {
          alpha: "KH",
          name: "Camboja"
        }, {
          alpha: "CA",
          name: "Canad\xe1"
        }, {
          alpha: "QA",
          name: "Catar"
        }, {
          alpha: "KZ",
          name: "Cazaquist\xe3o"
        }, {
          alpha: "TD",
          name: "Chade"
        }, {
          alpha: "CL",
          name: "Chile"
        }, {
          alpha: "CN",
          name: "China"
        }, {
          alpha: "CY",
          name: "Chipre"
        }, {
          alpha: "VA",
          name: "Cidade do Vaticano"
        }, {
          alpha: "CO",
          name: "Col\xf4mbia"
        }, {
          alpha: "KM",
          name: "Comoros"
        }, {
          alpha: "CG",
          name: "Congo (Brazavile)"
        }, {
          alpha: "CD",
          name: "Congo (Quinxassa)"
        }, {
          alpha: "KR",
          name: "Coreia do Sul"
        }, {
          alpha: "CR",
          name: "Costa Rica"
        }, {
          alpha: "CI",
          name: "C\xf4te d'Ivoire"
        }, {
          alpha: "HR",
          name: "Cro\xe1cia"
        }, {
          alpha: "CW",
          name: "Cura\xe7ao"
        }, {
          alpha: "DK",
          name: "Dinamarca"
        }, {
          alpha: "DJ",
          name: "Djibuti"
        }, {
          alpha: "DM",
          name: "Dominica"
        }, {
          alpha: "EG",
          name: "Egito"
        }, {
          alpha: "SV",
          name: "El Salvador"
        }, {
          alpha: "AE",
          name: "Emirados \xc1rabes Unidos"
        }, {
          alpha: "EC",
          name: "Equador"
        }, {
          alpha: "ER",
          name: "Eritreia"
        }, {
          alpha: "SK",
          name: "Eslov\xe1quia"
        }, {
          alpha: "SI",
          name: "Eslov\xeania"
        }, {
          alpha: "ES",
          name: "Espanha"
        }, {
          alpha: "SZ",
          name: "Essuat\xedni"
        }, {
          alpha: "US",
          name: "Estados Unidos da Am\xe9rica"
        }, {
          alpha: "EE",
          name: "Est\xf4nia"
        }, {
          alpha: "ET",
          name: "Eti\xf3pia"
        }, {
          alpha: "FJ",
          name: "Fiji"
        }, {
          alpha: "PH",
          name: "Filipinas"
        }, {
          alpha: "FI",
          name: "Finl\xe2ndia"
        }, {
          alpha: "FR",
          name: "Fran\xe7a"
        }, {
          alpha: "GA",
          name: "Gab\xe3o"
        }, {
          alpha: "GM",
          name: "G\xe2mbia"
        }, {
          alpha: "GH",
          name: "Gana"
        }, {
          alpha: "GE",
          name: "Ge\xf3rgia"
        }, {
          alpha: "GI",
          name: "Gibraltar"
        }, {
          alpha: "GD",
          name: "Granada"
        }, {
          alpha: "GR",
          name: "Gr\xe9cia"
        }, {
          alpha: "GL",
          name: "Groenl\xe2ndia"
        }, {
          alpha: "GP",
          name: "Guadalupe"
        }, {
          alpha: "GU",
          name: "Guam"
        }, {
          alpha: "GT",
          name: "Guatemala"
        }, {
          alpha: "GG",
          name: "Guernsey"
        }, {
          alpha: "GY",
          name: "Guiana"
        }, {
          alpha: "GF",
          name: "Guiana Francesa"
        }, {
          alpha: "GN",
          name: "Guin\xe9"
        }, {
          alpha: "GQ",
          name: "Guin\xe9 Equatorial"
        }, {
          alpha: "GW",
          name: "Guin\xe9-Bissau"
        }, {
          alpha: "HT",
          name: "Haiti"
        }, {
          alpha: "HN",
          name: "Honduras"
        }, {
          alpha: "HK",
          name: "Hong Kong"
        }, {
          alpha: "HU",
          name: "Hungria"
        }, {
          alpha: "YE",
          name: "I\xeamen"
        }, {
          alpha: "BV",
          name: "Ilha Bouvet"
        }, {
          alpha: "CX",
          name: "Ilha Christmas"
        }, {
          alpha: "IM",
          name: "Ilha de Man"
        }, {
          alpha: "HM",
          name: "Ilha Heard e McDonald"
        }, {
          alpha: "NF",
          name: "Ilha Norfolk"
        }, {
          alpha: "KY",
          name: "Ilhas Cayman"
        }, {
          alpha: "CC",
          name: "Ilhas Cocos (Keeling)"
        }, {
          alpha: "CK",
          name: "Ilhas Cook"
        }, {
          alpha: "FK",
          name: "Ilhas Falkland"
        }, {
          alpha: "FO",
          name: "Ilhas Faro\xe9"
        }, {
          alpha: "GS",
          name: "Ilhas Ge\xf3rgia do Sul e Sandwich do Sul"
        }, {
          alpha: "MP",
          name: "Ilhas Marianas do Norte"
        }, {
          alpha: "MH",
          name: "Ilhas Marshall"
        }, {
          alpha: "SB",
          name: "Ilhas Salom\xe3o"
        }, {
          alpha: "SJ",
          name: "Ilhas Svalbard e Jan Mayen"
        }, {
          alpha: "TC",
          name: "Ilhas Turks e Caicos"
        }, {
          alpha: "VG",
          name: "Ilhas Virgens Brit\xe2nicas"
        }, {
          alpha: "VI",
          name: "Ilhas Virgens dos Estados Unidos"
        }, {
          alpha: "WF",
          name: "Ilhas Wallis e Futuna"
        }, {
          alpha: "IN",
          name: "\xcdndia"
        }, {
          alpha: "ID",
          name: "Indon\xe9sia"
        }, {
          alpha: "IR",
          name: "Ir\xe3"
        }, {
          alpha: "IQ",
          name: "Iraque"
        }, {
          alpha: "IE",
          name: "Irlanda"
        }, {
          alpha: "IS",
          name: "Isl\xe2ndia"
        }, {
          alpha: "IL",
          name: "Israel"
        }, {
          alpha: "IT",
          name: "It\xe1lia"
        }, {
          alpha: "JM",
          name: "Jamaica"
        }, {
          alpha: "JP",
          name: "Jap\xe3o"
        }, {
          alpha: "JE",
          name: "Jersey"
        }, {
          alpha: "JO",
          name: "Jord\xe2nia"
        }, {
          alpha: "KI",
          name: "Kiribati"
        }, {
          alpha: "KW",
          name: "Kuwait"
        }, {
          alpha: "LA",
          name: "Laos"
        }, {
          alpha: "LS",
          name: "Lesoto"
        }, {
          alpha: "LV",
          name: "Let\xf4nia"
        }, {
          alpha: "LB",
          name: "L\xedbano"
        }, {
          alpha: "LR",
          name: "Lib\xe9ria"
        }, {
          alpha: "LY",
          name: "L\xedbia"
        }, {
          alpha: "LI",
          name: "Liechtenstein"
        }, {
          alpha: "LT",
          name: "Litu\xe2nia"
        }, {
          alpha: "LU",
          name: "Luxemburgo"
        }, {
          alpha: "MO",
          name: "Macau"
        }, {
          alpha: "MK",
          name: "Maced\xf4nia"
        }, {
          alpha: "MG",
          name: "Madagascar"
        }, {
          alpha: "YT",
          name: "Maiote"
        }, {
          alpha: "MY",
          name: "Mal\xe1sia"
        }, {
          alpha: "MW",
          name: "Malaui"
        }, {
          alpha: "MV",
          name: "Maldivas"
        }, {
          alpha: "ML",
          name: "Mali"
        }, {
          alpha: "MT",
          name: "Malta"
        }, {
          alpha: "MA",
          name: "Marrocos"
        }, {
          alpha: "MQ",
          name: "Martinica"
        }, {
          alpha: "MU",
          name: "Maur\xedcio"
        }, {
          alpha: "MR",
          name: "Maurit\xe2nia"
        }, {
          alpha: "MX",
          name: "M\xe9xico"
        }, {
          alpha: "FM",
          name: "Micron\xe9sia"
        }, {
          alpha: "MZ",
          name: "Mo\xe7ambique"
        }, {
          alpha: "MD",
          name: "Mold\xe1via"
        }, {
          alpha: "MC",
          name: "M\xf4naco"
        }, {
          alpha: "MN",
          name: "Mong\xf3lia"
        }, {
          alpha: "ME",
          name: "Montenegro"
        }, {
          alpha: "MS",
          name: "Montserrat"
        }, {
          alpha: "MM",
          name: "Myanmar"
        }, {
          alpha: "NA",
          name: "Nam\xedbia"
        }, {
          alpha: "NR",
          name: "Nauru"
        }, {
          alpha: "NP",
          name: "Nepal"
        }, {
          alpha: "NI",
          name: "Nicar\xe1gua"
        }, {
          alpha: "NE",
          name: "N\xedger"
        }, {
          alpha: "NG",
          name: "Nig\xe9ria"
        }, {
          alpha: "NU",
          name: "Niue"
        }, {
          alpha: "NO",
          name: "Noruega"
        }, {
          alpha: "NC",
          name: "Nova Caled\xf4nia"
        }, {
          alpha: "NZ",
          name: "Nova Zel\xe2ndia"
        }, {
          alpha: "OM",
          name: "Om\xe3"
        }, {
          alpha: "NL",
          name: "Pa\xedses Baixos"
        }, {
          alpha: "PW",
          name: "Palau"
        }, {
          alpha: "PS",
          name: "Palestina"
        }, {
          alpha: "PA",
          name: "Panam\xe1"
        }, {
          alpha: "PG",
          name: "Papua-Nova Guin\xe9"
        }, {
          alpha: "PK",
          name: "Paquist\xe3o"
        }, {
          alpha: "PY",
          name: "Paraguai"
        }, {
          alpha: "PE",
          name: "Peru"
        }, {
          alpha: "PN",
          name: "Pitcairn"
        }, {
          alpha: "PF",
          name: "Polin\xe9sia Francesa"
        }, {
          alpha: "PL",
          name: "Pol\xf4nia"
        }, {
          alpha: "PR",
          name: "Porto Rico"
        }, {
          alpha: "PT",
          name: "Portugal"
        }, {
          alpha: "KE",
          name: "Qu\xeania"
        }, {
          alpha: "KG",
          name: "Quirguist\xe3o"
        }, {
          alpha: "GB",
          name: "Reino Unido"
        }, {
          alpha: "CF",
          name: "Rep\xfablica Centro-Africana"
        }, {
          alpha: "DO",
          name: "Rep\xfablica Dominicana"
        }, {
          alpha: "CZ",
          name: "Rep\xfablica Tcheca"
        }, {
          alpha: "RE",
          name: "Reuni\xe3o"
        }, {
          alpha: "RO",
          name: "Rom\xeania"
        }, {
          alpha: "RW",
          name: "Ruanda"
        }, {
          alpha: "MF",
          name: "Saint Martin (parte francesa)"
        }, {
          alpha: "WS",
          name: "Samoa"
        }, {
          alpha: "AS",
          name: "Samoa Americana"
        }, {
          alpha: "SH",
          name: "Santa Helena"
        }, {
          alpha: "LC",
          name: "Santa L\xfacia"
        }, {
          alpha: "BL",
          name: "S\xe3o Bartolomeu"
        }, {
          alpha: "KN",
          name: "S\xe3o Crist\xf3v\xe3o e N\xe9vis"
        }, {
          alpha: "SM",
          name: "S\xe3o Marinho"
        }, {
          alpha: "PM",
          name: "S\xe3o Pedro e Miquelon"
        }, {
          alpha: "ST",
          name: "S\xe3o Tom\xe9 e Pr\xedncipe"
        }, {
          alpha: "VC",
          name: "S\xe3o Vicente e Granadinas"
        }, {
          alpha: "SC",
          name: "Seicheles"
        }, {
          alpha: "SN",
          name: "Senegal"
        }, {
          alpha: "SL",
          name: "Serra Leoa"
        }, {
          alpha: "RS",
          name: "S\xe9rvia"
        }, {
          alpha: "SG",
          name: "Singapura"
        }, {
          alpha: "SX",
          name: "Sint Maarten (parte holandesa)"
        }, {
          alpha: "SY",
          name: "S\xedria"
        }, {
          alpha: "SO",
          name: "Som\xe1lia"
        }, {
          alpha: "LK",
          name: "Sri Lanka"
        }, {
          alpha: "SD",
          name: "Sud\xe3o"
        }, {
          alpha: "SS",
          name: "Sud\xe3o do Sul"
        }, {
          alpha: "SE",
          name: "Su\xe9cia"
        }, {
          alpha: "CH",
          name: "Su\xed\xe7a"
        }, {
          alpha: "SR",
          name: "Suriname"
        }, {
          alpha: "TJ",
          name: "Tadjiquist\xe3o"
        }, {
          alpha: "TH",
          name: "Tail\xe2ndia"
        }, {
          alpha: "TW",
          name: "Taiwan"
        }, {
          alpha: "TZ",
          name: "Tanz\xe2nia"
        }, {
          alpha: "IO",
          name: "Territ\xf3rio Brit\xe2nico do Oceano \xcdndico"
        }, {
          alpha: "TF",
          name: "Territ\xf3rios Franceses do Sul"
        }, {
          alpha: "UM",
          name: "Territ\xf3rios Insulares dos Estados Unidos"
        }, {
          alpha: "TL",
          name: "Timor-Leste"
        }, {
          alpha: "TG",
          name: "Togo"
        }, {
          alpha: "TK",
          name: "Tokelau"
        }, {
          alpha: "TO",
          name: "Tonga"
        }, {
          alpha: "TT",
          name: "Trinidad e Tobago"
        }, {
          alpha: "TN",
          name: "Tun\xedsia"
        }, {
          alpha: "TM",
          name: "Turcomenist\xe3o"
        }, {
          alpha: "TR",
          name: "Turquia"
        }, {
          alpha: "TV",
          name: "Tuvalu"
        }, {
          alpha: "UA",
          name: "Ucr\xe2nia"
        }, {
          alpha: "UG",
          name: "Uganda"
        }, {
          alpha: "UY",
          name: "Uruguai"
        }, {
          alpha: "UZ",
          name: "Uzbequist\xe3o"
        }, {
          alpha: "VU",
          name: "Vanuatu"
        }, {
          alpha: "VE",
          name: "Venezuela"
        }, {
          alpha: "VN",
          name: "Vietn\xe3"
        }, {
          alpha: "ZM",
          name: "Z\xe2mbia"
        }, {
          alpha: "ZW",
          name: "Zimb\xe1bue"
        }],
        B = [{
          alpha: "IS",
          name: "\u30A2\u30A4\u30B9\u30E9\u30F3\u30C9"
        }, {
          alpha: "IE",
          name: "\u30A2\u30A4\u30EB\u30E9\u30F3\u30C9"
        }, {
          alpha: "AZ",
          name: "\u30A2\u30BC\u30EB\u30D0\u30A4\u30B8\u30E3\u30F3"
        }, {
          alpha: "AF",
          name: "\u30A2\u30D5\u30AC\u30CB\u30B9\u30BF\u30F3"
        }, {
          alpha: "VI",
          name: "\u30A2\u30E1\u30EA\u30AB\u9818\u30F4\u30A1\u30FC\u30B8\u30F3\u8AF8\u5CF6"
        }, {
          alpha: "AE",
          name: "\u30A2\u30E9\u30D6\u9996\u9577\u56FD\u9023\u90A6"
        }, {
          alpha: "DZ",
          name: "\u30A2\u30EB\u30B8\u30A7\u30EA\u30A2"
        }, {
          alpha: "AR",
          name: "\u30A2\u30EB\u30BC\u30F3\u30C1\u30F3"
        }, {
          alpha: "AW",
          name: "\u30A2\u30EB\u30D0"
        }, {
          alpha: "AL",
          name: "\u30A2\u30EB\u30D0\u30CB\u30A2"
        }, {
          alpha: "AM",
          name: "\u30A2\u30EB\u30E1\u30CB\u30A2"
        }, {
          alpha: "AI",
          name: "\u30A2\u30F3\u30AE\u30E9"
        }, {
          alpha: "AO",
          name: "\u30A2\u30F3\u30B4\u30E9"
        }, {
          alpha: "AG",
          name: "\u30A2\u30F3\u30C6\u30A3\u30B0\u30A2\u30FB\u30D0\u30FC\u30D6\u30FC\u30C0"
        }, {
          alpha: "AD",
          name: "\u30A2\u30F3\u30C9\u30E9"
        }, {
          alpha: "YE",
          name: "\u30A4\u30A8\u30E1\u30F3"
        }, {
          alpha: "IO",
          name: "\u30A4\u30AE\u30EA\u30B9\u9818\u30A4\u30F3\u30C9\u6D0B\u5730\u57DF"
        }, {
          alpha: "VG",
          name: "\u30A4\u30AE\u30EA\u30B9\u9818\u30F4\u30A1\u30FC\u30B8\u30F3\u8AF8\u5CF6"
        }, {
          alpha: "IL",
          name: "\u30A4\u30B9\u30E9\u30A8\u30EB"
        }, {
          alpha: "IT",
          name: "\u30A4\u30BF\u30EA\u30A2"
        }, {
          alpha: "IQ",
          name: "\u30A4\u30E9\u30AF"
        }, {
          alpha: "IR",
          name: "\u30A4\u30E9\u30F3"
        }, {
          alpha: "IN",
          name: "\u30A4\u30F3\u30C9"
        }, {
          alpha: "ID",
          name: "\u30A4\u30F3\u30C9\u30CD\u30B7\u30A2"
        }, {
          alpha: "UG",
          name: "\u30A6\u30AC\u30F3\u30C0"
        }, {
          alpha: "UA",
          name: "\u30A6\u30AF\u30E9\u30A4\u30CA"
        }, {
          alpha: "UZ",
          name: "\u30A6\u30BA\u30D9\u30AD\u30B9\u30BF\u30F3"
        }, {
          alpha: "UY",
          name: "\u30A6\u30EB\u30B0\u30A2\u30A4"
        }, {
          alpha: "EC",
          name: "\u30A8\u30AF\u30A2\u30C9\u30EB"
        }, {
          alpha: "EG",
          name: "\u30A8\u30B8\u30D7\u30C8"
        }, {
          alpha: "EE",
          name: "\u30A8\u30B9\u30C8\u30CB\u30A2"
        }, {
          alpha: "ET",
          name: "\u30A8\u30C1\u30AA\u30D4\u30A2"
        }, {
          alpha: "ER",
          name: "\u30A8\u30EA\u30C8\u30EA\u30A2"
        }, {
          alpha: "SV",
          name: "\u30A8\u30EB\u30B5\u30EB\u30D0\u30C9\u30EB"
        }, {
          alpha: "AU",
          name: "\u30AA\u30FC\u30B9\u30C8\u30E9\u30EA\u30A2"
        }, {
          alpha: "AT",
          name: "\u30AA\u30FC\u30B9\u30C8\u30EA\u30A2"
        }, {
          alpha: "AX",
          name: "\u30AA\u30FC\u30E9\u30F3\u30C9\u8AF8\u5CF6"
        }, {
          alpha: "OM",
          name: "\u30AA\u30DE\u30FC\u30F3"
        }, {
          alpha: "NL",
          name: "\u30AA\u30E9\u30F3\u30C0"
        }, {
          alpha: "GH",
          name: "\u30AC\u30FC\u30CA"
        }, {
          alpha: "CV",
          name: "\u30AB\u30FC\u30DC\u30D9\u30EB\u30C7"
        }, {
          alpha: "GG",
          name: "\u30AC\u30FC\u30F3\u30B8\u30FC\u5CF6"
        }, {
          alpha: "GY",
          name: "\u30AC\u30A4\u30A2\u30CA"
        }, {
          alpha: "KZ",
          name: "\u30AB\u30B6\u30D5\u30B9\u30BF\u30F3"
        }, {
          alpha: "QA",
          name: "\u30AB\u30BF\u30FC\u30EB"
        }, {
          alpha: "CA",
          name: "\u30AB\u30CA\u30C0"
        }, {
          alpha: "GA",
          name: "\u30AC\u30DC\u30F3"
        }, {
          alpha: "CM",
          name: "\u30AB\u30E1\u30EB\u30FC\u30F3"
        }, {
          alpha: "GM",
          name: "\u30AC\u30F3\u30D3\u30A2"
        }, {
          alpha: "KH",
          name: "\u30AB\u30F3\u30DC\u30B8\u30A2"
        }, {
          alpha: "GN",
          name: "\u30AE\u30CB\u30A2"
        }, {
          alpha: "GW",
          name: "\u30AE\u30CB\u30A2\u30D3\u30B5\u30A6"
        }, {
          alpha: "CY",
          name: "\u30AD\u30D7\u30ED\u30B9"
        }, {
          alpha: "CW",
          name: "\u30AD\u30E5\u30E9\u30BD\u30FC\u5CF6"
        }, {
          alpha: "GR",
          name: "\u30AE\u30EA\u30B7\u30E3"
        }, {
          alpha: "KI",
          name: "\u30AD\u30EA\u30D0\u30B9"
        }, {
          alpha: "KG",
          name: "\u30AD\u30EB\u30AE\u30B9\u30BF\u30F3"
        }, {
          alpha: "GT",
          name: "\u30B0\u30A2\u30C6\u30DE\u30E9"
        }, {
          alpha: "GP",
          name: "\u30B0\u30A2\u30C9\u30EB\u30FC\u30D7\u5CF6"
        }, {
          alpha: "GU",
          name: "\u30B0\u30A2\u30E0\u5CF6"
        }, {
          alpha: "KW",
          name: "\u30AF\u30A6\u30A7\u30FC\u30C8"
        }, {
          alpha: "CK",
          name: "\u30AF\u30C3\u30AF\u8AF8\u5CF6"
        }, {
          alpha: "GL",
          name: "\u30B0\u30EA\u30FC\u30F3\u30E9\u30F3\u30C9"
        }, {
          alpha: "CX",
          name: "\u30AF\u30EA\u30B9\u30DE\u30B9\u5CF6"
        }, {
          alpha: "GD",
          name: "\u30B0\u30EC\u30CA\u30C0"
        }, {
          alpha: "HR",
          name: "\u30AF\u30ED\u30A2\u30C1\u30A2"
        }, {
          alpha: "KY",
          name: "\u30B1\u30A4\u30DE\u30F3\u8AF8\u5CF6"
        }, {
          alpha: "KE",
          name: "\u30B1\u30CB\u30A2"
        }, {
          alpha: "CI",
          name: "\u30B3\u30FC\u30C8\u30B8\u30DC\u30A2\u30FC\u30EB"
        }, {
          alpha: "CC",
          name: "\u30B3\u30B3\u30B9\u8AF8\u5CF6"
        }, {
          alpha: "CR",
          name: "\u30B3\u30B9\u30BF\u30EA\u30AB"
        }, {
          alpha: "KM",
          name: "\u30B3\u30E2\u30ED"
        }, {
          alpha: "CO",
          name: "\u30B3\u30ED\u30F3\u30D3\u30A2"
        }, {
          alpha: "CD",
          name: "\u30B3\u30F3\u30B4 (\u30AD\u30F3\u30B7\u30E3\u30B5)"
        }, {
          alpha: "CG",
          name: "\u30B3\u30F3\u30B4 (\u30D6\u30E9\u30B6\u30D3\u30EB)"
        }, {
          alpha: "SA",
          name: "\u30B5\u30A6\u30B8\u30A2\u30E9\u30D3\u30A2"
        }, {
          alpha: "GS",
          name: "\u30B5\u30A6\u30B9\u30B8\u30E7\u30FC\u30B8\u30A2\u5CF6\u3068\u30B5\u30A6\u30B9\u30B5\u30F3\u30C9\u30A6\u30A3\u30C3\u30C1\u8AF8\u5CF6"
        }, {
          alpha: "WS",
          name: "\u30B5\u30E2\u30A2"
        }, {
          alpha: "ST",
          name: "\u30B5\u30F3\u30C8\u30E1\u30FB\u30D7\u30EA\u30F3\u30B7\u30DA"
        }, {
          alpha: "ZM",
          name: "\u30B6\u30F3\u30D3\u30A2"
        }, {
          alpha: "PM",
          name: "\u30B5\u30F3\u30D4\u30A8\u30FC\u30EB\u5CF6\u304A\u3088\u3073\u30DF\u30AF\u30ED\u30F3\u5CF6"
        }, {
          alpha: "SM",
          name: "\u30B5\u30F3\u30DE\u30EA\u30CE"
        }, {
          alpha: "MF",
          name: "\u30B5\u30F3\u30DE\u30EB\u30BF\u30F3\u5CF6 (\u30D5\u30E9\u30F3\u30B9\u9818)"
        }, {
          alpha: "SL",
          name: "\u30B7\u30A8\u30E9\u30EC\u30AA\u30CD"
        }, {
          alpha: "DJ",
          name: "\u30B8\u30D6\u30C1"
        }, {
          alpha: "GI",
          name: "\u30B8\u30D6\u30E9\u30EB\u30BF\u30EB"
        }, {
          alpha: "JE",
          name: "\u30B8\u30E3\u30FC\u30B8\u30FC\u5CF6"
        }, {
          alpha: "JM",
          name: "\u30B8\u30E3\u30DE\u30A4\u30AB"
        }, {
          alpha: "GE",
          name: "\u30B8\u30E7\u30FC\u30B8\u30A2"
        }, {
          alpha: "SY",
          name: "\u30B7\u30EA\u30A2"
        }, {
          alpha: "SG",
          name: "\u30B7\u30F3\u30AC\u30DD\u30FC\u30EB"
        }, {
          alpha: "SX",
          name: "\u30B7\u30F3\u30C8\u30FB\u30DE\u30FC\u30EB\u30C6\u30F3 (\u30AA\u30E9\u30F3\u30C0\u9818)"
        }, {
          alpha: "ZW",
          name: "\u30B8\u30F3\u30D0\u30D6\u30A8"
        }, {
          alpha: "SD",
          name: "\u30B9\u30FC\u30C0\u30F3"
        }, {
          alpha: "CH",
          name: "\u30B9\u30A4\u30B9"
        }, {
          alpha: "SJ",
          name: "\u30B9\u30F4\u30A1\u30FC\u30EB\u30D0\u30EB\u8AF8\u5CF6\u304A\u3088\u3073\u30E4\u30F3\u30DE\u30A4\u30A8\u30F3\u5CF6"
        }, {
          alpha: "SE",
          name: "\u30B9\u30A6\u30A7\u30FC\u30C7\u30F3"
        }, {
          alpha: "ES",
          name: "\u30B9\u30DA\u30A4\u30F3"
        }, {
          alpha: "SR",
          name: "\u30B9\u30EA\u30CA\u30E0"
        }, {
          alpha: "LK",
          name: "\u30B9\u30EA\u30E9\u30F3\u30AB"
        }, {
          alpha: "SK",
          name: "\u30B9\u30ED\u30D0\u30AD\u30A2"
        }, {
          alpha: "SI",
          name: "\u30B9\u30ED\u30D9\u30CB\u30A2"
        }, {
          alpha: "SZ",
          name: "\u30B9\u30EF\u30B8\u30E9\u30F3\u30C9"
        }, {
          alpha: "SC",
          name: "\u30BB\u30A4\u30B7\u30A7\u30EB"
        }, {
          alpha: "SN",
          name: "\u30BB\u30CD\u30AC\u30EB"
        }, {
          alpha: "RS",
          name: "\u30BB\u30EB\u30D3\u30A2"
        }, {
          alpha: "SH",
          name: "\u30BB\u30F3\u30C8\u30FB\u30D8\u30EC\u30CA\u5CF6"
        }, {
          alpha: "KN",
          name: "\u30BB\u30F3\u30C8\u30AF\u30EA\u30B9\u30C8\u30D5\u30A1\u30FC\u30FB\u30CD\u30A4\u30D3\u30B9"
        }, {
          alpha: "BL",
          name: "\u30BB\u30F3\u30C8\u30D0\u30FC\u30C4\u5CF6"
        }, {
          alpha: "VC",
          name: "\u30BB\u30F3\u30C8\u30D3\u30F3\u30BB\u30F3\u30C8\u304A\u3088\u3073\u30B0\u30EC\u30CA\u30C7\u30A3\u30FC\u30F3\u8AF8\u5CF6"
        }, {
          alpha: "LC",
          name: "\u30BB\u30F3\u30C8\u30EB\u30B7\u30A2"
        }, {
          alpha: "SO",
          name: "\u30BD\u30DE\u30EA\u30A2"
        }, {
          alpha: "SB",
          name: "\u30BD\u30ED\u30E2\u30F3\u8AF8\u5CF6"
        }, {
          alpha: "TC",
          name: "\u30BF\u30FC\u30AF\u30B9\u30FB\u30AB\u30A4\u30B3\u30B9\u8AF8\u5CF6"
        }, {
          alpha: "TH",
          name: "\u30BF\u30A4"
        }, {
          alpha: "TJ",
          name: "\u30BF\u30B8\u30AD\u30B9\u30BF\u30F3"
        }, {
          alpha: "TZ",
          name: "\u30BF\u30F3\u30B6\u30CB\u30A2"
        }, {
          alpha: "CZ",
          name: "\u30C1\u30A7\u30B3\u5171\u548C\u56FD"
        }, {
          alpha: "TD",
          name: "\u30C1\u30E3\u30C9"
        }, {
          alpha: "TN",
          name: "\u30C1\u30E5\u30CB\u30B8\u30A2"
        }, {
          alpha: "CL",
          name: "\u30C1\u30EA"
        }, {
          alpha: "TV",
          name: "\u30C4\u30D0\u30EB"
        }, {
          alpha: "DK",
          name: "\u30C7\u30F3\u30DE\u30FC\u30AF"
        }, {
          alpha: "TG",
          name: "\u30C8\u30FC\u30B4"
        }, {
          alpha: "DE",
          name: "\u30C9\u30A4\u30C4"
        }, {
          alpha: "TK",
          name: "\u30C8\u30B1\u30E9\u30A6\u8AF8\u5CF6"
        }, {
          alpha: "DM",
          name: "\u30C9\u30DF\u30CB\u30AB"
        }, {
          alpha: "DO",
          name: "\u30C9\u30DF\u30CB\u30AB\u5171\u548C\u56FD"
        }, {
          alpha: "TT",
          name: "\u30C8\u30EA\u30CB\u30C0\u30FC\u30C9\u30FB\u30C8\u30D0\u30B4"
        }, {
          alpha: "TM",
          name: "\u30C8\u30EB\u30AF\u30E1\u30CB\u30B9\u30BF\u30F3"
        }, {
          alpha: "TR",
          name: "\u30C8\u30EB\u30B3"
        }, {
          alpha: "TO",
          name: "\u30C8\u30F3\u30AC"
        }, {
          alpha: "NG",
          name: "\u30CA\u30A4\u30B8\u30A7\u30EA\u30A2"
        }, {
          alpha: "NR",
          name: "\u30CA\u30A6\u30EB"
        }, {
          alpha: "NA",
          name: "\u30CA\u30DF\u30D3\u30A2"
        }, {
          alpha: "NU",
          name: "\u30CB\u30A6\u30A8"
        }, {
          alpha: "NI",
          name: "\u30CB\u30AB\u30E9\u30B0\u30A2"
        }, {
          alpha: "NE",
          name: "\u30CB\u30B8\u30A7\u30FC\u30EB"
        }, {
          alpha: "NZ",
          name: "\u30CB\u30E5\u30FC\u30B8\u30FC\u30E9\u30F3\u30C9"
        }, {
          alpha: "NP",
          name: "\u30CD\u30D1\u30FC\u30EB"
        }, {
          alpha: "NF",
          name: "\u30CE\u30FC\u30D5\u30A9\u30FC\u30AF\u5CF6"
        }, {
          alpha: "NO",
          name: "\u30CE\u30EB\u30A6\u30A7\u30FC"
        }, {
          alpha: "HM",
          name: "\u30CF\u30FC\u30C9\u5CF6\u3068\u30DE\u30AF\u30C9\u30CA\u30EB\u30C9\u8AF8\u5CF6"
        }, {
          alpha: "BH",
          name: "\u30D0\u30FC\u30EC\u30FC\u30F3"
        }, {
          alpha: "HT",
          name: "\u30CF\u30A4\u30C1"
        }, {
          alpha: "PK",
          name: "\u30D1\u30AD\u30B9\u30BF\u30F3"
        }, {
          alpha: "VA",
          name: "\u30D0\u30C1\u30AB\u30F3\u5E02\u56FD"
        }, {
          alpha: "PA",
          name: "\u30D1\u30CA\u30DE"
        }, {
          alpha: "VU",
          name: "\u30D0\u30CC\u30A2\u30C4"
        }, {
          alpha: "BS",
          name: "\u30D0\u30CF\u30DE"
        }, {
          alpha: "PG",
          name: "\u30D1\u30D7\u30A2\u30FB\u30CB\u30E5\u30FC\u30AE\u30CB\u30A2"
        }, {
          alpha: "BM",
          name: "\u30D0\u30DF\u30E5\u30FC\u30C0\u8AF8\u5CF6"
        }, {
          alpha: "PW",
          name: "\u30D1\u30E9\u30AA"
        }, {
          alpha: "PY",
          name: "\u30D1\u30E9\u30B0\u30A2\u30A4"
        }, {
          alpha: "BB",
          name: "\u30D0\u30EB\u30D0\u30C9\u30B9"
        }, {
          alpha: "PS",
          name: "\u30D1\u30EC\u30B9\u30C1\u30CA"
        }, {
          alpha: "HU",
          name: "\u30CF\u30F3\u30AC\u30EA\u30FC"
        }, {
          alpha: "BD",
          name: "\u30D0\u30F3\u30B0\u30E9\u30C7\u30B7\u30E5"
        }, {
          alpha: "PN",
          name: "\u30D4\u30C8\u30B1\u30A2\u30F3\u5CF6"
        }, {
          alpha: "BV",
          name: "\u30D6\u30FC\u30F4\u30A7\u5CF6"
        }, {
          alpha: "BT",
          name: "\u30D6\u30FC\u30BF\u30F3"
        }, {
          alpha: "FJ",
          name: "\u30D5\u30A3\u30B8\u30FC"
        }, {
          alpha: "PH",
          name: "\u30D5\u30A3\u30EA\u30D4\u30F3"
        }, {
          alpha: "FI",
          name: "\u30D5\u30A3\u30F3\u30E9\u30F3\u30C9"
        }, {
          alpha: "PR",
          name: "\u30D7\u30A8\u30EB\u30C8\u30EA\u30B3"
        }, {
          alpha: "FO",
          name: "\u30D5\u30A7\u30ED\u30FC\u8AF8\u5CF6"
        }, {
          alpha: "FK",
          name: "\u30D5\u30A9\u30FC\u30AF\u30E9\u30F3\u30C9\u8AF8\u5CF6"
        }, {
          alpha: "BR",
          name: "\u30D6\u30E9\u30B8\u30EB"
        }, {
          alpha: "FR",
          name: "\u30D5\u30E9\u30F3\u30B9"
        }, {
          alpha: "GF",
          name: "\u30D5\u30E9\u30F3\u30B9\u9818\u30AE\u30A2\u30CA"
        }, {
          alpha: "NC",
          name: "\u30D5\u30E9\u30F3\u30B9\u9818\u30CB\u30E5\u30FC\u30AB\u30EC\u30C9\u30CB\u30A2"
        }, {
          alpha: "PF",
          name: "\u30D5\u30E9\u30F3\u30B9\u9818\u30DD\u30EA\u30CD\u30B7\u30A2"
        }, {
          alpha: "TF",
          name: "\u30D5\u30E9\u30F3\u30B9\u9818\u5357\u65B9\u30FB\u5357\u6975\u5730\u57DF"
        }, {
          alpha: "BG",
          name: "\u30D6\u30EB\u30AC\u30EA\u30A2"
        }, {
          alpha: "BF",
          name: "\u30D6\u30EB\u30AD\u30CA\u30D5\u30A1\u30BD"
        }, {
          alpha: "BN",
          name: "\u30D6\u30EB\u30CD\u30A4"
        }, {
          alpha: "BI",
          name: "\u30D6\u30EB\u30F3\u30B8"
        }, {
          alpha: "VN",
          name: "\u30D9\u30C8\u30CA\u30E0"
        }, {
          alpha: "BJ",
          name: "\u30D9\u30CA\u30F3"
        }, {
          alpha: "VE",
          name: "\u30D9\u30CD\u30BA\u30A8\u30E9"
        }, {
          alpha: "BY",
          name: "\u30D9\u30E9\u30EB\u30FC\u30B7"
        }, {
          alpha: "BZ",
          name: "\u30D9\u30EA\u30FC\u30BA"
        }, {
          alpha: "PE",
          name: "\u30DA\u30EB\u30FC"
        }, {
          alpha: "BE",
          name: "\u30D9\u30EB\u30AE\u30FC"
        }, {
          alpha: "PL",
          name: "\u30DD\u30FC\u30E9\u30F3\u30C9"
        }, {
          alpha: "BA",
          name: "\u30DC\u30B9\u30CB\u30A2\u30FB\u30D8\u30EB\u30C4\u30A7\u30B4\u30D3\u30CA"
        }, {
          alpha: "BW",
          name: "\u30DC\u30C4\u30EF\u30CA"
        }, {
          alpha: "BQ",
          name: "\u30DC\u30CD\u30FC\u30EB\u3001\u30B7\u30F3\u30C8\u30FB\u30E6\u30FC\u30B9\u30BF\u30C6\u30A3\u30A6\u30B9\u304A\u3088\u3073\u30B5\u30D0"
        }, {
          alpha: "BO",
          name: "\u30DC\u30EA\u30D3\u30A2"
        }, {
          alpha: "PT",
          name: "\u30DD\u30EB\u30C8\u30AC\u30EB"
        }, {
          alpha: "HN",
          name: "\u30DB\u30F3\u30B8\u30E5\u30E9\u30B9"
        }, {
          alpha: "MH",
          name: "\u30DE\u30FC\u30B7\u30E3\u30EB\u8AF8\u5CF6"
        }, {
          alpha: "MO",
          name: "\u30DE\u30AB\u30AA"
        }, {
          alpha: "MK",
          name: "\u30DE\u30B1\u30C9\u30CB\u30A2"
        }, {
          alpha: "MG",
          name: "\u30DE\u30C0\u30AC\u30B9\u30AB\u30EB"
        }, {
          alpha: "YT",
          name: "\u30DE\u30E8\u30C3\u30C8\u5CF6"
        }, {
          alpha: "MW",
          name: "\u30DE\u30E9\u30A6\u30A3"
        }, {
          alpha: "ML",
          name: "\u30DE\u30EA"
        }, {
          alpha: "MT",
          name: "\u30DE\u30EB\u30BF"
        }, {
          alpha: "MQ",
          name: "\u30DE\u30EB\u30C6\u30A3\u30CB\u30FC\u30AF\u5CF6"
        }, {
          alpha: "MY",
          name: "\u30DE\u30EC\u30FC\u30B7\u30A2"
        }, {
          alpha: "IM",
          name: "\u30DE\u30F3\u5CF6"
        }, {
          alpha: "FM",
          name: "\u30DF\u30AF\u30ED\u30CD\u30B7\u30A2\u9023\u90A6"
        }, {
          alpha: "MM",
          name: "\u30DF\u30E3\u30F3\u30DE\u30FC"
        }, {
          alpha: "MX",
          name: "\u30E1\u30AD\u30B7\u30B3"
        }, {
          alpha: "MU",
          name: "\u30E2\u30FC\u30EA\u30B7\u30E3\u30B9"
        }, {
          alpha: "MR",
          name: "\u30E2\u30FC\u30EA\u30BF\u30CB\u30A2"
        }, {
          alpha: "MZ",
          name: "\u30E2\u30B6\u30F3\u30D3\u30FC\u30AF"
        }, {
          alpha: "MC",
          name: "\u30E2\u30CA\u30B3"
        }, {
          alpha: "MV",
          name: "\u30E2\u30EB\u30C7\u30A3\u30D6"
        }, {
          alpha: "MD",
          name: "\u30E2\u30EB\u30C9\u30D0"
        }, {
          alpha: "MA",
          name: "\u30E2\u30ED\u30C3\u30B3"
        }, {
          alpha: "MN",
          name: "\u30E2\u30F3\u30B4\u30EB"
        }, {
          alpha: "ME",
          name: "\u30E2\u30F3\u30C6\u30CD\u30B0\u30ED"
        }, {
          alpha: "MS",
          name: "\u30E2\u30F3\u30C8\u30BB\u30E9\u30C8\u5CF6"
        }, {
          alpha: "JO",
          name: "\u30E8\u30EB\u30C0\u30F3"
        }, {
          alpha: "LA",
          name: "\u30E9\u30AA\u30B9"
        }, {
          alpha: "LV",
          name: "\u30E9\u30C8\u30D3\u30A2"
        }, {
          alpha: "LT",
          name: "\u30EA\u30C8\u30A2\u30CB\u30A2"
        }, {
          alpha: "LY",
          name: "\u30EA\u30D3\u30A2"
        }, {
          alpha: "LI",
          name: "\u30EA\u30D2\u30C6\u30F3\u30B7\u30E5\u30BF\u30A4\u30F3"
        }, {
          alpha: "LR",
          name: "\u30EA\u30D9\u30EA\u30A2"
        }, {
          alpha: "RO",
          name: "\u30EB\u30FC\u30DE\u30CB\u30A2"
        }, {
          alpha: "LU",
          name: "\u30EB\u30AF\u30BB\u30F3\u30D6\u30EB\u30AF"
        }, {
          alpha: "RW",
          name: "\u30EB\u30EF\u30F3\u30C0"
        }, {
          alpha: "LS",
          name: "\u30EC\u30BD\u30C8"
        }, {
          alpha: "LB",
          name: "\u30EC\u30D0\u30CE\u30F3"
        }, {
          alpha: "RE",
          name: "\u30EC\u30E6\u30CB\u30AA\u30F3"
        }, {
          alpha: "WF",
          name: "\u30EF\u30EA\u30FC\u30FB\u30A8\u30FB\u30D5\u30C8\u30A5\u30FC\u30CA\u8AF8\u5CF6"
        }, {
          alpha: "CN",
          name: "\u4E2D\u56FD"
        }, {
          alpha: "CF",
          name: "\u4E2D\u592E\u30A2\u30D5\u30EA\u30AB\u5171\u548C\u56FD"
        }, {
          alpha: "MP",
          name: "\u5317\u30DE\u30EA\u30A2\u30CA\u8AF8\u5CF6"
        }, {
          alpha: "ZA",
          name: "\u5357\u30A2\u30D5\u30EA\u30AB"
        }, {
          alpha: "SS",
          name: "\u5357\u30B9\u30FC\u30C0\u30F3"
        }, {
          alpha: "AQ",
          name: "\u5357\u6975\u5927\u9678"
        }, {
          alpha: "TW",
          name: "\u53F0\u6E7E"
        }, {
          alpha: "UM",
          name: "\u5408\u8846\u56FD\u9818\u6709\u5C0F\u96E2\u5CF6"
        }, {
          alpha: "JP",
          name: "\u65E5\u672C"
        }, {
          alpha: "TL",
          name: "\u6771\u30C6\u30A3\u30E2\u30FC\u30EB"
        }, {
          alpha: "AS",
          name: "\u7C73\u30B5\u30E2\u30A2"
        }, {
          alpha: "US",
          name: "\u7C73\u56FD"
        }, {
          alpha: "GB",
          name: "\u82F1\u56FD"
        }, {
          alpha: "GQ",
          name: "\u8D64\u9053\u30AE\u30CB\u30A2"
        }, {
          alpha: "KR",
          name: "\u97D3\u56FD"
        }, {
          alpha: "HK",
          name: "\u9999\u6E2F"
        }],
        P = [{
          schema: s.Yj().min(1),
          message: (0, u.t)("Please select your country/region")
        }],
        R = () => {
          let a = "country-validation-msg",
            e = (0, r.use)(d),
            n = e?.errors.country,
            {
              selectedCountry: i,
              setSelectedCountry: t
            } = (0, r.use)(v.G),
            h = (0, r.use)(v.G),
            o = (0, u.JK)(),
            s = (0, r.useMemo)(() => {
              switch (o) {
                case "es":
                  return E;
                case "ko":
                  return A;
                case "pt":
                  return L;
                case "ja":
                  return B;
                default:
                  return h.marketingTargetedCountries || []
              }
            }, [h.marketingTargetedCountries, o]),
            c = (0, r.useCallback)(a => {
              let e = a.target.value;
              t(s.find(a => a.alpha === e) || null)
            }, [s, t]);
          return (0, l.jsxs)(m.FormControl, {
            id: "form-field-country",
            validationStatus: "string" == typeof n ? "error" : void 0,
            fullWidth: !0,
            required: !0,
            children: [(0, l.jsx)(m.FormControl.Label, {
              children: (0, u.t)("Country")
            }), (0, l.jsxs)(m.Select, {
              ...e?.register("country", {
                label: "Country",
                required: !0,
                validations: P
              }),
              ...(0, p.$C)({
                action: "country",
                tag: "select",
                context: "form_control",
                location: "form"
              }),
              "aria-describedby": a,
              onChange: c,
              value: i?.alpha || "",
              children: [(0, l.jsx)(m.Select.Option, {
                value: "",
                children: (0, u.t)("Choose your country/region")
              }), s.map(a => (0, l.jsx)(m.Select.Option, {
                value: a.alpha,
                children: a.name
              }, a.name))]
            }), "string" == typeof n ? (0, l.jsx)(m.FormControl.Validation, {
              id: a,
              children: n
            }) : null]
          })
        };
      R.displayName = "CountrySelectField";
      let k = a => {
        let {
          onSubmit: e,
          children: n,
          ...i
        } = a;
        return (0, l.jsx)("form", {
          noValidate: !0,
          onSubmit: e,
          ...i,
          children: n
        })
      };
      k.displayName = "Root";
      let H = ({
        children: a,
        ...e
      }) => (0, l.jsx)(m.Heading, {
        as: "h4",
        ...e,
        children: a
      });
      H.displayName = "FormHeading";
      let U = a => {
        let {
          children: e,
          ...n
        } = a;
        return (0, l.jsx)(m.Button, {
          variant: "primary",
          type: "submit",
          ...n,
          children: a.children
        })
      };
      U.displayName = "FormSubmit";
      let V = () => {
        let a = (0, r.use)(d);
        return (0, l.jsxs)(c.H, {
          hidden: void 0 === a || 0 === Object.keys(a.errors).length,
          variant: "error",
          children: [(0, l.jsx)(m.Text, {
            as: "p",
            weight: "semibold",
            size: "200",
            children: "The following fields have errors:"
          }), (0, l.jsx)(m.Text, {
            as: "p",
            size: "200",
            children: Object.keys(a?.errors ?? []).map((e, n, i) => {
              let t = a?.formFields[e];
              if (void 0 === t) return null;
              let m = n === i.length - 1,
                h = t.label ?? t.name;
              return (0, l.jsxs)(r.Fragment, {
                children: [(0, l.jsx)("a", {
                  href: `#${t.id}`,
                  className: "Form-module__FormErrorsItem__S6thp",
                  ...(0, p.$C)({
                    action: h,
                    tag: "hyperlink",
                    context: "form_errors",
                    location: "form"
                  }),
                  children: h
                }), !m && ", "]
              }, t.name)
            })
          })]
        })
      };
      V.displayName = "FormErrors";
      let O = () => {
        let a = "octocaptcha-token",
          e = (0, r.useRef)(null),
          n = (0, r.use)(d),
          i = n?.register(a, {
            label: "CAPTCHA",
            required: !0,
            validations: [{
              message: (0, u.t)("Please complete the CAPTCHA."),
              schema: s.Yj().min(1)
            }]
          }),
          t = n?.errors[a];
        return (0, l.jsxs)(m.FormControl, {
          id: i?.id,
          validationStatus: "string" == typeof t ? "error" : void 0,
          children: [(0, l.jsx)(j, {
            onComplete: a => {
              if (null !== e.current) {
                let n = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value")?.set;
                n?.call(e.current, a.token), e.current.dispatchEvent(new Event("input", {
                  bubbles: !0
                }))
              }
            }
          }), (0, l.jsx)("input", {
            name: i?.name,
            onChange: i?.onChange,
            ref: e,
            style: {
              display: "none"
            }
          }), "string" == typeof t ? (0, l.jsx)(m.FormControl.Validation, {
            children: t
          }) : null]
        })
      };
      O.displayName = "FormOctocaptcha";
      let K = a => (0, l.jsx)(N, {
        ...a
      });
      K.displayName = "FormConsentExperience";
      let D = Object.assign(k, {
        Errors: V,
        Heading: H,
        Octocaptcha: O,
        ConsentExperience: K,
        Submit: U,
        CountrySelectField: R
      });
      var w = n(79926),
        _ = n(51367),
        W = n(82520),
        Y = n(83174),
        Z = n(58015);
      let $ = RegExp("@(gmail|yahoo|hotmail|aol|msn|orange|comcast|live|outlook|yandex|me|icloud|verizon|fastmail)\\.(com|co\\.uk|fr|net|fm|ru)$"),
        q = {
          REQUIRED: {
            message: (0, u.t)("This field is required."),
            schema: s.Yj().trim().min(1)
          },
          WORK_EMAIL_ONLY: {
            message: (0, u.t)("Please enter a valid work email address."),
            schema: s.Rp().refine(a => !$.test(a), {
              message: (0, u.t)("The email is from a personal email provider.")
            })
          },
          EMAIL: {
            message: (0, u.t)("Please enter a valid email address."),
            schema: s.Rp()
          },
          PHONE: {
            message: (0, u.t)("Please enter a valid phone number."),
            schema: s.Yj().trim().refine(a => {
              let e = (0, Z.l)(a, {
                extract: !1
              });
              return void 0 !== e && e.isPossible()
            })
          }
        };

      function J(a) {
        let e = q[a.fields.name],
          n = a.fields.errorMessage;
        return "string" == typeof n && n.trim().length > 0 ? {
          ...e,
          message: n
        } : e
      }

      function z(a) {
        let e = e => a.fields.validations?.some(({
          fields: {
            name: a
          }
        }) => a === e);
        return e("EMAIL") || e("WORK_EMAIL_ONLY") ? "email" : e("PHONE") ? "tel" : "text"
      }
      var Q = n(61715),
        X = n(58172);
      let aa = a => {
        let {
          id: e,
          label: n,
          error: i,
          required: t,
          placeholder: h,
          validationErrorId: o,
          onChange: p,
          allowedCountries: s
        } = a, d = (0, r.useMemo)(() => new Set((0, Q.X)()), []), c = (0, r.useMemo)(() => s && s.length > 0 ? s.filter(a => d.has(a.alpha)) : (0, Q.X)().map(a => ({
          name: a,
          alpha: a
        })), [s, d]), [u, f] = (0, r.useState)("US"), [g, C] = (0, r.useState)(""), S = (0, r.useRef)(null), x = a => {
          if (S.current) {
            let e = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value")?.set;
            e?.call(S.current, a), S.current.dispatchEvent(new Event("input", {
              bubbles: !0
            }))
          }
        };
        return (0, l.jsxs)(m.FormControl, {
          id: e,
          fullWidth: !0,
          required: t,
          validationStatus: "string" == typeof i ? "error" : void 0,
          children: [(0, l.jsx)(m.FormControl.Label, {
            children: n
          }), (0, l.jsxs)(m.Stack, {
            direction: "horizontal",
            alignItems: "flex-start",
            padding: "none",
            style: {
              width: "100%"
            },
            children: [(0, l.jsx)(m.Box, {
              style: {
                flex: 5,
                minWidth: 0
              },
              children: (0, l.jsx)(m.Select, {
                value: u,
                onChange: a => {
                  f(a.target.value), C(""), x("")
                },
                "aria-label": "Select country for phone number",
                children: c.map(a => (0, l.jsxs)(m.Select.Option, {
                  value: a.alpha,
                  children: [a.name, " (", `+${(0,X.K)(a.alpha)}`, ")"]
                }, a.alpha))
              })
            }), (0, l.jsx)(m.Box, {
              style: {
                flex: 5,
                minWidth: 0
              },
              children: (0, l.jsx)(m.TextInput, {
                id: e,
                value: g,
                onChange: a => {
                  let e = a.target.value;
                  if (C(e), "" === a.target.value.trim()) return void x("");
                  let n = e.replace(/\D/g, ""),
                    l = `+${(0,X.K)(u)}${n}`,
                    i = (0, Z.l)(n, u);
                  x(i && i.isPossible() ? i.format("E.164") : l)
                },
                "aria-describedby": o,
                "aria-label": n,
                placeholder: h,
                type: "tel",
                fullWidth: !0,
                validationStatus: "string" == typeof g && "" === g.trim() ? void 0 : "string" == typeof i ? "error" : void 0,
                leadingText: `+${(0,X.K)(u)}`
              })
            })]
          }), (0, l.jsx)("input", {
            name: a.name,
            style: {
              display: "none"
            },
            onChange: p,
            ref: S
          }), "string" == typeof i ? (0, l.jsx)(m.FormControl.Validation, {
            id: o,
            children: i
          }) : null]
        }, e)
      };

      function ae({
        component: a
      }) {
        let e = (0, r.use)(d),
          n = (0, r.use)(v.G);
        if (void 0 === e) throw Error("ERROR: form context is undefined for ContentfulTextInput");
        let i = a.fields.validations?.some(a => "REQUIRED" === a.fields.name) ?? !1,
          t = a.fields.validations?.map(J) ?? [],
          h = e.errors[a.fields.htmlName],
          o = `${a.fields.htmlName}-validation-msg`,
          {
            id: s,
            ...c
          } = e.register(a.fields.htmlName, {
            label: a.fields.label,
            required: i,
            validations: t
          });
        return "tel" === z(a) ? (0, l.jsx)(aa, {
          id: s,
          onChange: c.onChange,
          error: h,
          required: i,
          placeholder: a.fields.placeholder,
          validationErrorId: o,
          label: a.fields.label,
          name: c.name,
          allowedCountries: n.marketingTargetedCountries?.length ? n.marketingTargetedCountries : void 0
        }) : (0, l.jsxs)(m.FormControl, {
          id: s,
          fullWidth: !0,
          required: i,
          validationStatus: "string" == typeof h ? "error" : void 0,
          children: [(0, l.jsx)(m.FormControl.Label, {
            children: a.fields.label
          }), (0, l.jsx)(m.TextInput, {
            ...c,
            ...(0, p.$C)({
              action: a.fields.label,
              tag: "input",
              context: "form_control",
              location: "form"
            }),
            "aria-describedby": o,
            placeholder: a.fields.placeholder,
            type: z(a)
          }), "string" == typeof h ? (0, l.jsx)(m.FormControl.Validation, {
            id: o,
            children: h
          }) : null]
        }, a.fields.htmlName)
      }

      function an({
        component: a
      }) {
        let e = (0, r.use)(d);
        if (void 0 === e) throw Error("ERROR: form context is undefined for ContentfulSelectInput");
        let n = a.fields.validations?.some(a => "REQUIRED" === a.fields.name) ?? !1,
          i = a.fields.validations?.map(J) ?? [],
          t = e.errors[a.fields.htmlName],
          h = `${a.fields.htmlName}-validation-msg`,
          {
            id: o,
            ...s
          } = e.register(a.fields.htmlName, {
            label: a.fields.label,
            required: n,
            validations: i
          });
        return (0, l.jsxs)(m.FormControl, {
          id: o,
          fullWidth: !0,
          required: n,
          validationStatus: "string" == typeof t ? "error" : void 0,
          children: [(0, l.jsx)(m.FormControl.Label, {
            children: a.fields.label
          }), (0, l.jsxs)(m.Select, {
            ...s,
            ...(0, p.$C)({
              action: a.fields.label,
              tag: "select",
              context: "form_control",
              location: "form"
            }),
            "aria-describedby": h,
            children: [(0, l.jsxs)("option", {
              value: "",
              children: [(0, u.t)("Select"), "\u2026"]
            }), Object.entries(a.fields.options).map(([a, e]) => (0, l.jsx)("option", {
              value: a,
              children: e
            }, a))]
          }), "string" == typeof t ? (0, l.jsx)(m.FormControl.Validation, {
            id: h,
            children: t
          }) : null]
        }, a.fields.htmlName)
      }
      aa.displayName = "PhoneInput", ae.displayName = "ContentfulTextInput", an.displayName = "ContentfulSelectInput";

      function al({
        component: a
      }) {
        var e;
        let n = Array.from({
          length: Math.ceil((e = Object.entries(a.fields.options)).length / 3)
        }, (a, n) => {
          let l = 3 * n;
          return e.slice(l, l + 3)
        });
        return (0, l.jsxs)(m.CheckboxGroup, {
          ...(0, p.$C)({
            action: a.fields.text,
            tag: "checkbox-group",
            context: "form_control",
            location: "form"
          }),
          children: [(0, l.jsx)(m.CheckboxGroup.Label, {
            children: a.fields.text
          }), (0, l.jsx)(m.Grid, {
            className: "ContentfulCheckboxGroupInput-module__checkboxGrid__ehTMs",
            children: n.map((e, n) => (0, l.jsx)(m.Grid.Column, {
              span: 6,
              children: (0, l.jsx)(m.Stack, {
                direction: "vertical",
                gap: 8,
                padding: "none",
                children: e.map(([e, n]) => (0, l.jsxs)(m.FormControl, {
                  id: `checkbox-${a.fields.htmlName}-${e}`,
                  children: [(0, l.jsx)(m.FormControl.Label, {
                    children: n
                  }), (0, l.jsx)(m.Checkbox, {
                    name: `${a.fields.htmlName}[]`,
                    value: e
                  })]
                }, e))
              })
            }, `column-${e[0]?.[0]??n}`))
          })]
        }, a.fields.htmlName)
      }

      function ai({
        rows: a,
        formContext: e
      }) {
        let n = a => {
          if ((0, _.O)(a)) return (0, l.jsx)(ae, {
            component: a
          }, a.sys.id);
          if ((0, Y.$)(a)) return (0, l.jsx)(al, {
            component: a
          }, a.sys.id);
          if ((0, w.B)(a)) {
            let n = a.fields.validations?.some(a => "REQUIRED" === a.fields.name) ?? !1,
              i = e.errors[a.fields.htmlName],
              t = `${a.fields.htmlName}-validation-msg`,
              r = [...a.fields.validations?.map(J) ?? []],
              {
                id: h,
                ...o
              } = e.register(a.fields.htmlName, {
                label: a.fields.label,
                required: n,
                validations: r
              });
            return (0, l.jsxs)(m.FormControl, {
              id: h,
              fullWidth: !0,
              required: n,
              validationStatus: "string" == typeof i ? "error" : void 0,
              children: [(0, l.jsx)(m.FormControl.Label, {
                children: a.fields.label
              }), (0, l.jsx)(m.Textarea, {
                ...o,
                ...(0, p.$C)({
                  action: a.fields.label,
                  tag: "input",
                  context: "form_control",
                  location: "form"
                }),
                "aria-describedby": t,
                placeholder: a.fields.placeholder
              }), "string" == typeof i ? (0, l.jsx)(m.FormControl.Validation, {
                id: t,
                children: i
              }) : null]
            }, a.fields.htmlName)
          }
          return (0, W.p)(a) ? (0, l.jsx)(an, {
            component: a
          }, a.sys.id) : null
        };
        return (0, l.jsx)(l.Fragment, {
          children: a.map(a => {
            let e = a.fields.formFields ?? a.fields.fields ?? [] ?? [];
            return 2 === e.length ? (0, l.jsxs)(m.Stack, {
              direction: "horizontal",
              alignItems: "flex-start",
              padding: "none",
              style: {
                width: "100%"
              },
              children: [(0, l.jsx)(m.Box, {
                style: {
                  flex: 5,
                  minWidth: 0
                },
                children: n(e[0])
              }), (0, l.jsx)(m.Box, {
                style: {
                  flex: 5,
                  minWidth: 0
                },
                children: n(e[1])
              })]
            }, a.sys.id) : (0, l.jsx)(m.Stack, {
              direction: "horizontal",
              alignItems: "flex-start",
              padding: "none",
              style: {
                width: "100%"
              },
              children: (0, l.jsx)(m.Box, {
                style: {
                  flex: 10,
                  minWidth: 0
                },
                children: e.map(a => n(a))
              })
            }, a.sys.id)
          })
        })
      }

      function at({
        formFields: a,
        formContext: e
      }) {
        return (0, l.jsx)(l.Fragment, {
          children: a.map(a => {
            if ((0, _.O)(a)) return (0, l.jsx)(ae, {
              component: a
            }, a.sys.id);
            if ((0, Y.$)(a)) return (0, l.jsx)(al, {
              component: a
            }, a.sys.id);
            if ((0, w.B)(a)) {
              let n = a.fields.validations?.some(a => "REQUIRED" === a.fields.name) ?? !1,
                i = e.errors[a.fields.htmlName],
                t = `${a.fields.htmlName}-validation-msg`,
                r = [...a.fields.validations?.map(J) ?? []],
                {
                  id: h,
                  ...o
                } = e.register(a.fields.htmlName, {
                  label: a.fields.label,
                  required: n,
                  validations: r
                });
              return (0, l.jsxs)(m.FormControl, {
                id: h,
                fullWidth: !0,
                required: n,
                validationStatus: "string" == typeof i ? "error" : void 0,
                children: [(0, l.jsx)(m.FormControl.Label, {
                  children: a.fields.label
                }), (0, l.jsx)(m.Textarea, {
                  ...o,
                  ...(0, p.$C)({
                    action: a.fields.label,
                    tag: "input",
                    context: "form_control",
                    location: "form"
                  }),
                  "aria-describedby": t,
                  placeholder: a.fields.placeholder
                }), "string" == typeof i ? (0, l.jsx)(m.FormControl.Validation, {
                  id: t,
                  children: i
                }) : null]
              }, a.fields.htmlName)
            }
            return (0, W.p)(a) ? (0, l.jsx)(an, {
              component: a
            }, a.sys.id) : null
          })
        })
      }
      al.displayName = "ContentfulCheckboxGroupInput", ai.displayName = "ContentfulFormTwoColumnLayout", at.displayName = "ContentfulFormSingleColumnLayout";
      let am = (0, r.createContext)({});

      function ar({
        component: a,
        ...e
      }) {
        let n = (0, r.use)(am),
          s = (() => {
            let a = (0, r.useRef)({}),
              e = (0, r.useRef)({}),
              [n, l] = (0, r.useState)({
                touched: !1,
                errors: !1
              }),
              i = e => {
                a.current = {
                  ...a.current,
                  [e.name]: e
                }
              };
            return {
              errors: e.current,
              formFields: a.current,
              formState: n,
              handleSubmit: n => async i => {
                for (let [n, {
                    value: l,
                    validations: t,
                    required: m
                  }] of(i.preventDefault(), e.current = {}, Object.entries(a.current)))
                  if ("string" != typeof l || "" !== l || m) {
                    for (let a of t ?? []) {
                      let {
                        success: i
                      } = a.schema.safeParse(l);
                      if (!i) {
                        e.current = {
                          ...e.current,
                          [n]: a.message
                        };
                        break
                      }
                    }!e.current[n] && m && "string" == typeof l && "" === l && (e.current = {
                      ...e.current,
                      [n]: "This field is required"
                    })
                  } let t = Object.keys(e.current).length > 0;
                if (l(a => ({
                    ...a,
                    errors: t
                  })), t) return;
                let m = Object.entries(a.current).reduce((a, [e, n]) => (a[e] = n.value, a), {}),
                  r = new FormData(i.target);
                for (let a of new Set(r.keys()))
                  if (a.endsWith("[]")) {
                    let e = a.slice(0, -2),
                      n = r.getAll(a);
                    m[e] = n
                  } await n(m)
              },
              register: (e, n) => {
                let t = a => {
                    if (a instanceof HTMLSelectElement || a instanceof HTMLTextAreaElement) return a.value;
                    let {
                      type: e,
                      checked: n,
                      value: l
                    } = a;
                    return "checkbox" !== e ? l : null !== a.getAttribute("value") ? n ? l : "" : n
                  },
                  m = `form-field-${e}`,
                  r = {
                    id: m,
                    name: e,
                    onChange: n => {
                      let m = a.current[e];
                      if (void 0 === m) return;
                      let r = t(n.target);
                      i({
                        ...m,
                        value: r
                      }), l(a => ({
                        ...a,
                        touched: !0
                      }))
                    },
                    ref: n => {
                      if (null === n) return;
                      let l = a.current[e];
                      void 0 !== l && i({
                        ...l,
                        $el: n,
                        value: t(n)
                      })
                    }
                  };
                return void 0 !== a.current[e] || i({
                  id: m,
                  label: n?.label,
                  name: e,
                  required: n?.required,
                  value: "",
                  validations: n?.validations
                }), r
              },
              unregister: n => {
                void 0 !== a.current[n] && (delete a.current[n], delete e.current[n])
              }
            }
          })(),
          {
            campaign: c
          } = a.fields,
          {
            isEloqua: u,
            isMarketo: f,
            redirectUrl: g,
            elqFormName: C,
            ...S
          } = function(a) {
            let e, n, l, i, t, [m, p] = (0, r.useState)(void 0);
            if ((0, r.useEffect)(() => {
                try {
                  let {
                    origin: a,
                    pathname: e,
                    search: n
                  } = window.location, l = e.endsWith("/") ? e.slice(0, -1) : e, i = `${a}${l}/confirmation${n}`;
                  p(i)
                } catch {
                  p(void 0)
                }
                return () => p(void 0)
              }, [a]), (0, o.s)(a)) {
              let t = a.fields;
              e = t.cDLProgramName, n = t.sFDCLastCampaignStatus, l = t.source, i = t.directToSfdcCampaignId
            }
            return (0, h.y)(a) && (t = a.fields.elqFormName, l = a.fields.source), {
              isEloqua: (0, h.y)(a),
              isMarketo: (0, o.s)(a),
              redirectUrl: m,
              cDLProgramName: e,
              sFDCLastCampaignStatus: n,
              source: l,
              ...i && {
                directToSfdcCampaignId: i
              },
              elqFormName: t
            }
          }(c),
          {
            source: x
          } = S;
        if (!c) return null;
        let b = async e => {
          if ("string" != typeof n.marketingFormsApiHost) throw Error("The 'marketingFormsApiHost' context value is missing.");
          let l = `contentful-${a.sys.id}`,
            {
              primaryConsent: i,
              ...t
            } = e;
          await fetch(`${n.marketingFormsApiHost}/forms/${l}/submissions`, {
            method: "POST",
            headers: {
              "content-type": "application/x-www-form-urlencoded"
            },
            body: new URLSearchParams({
              ...t,
              ...S,
              redirect_url: window.location.href
            }),
            redirect: "manual"
          })
        }, v = async a => {
          e.onSubmit ? await e.onSubmit({
            ...a,
            ...S
          }) : f && await b(a), e.onSubmitted && await e.onSubmitted()
        }, M = a.fields.layoutOption, y = u ? u ? {
          action: "https://s88570519.t.eloqua.com/e/f2"
        } : {} : {
          onSubmit: s.handleSubmit(v)
        };
        return (0, l.jsx)(d, {
          value: s,
          children: (0, l.jsx)(D, {
            ...y,
            children: (0, l.jsxs)(m.Stack, {
              direction: "vertical",
              gap: "condensed",
              padding: "none",
              children: [void 0 !== a.fields.heading ? (0, i.documentToReactComponents)(a.fields.heading, {
                renderNode: {
                  [t.BLOCKS.PARAGRAPH]: (a, n) => (0, l.jsx)(D.Heading, {
                    ...e.headingProps,
                    children: n
                  })
                }
              }) : null, "formLayout" === M.sys.contentType.sys.id && (0, l.jsx)(at, {
                formFields: "formFields" in M.fields ? M.fields.formFields : [],
                formContext: s
              }), "twoColumnFormLayout" === M.sys.contentType.sys.id && (0, l.jsx)(ai, {
                rows: "rows" in M.fields ? M.fields.rows : [],
                formContext: s
              }), !e.skipConsentExperience && (0, l.jsxs)(l.Fragment, {
                children: [(0, l.jsx)(D.CountrySelectField, {}), (0, l.jsx)(D.ConsentExperience, {})]
              }), !e.skipOctocaptcha && (0, l.jsx)(D.Octocaptcha, {}), u && (0, l.jsxs)(l.Fragment, {
                children: [C ? (0, l.jsx)("input", {
                  type: "hidden",
                  name: "elqFormName",
                  value: C
                }) : null, (0, l.jsx)("input", {
                  type: "hidden",
                  name: "elqSiteId",
                  value: "88570519"
                }), (0, l.jsx)("input", {
                  type: "hidden",
                  name: "redirect_url",
                  value: g
                }), x ? (0, l.jsx)("input", {
                  type: "hidden",
                  name: "source",
                  value: x
                }) : null]
              }), (0, l.jsx)(D.Submit, {
                ...(0, p.$C)({
                  action: a.fields.submitText,
                  tag: "button",
                  context: "form_submit",
                  location: "form"
                }),
                children: a.fields.submitText
              }), (0, l.jsx)(m.Box, {
                marginBlockStart: "normal",
                children: (0, l.jsx)(D.Errors, {})
              })]
            })
          })
        })
      }
      am.displayName = "ContentfulFormContext", ar.displayName = "ContentfulForm"
    },
    7151(a, e, n) {
      n.d(e, {
        W: () => s
      });
      var l = n(74848),
        i = n(55368),
        t = n(96540),
        m = n(24944);

      function r(a) {
        return a.replace(/\/$/, "") || "/"
      }
      let h = a => {
        if (void 0 === a.actual) return !1;
        let e = new URL(a.url, void 0),
          n = new URL(a.actual, void 0),
          l = e.hostname === n.hostname,
          i = r(e.pathname) === r(n.pathname);
        return l && i
      };
      var o = n(51587);
      let p = "subnav",
        s = ({
          ref: a,
          component: e,
          ...n
        }) => {
          let [r, s] = (0, t.useState)(void 0), d = e.fields.subheading && !h({
            url: e.fields.subheading.fields.href,
            actual: r
          });
          return (0, t.useEffect)(() => {
            s(window.location.href)
          }, []), (0, l.jsxs)("div", {
            "data-color-mode": n["data-color-mode"],
            children: [(0, l.jsxs)(i.SubNav, {
              className: n.className,
              hasShadow: n.hasShadow,
              ref: a,
              children: [(0, l.jsx)(i.SubNav.Heading, {
                "data-ref": `subnav-heading-link-${e.fields.heading.sys.id}`,
                href: e.fields.heading.fields.href,
                ...(0, o.$C)({
                  action: e.fields.heading.fields.text,
                  tag: "link",
                  location: p
                }),
                children: e.fields.heading.fields.text
              }), e.fields.subheading && (0, l.jsx)(i.SubNav.SubHeading, {
                "data-ref": `subnav-subheading-link-${e.fields.subheading.sys.id}`,
                href: e.fields.subheading.fields.href,
                ...h({
                  url: e.fields.subheading.fields.href,
                  actual: r
                }) ? {
                  "aria-current": "page"
                } : {},
                ...(0, o.$C)({
                  action: e.fields.subheading.fields.text,
                  tag: "link",
                  location: p
                }),
                children: e.fields.subheading.fields.text
              }), e.fields.links.map(a => {
                if ((0, m.P)(a)) {
                  let {
                    href: e,
                    text: t
                  } = a.fields, m = h({
                    url: e,
                    actual: r
                  });
                  return (0, l.jsx)(i.SubNav.Link, {
                    "data-ref": `subnav-link-${a.sys.id}`,
                    href: e,
                    variant: n.linkVariant,
                    ...m ? {
                      "aria-current": "page"
                    } : {},
                    ...(0, o.$C)({
                      action: t,
                      tag: "link",
                      location: p
                    }),
                    children: t
                  }, a.sys.id)
                }
                let {
                  heading: e,
                  links: t = []
                } = a.fields;
                return (0, l.jsxs)(i.SubNav.Link, {
                  href: e.fields.href,
                  variant: n.linkVariant,
                  ...h({
                    url: e.fields.href,
                    actual: r
                  }) ? {
                    "aria-current": "page"
                  } : {},
                  children: [e.fields.text, t.length > 0 && (0, l.jsx)(i.SubNav.SubMenu, {
                    children: t.map(a => (0, l.jsx)(i.SubNav.Link, {
                      href: a.fields.href,
                      variant: n.linkVariant,
                      "data-ref": `subnav-submenu-link-${a.sys.id}`,
                      ...h({
                        url: a.fields.href,
                        actual: r
                      }) ? {
                        "aria-current": "page"
                      } : {},
                      ...(0, o.$C)({
                        action: a.fields.text,
                        tag: "link",
                        context: e.fields.text,
                        location: p
                      }),
                      children: a.fields.text
                    }, a.sys.id))
                  })]
                }, e.sys.id)
              }), void 0 !== e.fields.cta && (0, l.jsx)(i.SubNav.Action, {
                href: e.fields.cta.fields.href,
                "data-ref": `subnav-cta-action-${e.fields.cta.sys.id}`,
                children: e.fields.cta.fields.text
              })]
            }), d && (0, l.jsx)(i.Box, {
              paddingBlockStart: {
                narrow: 64,
                regular: "none"
              }
            })]
          })
        };
      s.displayName = "ContentfulSubnav", s.displayName = "ContentfulSubnav"
    },
    51678(a, e, n) {
      n.d(e, {
        G: () => l
      });
      let l = (0, n(96540).createContext)({
        marketingTargetedCountries: [],
        selectedCountry: null,
        setSelectedCountry: () => {}
      });
      l.displayName = "ConsentExperienceContext"
    },
    27226(a, e, n) {
      n.d(e, {
        u: () => l
      });
      let l = {
        EXPLICIT: "optInExplicit",
        IMPLICIT: "optInImplicit"
      }
    },
    13800(a, e, n) {
      n.d(e, {
        s: () => i
      });
      var l = n(96540);

      function i(a = null) {
        let [e, n] = (0, l.useState)(!0), [t, m] = (0, l.useState)(a);
        return {
          isConsentExperienceValid: e,
          onConsentExperienceValidationChange: a => {
            n(a)
          },
          selectedCountry: t,
          setSelectedCountry: m
        }
      }
    },
    57766(a, e, n) {
      n.d(e, {
        x: () => l
      });
      let l = (0, n(96540).createContext)({
        hostName: ""
      });
      l.displayName = "OctocaptchaContext"
    }
  }
]);
//# sourceMappingURL=49957-e3bf0e20ef9a29eb-8beecbf8f8866f90.js.map