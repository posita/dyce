// Adapted from
// https://developer.mozilla.org/en-US/docs/Web/CSS/Media_Queries/Testing_media_queries#receiving_query_notifications
const mediaQueryList = window.matchMedia("(prefers-color-scheme: dark)");

function handleColorSchemeChange(event) {
  var body = document.querySelector("body[data-md-color-scheme]");

  if (body !== null && typeof palette !== "undefined" && palette.hasOwnProperty("color")) {
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

    palette.color.scheme = theme;
    palette.color.primary = palette.color.accent = color;
    localStorage.setItem(__prefix("__palette"), JSON.stringify(palette));
    body.setAttribute("data-md-color-scheme", palette.color.scheme);
    body.setAttribute("data-md-color-primary", palette.color.primary);
    body.setAttribute("data-md-color-accent", palette.color.accent);
  }
}

handleColorSchemeChange(mediaQueryList);
mediaQueryList.addListener(handleColorSchemeChange);
