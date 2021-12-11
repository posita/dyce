// Copyright and other protections apply. Please see the accompanying LICENSE file for
// rights and restrictions governing use of this software. All rights not expressly
// waived or licensed are reserved. If that file is missing or appears to be modified
// from its original, then please contact the author before viewing or using this
// software in any capacity.

// Adapted from
// https://developer.mozilla.org/en-US/docs/Web/CSS/Media_Queries/Testing_media_queries#receiving_query_notifications
const mediaQueryList = window.matchMedia("(prefers-color-scheme: dark)");

function handleColorSchemeChange(event) {
  var body = document.querySelector("body[data-md-color-scheme]");
  var color, theme;

  if (event.matches) {
    // Dark
    color = "light-green";
    theme = "slate";
  } else {
    // Light
    color = "green";
    theme = "default";
  }

  if (body !== null) {
    var palette_native;

    if (typeof __md_get !== "undefined") {
      // See
      // <https://github.com/squidfunk/mkdocs-material/commit/887b7115fcca3c945582a3d1f90810a7aeda6ead#diff-27db428a75bbd7d3b97412161ed4136c8986748a616c8be4d93f60b16e74f22d>
      palette_native = __md_get("__palette");
    } else {
      palette_native = JSON.parse(localStorage.getItem(__prefix("__palette")));
    }

    if (typeof palette_native.color === "object") {
      palette_native.color.scheme = theme;
      palette_native.color.primary = palette_native.color.accent = color;

      if (typeof __md_set !== "undefined") {
        // See note regarding __md_get above
        __md_set("__palette", palette_native);
      } else {
        localStorage.setItem(__prefix("__palette"), JSON.stringify(palette_native));
      }

      body.setAttribute("data-md-color-scheme", palette_native.color.scheme);
      body.setAttribute("data-md-color-primary", palette_native.color.primary);
      body.setAttribute("data-md-color-accent", palette_native.color.accent);
    }
  }
}

handleColorSchemeChange(mediaQueryList);
mediaQueryList.addListener(handleColorSchemeChange);
