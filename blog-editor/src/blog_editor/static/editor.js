// The blog editor. No framework and no build step: it talks to the local
// server in server.py, which does all the Markdown work, so the preview is
// exactly the page that publishing will write.
"use strict";

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

const el = {
  title: $("#f-title"), date: $("#f-date"), slug: $("#f-slug"), summary: $("#f-summary"),
  cover: $("#f-cover"), src: $("#src"), frame: $("#preview"), frameWrap: $("#frame-wrap"),
  chip: $("#chip"), status: $("#status"), where: $("#where"), words: $("#words"),
  issuesBtn: $("#btn-issues"), issues: $("#issues"), rename: $("#btn-rename"),
  save: $("#btn-save"), publish: $("#btn-publish"), more: $("#more"),
};

const state = { slug: null, status: null, url: null, media: [], dirty: false, busy: false };

// ---------- small helpers ----------

const store = {
  get(k, d = null) { try { return localStorage.getItem("blog-editor:" + k) ?? d; } catch { return d; } },
  set(k, v) { try { localStorage.setItem("blog-editor:" + k, v); } catch { /* private mode */ } },
};

async function api(method, path, body) {
  const opts = { method, headers: {} };
  if (body instanceof FormData) opts.body = body;
  else if (body !== undefined) {
    opts.body = JSON.stringify(body);
    opts.headers["Content-Type"] = "application/json";
  }
  const r = await fetch(path, opts);
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.error || `${r.status} ${r.statusText}`);
  return data;
}

function say(text, kind = "") {
  el.status.textContent = text;
  el.status.className = kind;
}

function fail(e) {
  console.error(e);
  say(e.message || String(e), "error");
}

const kindOf = (name) =>
  /\.(png|jpe?g|gif|webp|avif|svg)$/i.test(name) ? "image" : /\.(mp4|webm)$/i.test(name) ? "video" : "file";

const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);

function payload() {
  return {
    meta: { title: el.title.value, date: el.date.value, summary: el.summary.value, cover: el.cover.value },
    body: el.src.value,
  };
}

// ---------- loading posts ----------

function applyPost(p, { keepText = false } = {}) {
  const switching = p.slug !== state.slug;
  state.slug = p.slug;
  state.status = p.status;
  state.url = p.url;
  setMedia(p.media);
  if (!keepText) {
    el.title.value = p.meta.title;
    el.date.value = p.meta.date;
    el.summary.value = p.meta.summary;
    el.cover.value = p.meta.cover;
    el.src.value = p.body;
    el.src.scrollTop = 0;
    el.src.setSelectionRange(0, 0);
    setDirty(false);
  }
  el.slug.value = p.slug;
  history.replaceState(null, "", "#" + p.slug);
  store.set("last", p.slug);
  document.title = `${p.meta.title || "Untitled"} — Blog editor`;
  updateChrome();
  countWords();
  if (switching || !keepText) refreshPreview({ reload: true });
}

async function openPost(slug, { force = false } = {}) {
  if (!force && state.dirty && slug !== state.slug && !confirm("This post has unsaved changes. Leave them?")) return false;
  try {
    applyPost(await api("GET", `/_api/posts/${slug}`));
    say(`Opened ${slug}`);
    return true;
  } catch (e) { fail(e); return false; }
}

function setDirty(dirty) {
  state.dirty = dirty;
  updateChrome();
}

function updateChrome() {
  const s = state.status;
  const label = { draft: "Draft", published: "Published", changed: "Published · draft has changes" }[s] || "";
  el.chip.hidden = !s;
  el.chip.className = "chip " + (s || "");
  el.chip.innerHTML = esc(label) + (state.dirty ? ' <span class="dirty">· unsaved</span>' : "");
  el.slug.readOnly = s !== "draft";
  el.slug.title = s === "draft" ? "The post's address. You can change it until it is published."
    : "A published post keeps its address.";
  el.rename.hidden = s !== "draft" || el.slug.value === state.slug;
  $("#m-discard").disabled = s !== "changed";
  $("#m-unpublish").disabled = s === "draft" || !s;
  const live = $("#m-live");
  live.setAttribute("aria-disabled", String(!state.url));
  if (state.url) live.href = state.url; else live.removeAttribute("href");
  $("#m-preview").href = state.slug ? `/_preview/${state.slug}/` : "#";
  el.where.textContent = state.slug ? `blog-editor/posts/${state.slug}/` : "";
  el.save.disabled = el.publish.disabled = !state.slug || state.busy;
}

function setMedia(media) {
  state.media = media || [];
  const current = el.cover.value;
  el.cover.replaceChildren(new Option("None", ""));
  for (const m of state.media.filter((m) => m.kind === "image" && !m.name.endsWith(".svg"))) {
    el.cover.add(new Option(m.name, m.name));
  }
  el.cover.value = state.media.some((m) => m.name === current) ? current : "";
}

// ---------- saving and publishing ----------

async function saveDraft() {
  if (!state.slug || state.busy) return;
  try {
    state.busy = true; updateChrome();
    const r = await api("PUT", `/_api/posts/${state.slug}/draft`, payload());
    state.status = r.status;
    setDirty(false);
    say(`Draft saved · ${new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`, "ok");
  } catch (e) { fail(e); }
  finally { state.busy = false; updateChrome(); }
}

async function publish() {
  if (!state.slug || state.busy) return;
  try {
    state.busy = true; updateChrome();
    say("Publishing…");
    const r = await api("POST", `/_api/posts/${state.slug}/publish`, payload());
    if (r.published) {
      applyPost(r, { keepText: true });
      setDirty(false);
      say(r.check_ok === false ? "Published, but the site check failed" : "Published into the site folder — not committed",
          r.check_ok === false ? "error" : "ok");
    } else {
      say("Not published: fix the problems first", "error");
    }
    showResult(r);
  } catch (e) { fail(e); }
  finally { state.busy = false; updateChrome(); }
}

function showResult(r) {
  const ok = r.published !== false;
  $("#r-heading").textContent = ok ? (r.unpublished ? "Unpublished" : "Published") : "Not published yet";
  const parts = [];
  if (r.errors?.length) {
    parts.push(`<div class="err"><h3>${ok ? "Problems" : "Fix these first"}</h3><ul>${r.errors.map((e) => `<li>${esc(e)}</li>`).join("")}</ul></div>`);
  }
  if (r.warnings?.length) {
    parts.push(`<div class="warn"><h3>Worth a look</h3><ul>${r.warnings.map((w) => `<li>${esc(w)}</li>`).join("")}</ul></div>`);
  }
  if (ok) {
    parts.push(r.changed?.length
      ? `<div><h3>Changed in the site folder</h3><ul class="files">${r.changed.map((f) => `<li>${esc(f)}</li>`).join("")}</ul></div>`
      : `<p class="note">Nothing in the site folder changed.</p>`);
    if (r.check) parts.push(`<div><h3>Site check</h3><pre>${esc(r.check)}</pre></div>`);
    parts.push(`<p class="note">Nothing has been committed. Review the changes with <code>git status</code> and commit them when you're ready.</p>`);
  }
  $("#r-body").innerHTML = parts.join("");
  const view = $("#r-view");
  view.hidden = !(ok && r.url && !r.unpublished);
  if (r.url) view.href = r.url;
  $("#dlg-result").showModal();
}

async function discardDraft() {
  el.more.open = false;
  if (!confirm("Throw away the draft and go back to the published version?")) return;
  try {
    applyPost(await api("DELETE", `/_api/posts/${state.slug}/draft`));
    say("Draft discarded; showing the published version", "ok");
  } catch (e) { fail(e); }
}

async function unpublish() {
  el.more.open = false;
  if (!confirm("Take this post off the site? Its page is removed from the site folder, and the post goes back to being a draft.")) return;
  try {
    state.busy = true;
    const r = await api("POST", `/_api/posts/${state.slug}/unpublish`);
    applyPost(r, { keepText: state.dirty });
    showResult({ ...r, unpublished: true });
    say("Unpublished — not committed", "ok");
  } catch (e) { fail(e); }
  finally { state.busy = false; updateChrome(); }
}

async function renameSlug() {
  const slug = el.slug.value.trim();
  try {
    applyPost(await api("POST", `/_api/posts/${state.slug}/rename`, { slug }), { keepText: true });
    say(`Renamed to /blog/${slug}/`, "ok");
  } catch (e) { fail(e); el.slug.value = state.slug; updateChrome(); }
}

// ---------- the posts dialog ----------

async function showPosts() {
  const dlg = $("#dlg-posts");
  const list = $("#post-list");
  try {
    const { posts } = await api("GET", "/_api/posts");
    list.innerHTML = posts.length ? "" : '<li class="empty">No posts yet. Give the first one a title above.</li>';
    for (const p of posts) {
      const li = document.createElement("li");
      if (p.slug === state.slug) li.className = "current";
      const label = { draft: "Draft", published: "Published", changed: "Changed" }[p.status];
      li.innerHTML = `<button type="button"><span class="t">${esc(p.title || p.slug)}</span>
        <span class="d">${esc(p.date)} · /blog/${esc(p.slug)}/</span><span class="chip ${p.status}">${label}</span></button>`;
      li.firstElementChild.addEventListener("click", async () => {
        if (await openPost(p.slug)) dlg.close();
      });
      list.append(li);
    }
  } catch (e) { fail(e); }
  if (!dlg.open) dlg.showModal();
  $("#new-title").focus();
}

async function newPost() {
  const title = $("#new-title").value.trim();
  if (!title) { $("#new-title").focus(); return; }
  if (state.dirty && !confirm("This post has unsaved changes. Leave them?")) return;
  try {
    applyPost(await api("POST", "/_api/posts", { title }));
    $("#new-title").value = "";
    $("#dlg-posts").close();
    el.src.focus();
    say(`New draft in blog-editor/posts/${state.slug}/`, "ok");
  } catch (e) { fail(e); }
}

// ---------- editing the text ----------

// Insert text in place of the selection, keeping the browser's undo history.
function replaceSelection(text, selStart = text.length, selEnd = selStart) {
  const src = el.src;
  src.focus();
  const start = src.selectionStart;
  if (!document.execCommand("insertText", false, text)) {
    src.setRangeText(text, src.selectionStart, src.selectionEnd, "end");
    src.dispatchEvent(new Event("input", { bubbles: true }));
  }
  src.setSelectionRange(start + selStart, start + selEnd);
}

function wrap(before, after, placeholder) {
  const { selectionStart: s, selectionEnd: e, value } = el.src;
  const sel = value.slice(s, e) || placeholder;
  replaceSelection(before + sel + after, before.length, before.length + sel.length);
}

// Insert a block on lines of its own, with blank lines around it. With no
// selection and the cursor partway along a line, it goes after that line,
// so it can't land inside a link or another image.
function insertBlock(text, selStart = text.length, selEnd = selStart) {
  const src = el.src;
  if (src.selectionStart === src.selectionEnd && src.selectionStart > 0 && src.value[src.selectionStart - 1] !== "\n") {
    let eol = src.value.indexOf("\n", src.selectionStart);
    if (eol < 0) eol = src.value.length;
    src.setSelectionRange(eol, eol);
  }
  const { selectionStart: s, selectionEnd: e, value } = src;
  const before = value.slice(0, s), after = value.slice(e);
  const pre = !before || before.endsWith("\n\n") ? "" : before.endsWith("\n") ? "\n" : "\n\n";
  const post = after.startsWith("\n\n") ? "" : after.startsWith("\n") || !after ? "\n" : "\n\n";
  replaceSelection(pre + text + post, pre.length + selStart, pre.length + selEnd);
}

// Toggle a prefix ("## ", "> ", "- ") on every line the selection touches.
function prefixLines(prefix, strip = /^$/) {
  const src = el.src;
  const { selectionStart: s, selectionEnd: e, value } = src;
  const ls = value.lastIndexOf("\n", s - 1) + 1;
  let le = value.indexOf("\n", e > s && value[e - 1] === "\n" ? e - 1 : e);
  if (le < 0) le = value.length;
  const lines = value.slice(ls, le).split("\n");
  const all = lines.every((l) => l.startsWith(prefix));
  const out = lines.map((l) => (all ? l.slice(prefix.length) : prefix + l.replace(strip, ""))).join("\n");
  src.setSelectionRange(ls, le);
  replaceSelection(out, out.length);
}

function selectedText() {
  return el.src.value.slice(el.src.selectionStart, el.src.selectionEnd);
}

const commands = {
  h2: () => prefixLines("## ", /^#{1,6} /),
  h3: () => prefixLines("### ", /^#{1,6} /),
  bold: () => wrap("**", "**", "bold text"),
  italic: () => wrap("*", "*", "italic text"),
  link() {
    const sel = selectedText();
    if (/^https?:\/\/\S+$/.test(sel)) replaceSelection(`[link text](${sel})`, 1, 10);
    else {
      const text = sel || "link text";
      replaceSelection(`[${text}](https://)`, text.length + 3, text.length + 11);
    }
  },
  quote: () => prefixLines("> "),
  list: () => prefixLines("- "),
  code() {
    const sel = selectedText();
    if (sel.includes("\n")) insertBlock("```\n" + sel + "\n```", 3, 3);
    else wrap("`", "`", "code");
  },
  footnote() {
    const used = [...el.src.value.matchAll(/\[\^(\d+)\]/g)].map((m) => +m[1]);
    const n = used.length ? Math.max(...used) + 1 : 1;
    const { selectionEnd: e } = el.src;
    el.src.setSelectionRange(e, e);
    replaceSelection(`[^${n}]`);
    // The note itself goes at the end, with its text selected to type over.
    el.src.setSelectionRange(el.src.value.length, el.src.value.length);
    const note = `[^${n}]: `;
    const lead = el.src.value.endsWith("\n\n") ? "" : el.src.value.endsWith("\n") ? "\n" : "\n\n";
    replaceSelection(lead + note + "The note.\n", lead.length + note.length, lead.length + note.length + 9);
  },
  "math-inline": () => wrap("$", "$", selectedText() ? "" : "x^2"),
  "math-block": () => {
    const sel = selectedText() || "\\sum_{i=1}^{n} i = \\frac{n(n+1)}{2}";
    insertBlock(`$$\n${sel}\n$$`, 3, 3 + sel.length);
  },
  image: () => openMedia("image"),
  video: () => openMedia("video"),
  help: () => $("#dlg-help").showModal(),
};

// ---------- media ----------

async function upload(files, webSize) {
  const fd = new FormData();
  for (const f of files) fd.append("file", f, f.name);
  fd.append("web_size", webSize ? "1" : "0");
  const r = await api("POST", `/_api/posts/${state.slug}/media`, fd);
  setMedia(r.media);
  return r.names;
}

async function uploadAndInsert(files) {
  if (!state.slug || !files.length) return;
  say(`Adding ${files.length === 1 ? files[0].name : files.length + " files"}…`);
  try {
    const names = await upload(files, store.get("websize", "1") === "1");
    const md = names.map((n) => (kindOf(n) === "file" ? `[${n}](${n})` : `![](${n})`));
    // Put the cursor in the first one's [alt text] brackets.
    insertBlock(md.join("\n"), 2, 2);
    say(`Added ${names.join(", ")}. Describe ${names.length > 1 ? "them" : "it"} between the [ ]`, "ok");
  } catch (e) { fail(e); }
}

const media = { kind: "image", file: null, existing: null };

function openMedia(kind) {
  media.kind = kind; media.file = null; media.existing = null;
  const form = $("#media-form");
  form.reset();
  $("#m-websize").checked = store.get("websize", "1") === "1";
  $("#media-heading").textContent = kind === "image" ? "Insert image" : "Insert video";
  $("#m-file").accept = kind === "image" ? "image/png,image/jpeg,image/gif,image/webp,image/avif,image/svg+xml" : "video/mp4,video/webm";
  $("#m-drop-text").textContent = kind === "image" ? "Choose an image, or drop one here" : "Choose an MP4 or WebM file, or drop one here";
  $("#m-drop").classList.remove("chosen");
  $("#m-link-row").hidden = kind !== "video";
  $("#m-websize-row").hidden = $("#m-pixel-row").hidden = kind !== "image";
  $("#m-loop-row").hidden = kind !== "video";
  $("#m-alt-help").textContent = kind === "image"
    ? "What the image shows, for people who can't see it."
    : "A short description of the video, read out by screen readers.";
  const thumbs = $("#m-existing");
  thumbs.replaceChildren();
  for (const m of state.media.filter((m) => m.kind === kind)) {
    const b = document.createElement("button");
    b.type = "button";
    b.setAttribute("aria-pressed", "false");
    b.title = m.name;
    b.innerHTML = (kind === "image"
      ? `<img src="/_preview/${state.slug}/${encodeURIComponent(m.name)}" alt="">`
      : `<div class="vid"><svg viewBox="0 0 24 24"><rect x="3" y="6" width="13" height="12" rx="2"/><path d="m16 10 5-3v10l-5-3"/></svg></div>`)
      + `<span>${esc(m.name)}</span>`;
    b.addEventListener("click", () => {
      $$("button", thumbs).forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
      media.existing = m.name; media.file = null;
      $("#m-drop").classList.remove("chosen");
      $("#m-drop-text").textContent = "Choose a file, or drop one here";
      $("#m-url").value = "";
    });
    thumbs.append(b);
  }
  $("#dlg-media").showModal();
}

function chooseMediaFile(file) {
  if (!file) return;
  media.file = file; media.existing = null;
  $$("#m-existing button").forEach((x) => x.setAttribute("aria-pressed", "false"));
  $("#m-url").value = "";
  $("#m-drop").classList.add("chosen");
  $("#m-drop-text").textContent = `${file.name} · ${(file.size / 1048576).toFixed(1)} MB`;
}

async function insertMedia() {
  const url = $("#m-url").value.trim();
  const alt = $("#m-alt").value.trim().replace(/[[\]]/g, "");
  const caption = $("#m-caption").value.trim().replace(/"/g, "”");
  let name = media.existing;
  try {
    if (media.kind === "video" && url) name = url;
    else if (media.file) {
      store.set("websize", $("#m-websize").checked ? "1" : "0");
      say(`Adding ${media.file.name}…`);
      [name] = await upload([media.file], media.kind === "image" && $("#m-websize").checked);
    }
    if (!name) { say("Pick a file first", "error"); return; }
    const attrs = [];
    if ($("#m-wide").checked) attrs.push(".wide");
    if (media.kind === "image" && $("#m-pixel").checked) attrs.push(".pixel");
    if (media.kind === "video" && $("#m-loop").checked && !url) attrs.push(".loop");
    const md = `![${alt}](${name}${caption ? ` "${caption}"` : ""})${attrs.length ? `{${attrs.join(" ")}}` : ""}`;
    $("#dlg-media").close();
    insertBlock(md, alt ? md.length : 2);
    say(alt || media.kind === "video" ? `Inserted ${name}` : `Inserted ${name}. Add alt text between the [ ]`, "ok");
  } catch (e) { fail(e); }
}

// ---------- preview ----------

let previewTimer = null;
let previewSeq = 0;
let frameReady = false;
let frameLoading = false;
let patchPending = false;

function schedulePreview() {
  clearTimeout(previewTimer);
  previewTimer = setTimeout(() => refreshPreview(), 160);
}

async function refreshPreview({ reload = false } = {}) {
  if (!state.slug) return;
  const seq = ++previewSeq;
  let r;
  try {
    r = await api("POST", `/_api/preview/${state.slug}`, payload());
  } catch (e) { fail(e); return; }
  if (seq !== previewSeq) return; // a newer render is on its way
  showIssues(r.errors, r.warnings);

  const path = `/_preview/${state.slug}/`;
  let doc = null;
  try { doc = el.frame.contentDocument; } catch { /* not ours */ }
  const onPage = doc && frameReady && el.frame.contentWindow.location.pathname === path;
  if (reload || !onPage) {
    if (frameLoading && !reload && el.frame.dataset.path === path) { patchPending = true; return; }
    frameReady = false; frameLoading = true; patchPending = false;
    el.frame.dataset.path = path;
    // replace() so previews don't pile up in the browser's back history
    if (doc && el.frame.contentWindow.location.href !== "about:blank") el.frame.contentWindow.location.replace(path);
    else el.frame.src = path;
    return;
  }
  const fresh = new DOMParser().parseFromString(r.html, "text/html");
  doc.title = fresh.title;
  patchChildren(doc.body, fresh.body, doc);
  requestAnimationFrame(syncScroll);
}

el.frame.addEventListener("load", () => {
  frameLoading = false;
  let doc;
  try { doc = el.frame.contentDocument; } catch { return; }
  if (!doc) return;
  frameReady = true;
  // Links in the preview open in a new tab; in-page anchors (footnotes) stay.
  doc.addEventListener("click", (e) => {
    const a = e.target.closest?.("a[href]");
    if (!a) return;
    const url = new URL(a.getAttribute("href"), doc.baseURI);
    if (url.origin === location.origin && url.pathname === el.frame.contentWindow.location.pathname && url.hash) return;
    e.preventDefault();
    window.open(url.href, "_blank", "noopener");
  });
  measureLines();
  syncScroll();
  if (patchPending) { patchPending = false; refreshPreview(); }
});

// Update the preview in place: keep every node that didn't change, so
// images don't flicker, videos keep playing and the scroll stays put.
const lineless = (n) => (n.nodeType === 1 ? n.outerHTML.replace(/ data-line="\d+"/g, "") : n.nodeType + ":" + n.textContent);

function sameAttrs(a, b) {
  const names = (n) => [...n.attributes].map((x) => x.name).filter((x) => x !== "data-line");
  const an = names(a);
  return an.length === names(b).length && an.every((x) => a.getAttribute(x) === b.getAttribute(x));
}

function copyLines(from, to) {
  if (from.nodeType !== 1) return;
  if (from.hasAttribute("data-line")) to.setAttribute("data-line", from.getAttribute("data-line"));
  const a = from.querySelectorAll("[data-line]"), b = to.querySelectorAll("[data-line]");
  b.forEach((node, i) => a[i] && node.setAttribute("data-line", a[i].getAttribute("data-line")));
}

function patchChildren(oldParent, newParent, doc) {
  const olds = [...oldParent.childNodes], news = [...newParent.childNodes];
  let s = 0;
  while (s < olds.length && s < news.length && lineless(olds[s]) === lineless(news[s])) { copyLines(news[s], olds[s]); s++; }
  let eo = olds.length - 1, en = news.length - 1;
  while (eo >= s && en >= s && lineless(olds[eo]) === lineless(news[en])) { copyLines(news[en], olds[eo]); eo--; en--; }
  if (eo === s && en === s && olds[s].nodeType === 1 && news[s].nodeType === 1 &&
      olds[s].tagName === news[s].tagName && sameAttrs(olds[s], news[s]) &&
      !["VIDEO", "IFRAME", "IMG", "math"].includes(olds[s].tagName)) {
    if (news[s].hasAttribute("data-line")) olds[s].setAttribute("data-line", news[s].getAttribute("data-line"));
    patchChildren(olds[s], news[s], doc);
    return;
  }
  const ref = olds[eo + 1] || null;
  for (let i = s; i <= eo; i++) olds[i].remove();
  for (let i = s; i <= en; i++) oldParent.insertBefore(doc.importNode(news[i], true), ref);
}

function showIssues(errors = [], warnings = []) {
  const btn = el.issuesBtn;
  const n = errors.length + warnings.length;
  btn.className = "issues " + (errors.length ? "err" : warnings.length ? "warn" : "ok");
  const plural = (k, w) => `${k} ${w}${k === 1 ? "" : "s"}`;
  btn.textContent = !n ? "No problems"
    : [errors.length && plural(errors.length, "error"), warnings.length && plural(warnings.length, "warning")].filter(Boolean).join(" · ");
  el.issues.replaceChildren(...[...errors.map((t) => ["err", t]), ...warnings.map((t) => ["warn", t])].map(([k, t]) => {
    const li = document.createElement("li");
    li.className = k;
    li.textContent = t;
    const m = /^line (\d+):/.exec(t);
    if (m) { li.dataset.line = m[1]; li.title = "Go to line " + m[1]; }
    return li;
  }));
  if (!n) el.issues.hidden = true;
  btn.setAttribute("aria-expanded", String(!el.issues.hidden));
}

// ---------- scroll sync ----------
// A hidden copy of the textarea gives the pixel top of every source line
// (lines wrap, so they aren't evenly spaced). The preview marks each block
// with the line it starts on; together they map one scroll position to the other.

const mirror = document.createElement("div");
mirror.className = "mirror";
mirror.setAttribute("aria-hidden", "true");
$(".src-wrap").append(mirror);
let lineTops = [];

function measureLines() {
  const src = el.src;
  const cs = getComputedStyle(src);
  mirror.style.width = src.clientWidth + "px"; // content + padding, not the scrollbar
  mirror.style.boxSizing = "border-box";
  const lines = src.value.split("\n");
  const frag = document.createDocumentFragment();
  for (const line of lines) {
    const d = document.createElement("div");
    d.textContent = line || "​";
    frag.append(d);
  }
  mirror.replaceChildren(frag);
  const pad = parseFloat(cs.paddingTop);
  lineTops = [...mirror.children].map((d) => d.offsetTop - pad);
  mirror.replaceChildren();
}

let syncing = false;
function syncScroll() {
  if (syncing) return;
  syncing = true;
  requestAnimationFrame(() => {
    syncing = false;
    let doc, win;
    try { doc = el.frame.contentDocument; win = el.frame.contentWindow; } catch { return; }
    if (!frameReady || !doc?.body || !lineTops.length) return;
    const src = el.src;
    const header = doc.querySelector(".site-header")?.offsetHeight || 0;
    const anchors = [[0, 0]];
    for (const block of doc.querySelectorAll("[data-line]")) {
      const line = +block.dataset.line;
      if (!(line < lineTops.length)) continue;
      const e = lineTops[line];
      const p = block.getBoundingClientRect().top + win.scrollY - header - 16;
      const last = anchors[anchors.length - 1];
      if (e > last[0] && p > last[1]) anchors.push([e, p]);
    }
    const eMax = src.scrollHeight - src.clientHeight;
    const pMax = doc.documentElement.scrollHeight - win.innerHeight;
    const last = anchors[anchors.length - 1];
    if (eMax > last[0]) anchors.push([eMax, Math.max(pMax, last[1])]);
    const y = src.scrollTop;
    let i = 0;
    while (i < anchors.length - 2 && anchors[i + 1][0] <= y) i++;
    const [e0, p0] = anchors[i];
    const [e1, p1] = anchors[i + 1] || anchors[i];
    const t = e1 > e0 ? Math.min(1, Math.max(0, (y - e0) / (e1 - e0))) : 0;
    // "instant": the site's CSS asks for smooth scrolling, which would lag behind the text
    win.scrollTo({ top: p0 + t * (p1 - p0), behavior: "instant" });
  });
}

function goToLine(n) {
  const lines = el.src.value.split("\n");
  const at = lines.slice(0, n - 1).reduce((sum, l) => sum + l.length + 1, 0);
  el.src.focus();
  el.src.setSelectionRange(at, at + (lines[n - 1] || "").length);
  measureLines();
  el.src.scrollTop = Math.max(0, (lineTops[n - 1] || 0) - el.src.clientHeight / 3);
}

// ---------- layout: split and preview width ----------

function setSplit(pct) {
  pct = Math.min(75, Math.max(25, pct));
  document.documentElement.style.setProperty("--split", pct + "%");
  store.set("split", String(pct));
}

function setWidth(w) {
  el.frameWrap.classList.toggle("phone", w === "phone");
  $$("[data-width]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.width === w)));
  store.set("width", w);
  setTimeout(syncScroll, 50);
}

function countWords() {
  const words = (el.src.value.replace(/\$\$[\s\S]*?\$\$|```[\s\S]*?```/g, " ").match(/[\p{L}\p{N}’'-]+/gu) || []).length;
  el.words.textContent = `${words.toLocaleString()} words · ${Math.max(1, Math.round(words / 230))} min read`;
}

// ---------- wiring ----------

function onEdit() {
  if (!state.dirty) setDirty(true);
  schedulePreview();
}

let measureTimer = null;
el.src.addEventListener("input", () => {
  onEdit();
  countWords();
  clearTimeout(measureTimer);
  measureTimer = setTimeout(measureLines, 150);
});
for (const f of [el.title, el.date, el.summary, el.cover]) f.addEventListener("input", onEdit);
el.title.addEventListener("input", () => { document.title = `${el.title.value || "Untitled"} — Blog editor`; });
el.slug.addEventListener("input", () => {
  el.slug.value = el.slug.value.toLowerCase().replace(/[^a-z0-9-]+/g, "-");
  updateChrome();
});
el.slug.addEventListener("keydown", (e) => { if (e.key === "Enter" && !el.rename.hidden) { e.preventDefault(); renameSlug(); } });
el.rename.addEventListener("click", renameSlug);
el.src.addEventListener("scroll", syncScroll, { passive: true });
new ResizeObserver(() => { measureLines(); syncScroll(); }).observe(el.src);

for (const b of $$(".toolbar [data-cmd]")) {
  b.addEventListener("mousedown", (e) => e.preventDefault()); // keep the selection in the text
  b.addEventListener("click", () => commands[b.dataset.cmd]());
}

el.src.addEventListener("keydown", (e) => {
  if (!(e.ctrlKey || e.metaKey) || e.altKey) return;
  const cmd = { b: "bold", i: "italic", k: "link" }[e.key.toLowerCase()];
  if (cmd && !e.shiftKey) { e.preventDefault(); commands[cmd](); }
});
document.addEventListener("keydown", (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "s") { e.preventDefault(); saveDraft(); }
});

// Paste or drop files straight into the text.
el.src.addEventListener("paste", (e) => {
  const files = [...(e.clipboardData?.files || [])];
  if (files.length) { e.preventDefault(); uploadAndInsert(files); }
});
const srcWrap = $(".src-wrap");
el.src.addEventListener("dragover", (e) => {
  if (![...e.dataTransfer.types].includes("Files")) return;
  e.preventDefault();
  srcWrap.classList.add("drop");
});
el.src.addEventListener("dragleave", () => srcWrap.classList.remove("drop"));
el.src.addEventListener("drop", (e) => {
  srcWrap.classList.remove("drop");
  if (!e.dataTransfer.files.length) return;
  e.preventDefault();
  uploadAndInsert([...e.dataTransfer.files]);
});

el.save.addEventListener("click", saveDraft);
el.publish.addEventListener("click", publish);
$("#m-discard").addEventListener("click", discardDraft);
$("#m-unpublish").addEventListener("click", unpublish);
document.addEventListener("click", (e) => { if (el.more.open && !el.more.contains(e.target)) el.more.open = false; });
$("#btn-posts").addEventListener("click", showPosts);
$("#btn-new").addEventListener("click", newPost);
$("#new-title").addEventListener("keydown", (e) => { if (e.key === "Enter") { e.preventDefault(); newPost(); } });
$("#btn-reload").addEventListener("click", () => refreshPreview({ reload: true }));
el.issuesBtn.addEventListener("click", () => {
  if (!el.issues.children.length) return;
  el.issues.hidden = !el.issues.hidden;
  el.issuesBtn.setAttribute("aria-expanded", String(!el.issues.hidden));
});
el.issues.addEventListener("click", (e) => {
  const li = e.target.closest("li[data-line]");
  if (li) goToLine(+li.dataset.line);
});
$$("[data-width]").forEach((b) => b.addEventListener("click", () => setWidth(b.dataset.width)));

// media dialog
$("#m-file").addEventListener("change", (e) => chooseMediaFile(e.target.files[0]));
const drop = $("#m-drop");
drop.addEventListener("dragover", (e) => { e.preventDefault(); drop.classList.add("over"); });
drop.addEventListener("dragleave", () => drop.classList.remove("over"));
drop.addEventListener("drop", (e) => { e.preventDefault(); drop.classList.remove("over"); chooseMediaFile(e.dataTransfer.files[0]); });
$("#m-url").addEventListener("input", () => {
  media.file = null; media.existing = null;
  $$("#m-existing button").forEach((x) => x.setAttribute("aria-pressed", "false"));
  $("#m-drop").classList.remove("chosen");
});
$("#media-form").addEventListener("submit", (e) => { e.preventDefault(); insertMedia(); });
$("#m-cancel").addEventListener("click", () => $("#dlg-media").close());

// the divider
const divider = $("#divider");
divider.addEventListener("pointerdown", (e) => {
  divider.setPointerCapture(e.pointerId);
  divider.classList.add("dragging");
  document.body.classList.add("dragging");
});
divider.addEventListener("pointermove", (e) => {
  if (!divider.hasPointerCapture(e.pointerId)) return;
  setSplit((e.clientX / window.innerWidth) * 100);
});
divider.addEventListener("pointerup", (e) => {
  divider.releasePointerCapture(e.pointerId);
  divider.classList.remove("dragging");
  document.body.classList.remove("dragging");
});
divider.addEventListener("keydown", (e) => {
  const cur = parseFloat(getComputedStyle(document.documentElement).getPropertyValue("--split")) || 46;
  if (e.key === "ArrowLeft") setSplit(cur - 2);
  if (e.key === "ArrowRight") setSplit(cur + 2);
});

window.addEventListener("beforeunload", (e) => {
  if (state.dirty) { e.preventDefault(); e.returnValue = ""; }
});
window.addEventListener("hashchange", () => {
  const slug = location.hash.slice(1);
  if (slug && slug !== state.slug) openPost(slug);
});

// ---------- start ----------

(async function start() {
  const split = parseFloat(store.get("split"));
  if (split) setSplit(split);
  setWidth(store.get("width", "desktop"));
  try {
    const { posts } = await api("GET", "/_api/posts");
    let slug = location.hash.slice(1) || store.get("last");
    if (!posts.some((p) => p.slug === slug)) slug = posts[0]?.slug;
    if (slug) await openPost(slug, { force: true });
    else { say("No posts yet — start one"); updateChrome(); showPosts(); }
  } catch (e) { fail(e); }
})();
