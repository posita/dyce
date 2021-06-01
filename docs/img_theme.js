// Adapted from
// https://developer.mozilla.org/en-US/docs/Web/CSS/Media_Queries/Testing_media_queries#receiving_query_notifications
const mediaQueryList = window.matchMedia("(prefers-color-scheme: dark)");

function handleColorSchemeChange(event) {
  var body = document.querySelector("body[data-md-color-scheme]");
  var color, theme;
  if (event.matches) {
    color = "light-green";
    theme = "slate";
  } else {
    color = "green";
    theme = "default";
  }
  if (body !== null && theme !== null) {
    body.setAttribute("data-md-color-scheme", theme);
    body.setAttribute("data-md-color-primary", color);
    body.setAttribute("data-md-color-accent", color);
  }
}

handleColorSchemeChange(mediaQueryList);
mediaQueryList.addListener(handleColorSchemeChange);
