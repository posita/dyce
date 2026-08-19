// Theme the generated Plotly fragments from the active Material palette.
(() => {
  "use strict";

  function resolvedCssColor(color) {
    const probe = document.createElement("span");
    probe.hidden = true;
    probe.style.color = color;
    document.body.appendChild(probe);
    const resolved = getComputedStyle(probe).color;
    probe.remove();
    return resolved;
  }

  function cssColorWithAlpha(color, alpha) {
    const channels = resolvedCssColor(color).match(/[\d.]+/g);
    return channels?.length >= 3
      ? `rgba(${channels[0]}, ${channels[1]}, ${channels[2]}, ${alpha})`
      : color;
  }

  function materialTheme() {
    const value = (name) => resolvedCssColor(`var(${name})`);
    return {
      background: value("--md-default-bg-color"),
      foreground: value("--md-typeset-color"),
      muted: value("--md-default-fg-color--light"),
      border: value("--md-default-fg-color--lightest"),
    };
  }

  async function themePlotly(target) {
    const plot = typeof target === "string" ? document.getElementById(target) : target;
    if (!plot?.layout || !window.Plotly) return;

    const theme = materialTheme();
    const annotations = (plot.layout.annotations || []).map((annotation) => ({
      ...annotation,
      font: { ...(annotation.font || {}), color: theme.muted },
      ...(annotation.name === "ridge-label" ||
      annotation.name === "ridge-peak-label"
        ? { bgcolor: cssColorWithAlpha(theme.background, 0.72) }
        : {}),
    }));
    await window.Plotly.relayout(plot, {
      "font.color": theme.foreground,
      "xaxis.color": theme.muted,
      "xaxis.gridcolor": theme.border,
      "xaxis.linecolor": theme.border,
      "xaxis.zerolinecolor": theme.border,
      "yaxis.color": theme.muted,
      "yaxis.gridcolor": theme.border,
      "yaxis.linecolor": theme.border,
      "yaxis.zerolinecolor": theme.border,
      "modebar.color": theme.muted,
      "modebar.activecolor": theme.foreground,
      annotations,
    });
  }

  function themeAllPlots() {
    for (const plot of document.querySelectorAll(".plotly-graph-div")) {
      void themePlotly(plot);
    }
  }

  window.dyceThemePlotly = themePlotly;
  window.addEventListener("DOMContentLoaded", () => {
    themeAllPlots();
    new MutationObserver(themeAllPlots).observe(document.body, {
      attributes: true,
      attributeFilter: ["data-md-color-scheme"],
    });
  });
})();
