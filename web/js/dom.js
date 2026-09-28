export function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (value === undefined || value === null || value === false) continue;
    if (key === "class") node.className = value;
    else if (key === "dataset") Object.assign(node.dataset, value);
    else if (key.startsWith("on")) node.addEventListener(key.slice(2).toLowerCase(), value);
    else if (value === true) node.setAttribute(key, "");
    else node.setAttribute(key, value);
  }
  for (const child of children.flat()) {
    if (child === undefined || child === null || child === false) continue;
    node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return node;
}

const numberFormat = new Intl.NumberFormat("en-GB", { maximumFractionDigits: 1 });
const preciseFormat = new Intl.NumberFormat("en-GB", { maximumFractionDigits: 2 });

export function formatNumber(value) {
  if (value === null || value === undefined) return "–";
  if (Math.abs(value) < 10) return preciseFormat.format(value);
  return numberFormat.format(value);
}

export function formatFeature(feature, value) {
  if (feature.endsWith("_share")) return `${numberFormat.format(value * 100)} %`;
  if (feature === "net_income") return `€ ${numberFormat.format(value)}`;
  return formatNumber(value);
}

export function levelBadge(level) {
  return el("span", { class: `level level--${level}` }, level);
}

export function ordinal(n) {
  const suffix = n % 10 === 1 && n !== 11 ? "st" : n % 10 === 2 && n !== 12 ? "nd" : n % 10 === 3 && n !== 13 ? "rd" : "th";
  return `${n}${suffix}`;
}

export function districtTitle(district) {
  return `${district.number}. ${district.name}`;
}

export function notice(message, variant = "") {
  return el("div", { class: `notice ${variant ? `notice--${variant}` : ""}` }, message);
}

export function loading(label = "Loading…") {
  return el("div", { class: "empty" }, el("span", { class: "spinner" }), " ", label);
}
