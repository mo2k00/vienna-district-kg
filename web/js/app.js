import { api } from "./api.js";
import { el, notice } from "./dom.js";
import * as about from "./views/about.js";
import * as district from "./views/district.js";
import * as recommend from "./views/recommend.js";
import * as similar from "./views/similar.js";

const VIEWS = { recommend, similar, district, about };
const root = document.getElementById("view");
let cleanup = () => {};
let meta;

function parseHash() {
  const [name, params] = location.hash.replace(/^#\/?/, "").split("/");
  return { name: VIEWS[name] ? name : "recommend", params };
}

function navigate(path) {
  location.hash = `#/${path}`;
}

async function route() {
  const { name, params } = parseHash();
  cleanup();
  root.replaceChildren();
  for (const link of document.querySelectorAll(".nav a")) {
    link.classList.toggle("active", link.dataset.view === name);
  }
  window.scrollTo({ top: 0 });
  try {
    cleanup = (await VIEWS[name].render(root, { meta, navigate, params })) ?? (() => {});
  } catch (error) {
    console.error(error);
    root.replaceChildren(notice(`Something went wrong: ${error.message}`, "error"));
    cleanup = () => {};
  }
}

async function start() {
  try {
    meta = await api.meta();
  } catch (error) {
    root.replaceChildren(el("div", { class: "card" }, notice(`API not reachable: ${error.message}`, "error")));
    return;
  }
  window.addEventListener("hashchange", route);
  route();
}

start();
