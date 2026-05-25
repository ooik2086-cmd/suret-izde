# -*- coding: utf-8 -*-
"""
Суретті/есіммен интернеттен іздеу — мобильдік веб-қолданба (KZ / RU / EN).

Мүмкіндіктер:
  • Сурет, есім немесе екеуімен бірге іздеу
  • Кез келген фотоны сенімді жүктеу (бірнеше серверге қайталап)
  • Телефонға орнатуға болады (PWA — "Жүктеу/Орнату" батырмасы)
  • 3 тіл: қазақ / орыс / ағылшын
  • Заманауи дизайн (градиент фон, шыны эффект)

Жергілікті іске қосу:  python app.py
"""

import os
import sys
import ssl
import json
import time
import uuid
import urllib.request

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from flask import Flask, request, jsonify, Response, send_file

app = Flask(__name__)
BASE = os.path.dirname(os.path.abspath(__file__))


# ─────────────────── фотоны ашық хостқа жүктеу (қайталаулы, сенімді) ───────────────────
def _insecure_ctx():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _multipart(fields, files):
    boundary = "----" + uuid.uuid4().hex
    body = b""
    for name, val in fields.items():
        body += ("--%s\r\nContent-Disposition: form-data; name=\"%s\"\r\n\r\n%s\r\n"
                 % (boundary, name, val)).encode()
    for name, (filename, content, ctype) in files.items():
        body += ("--%s\r\nContent-Disposition: form-data; name=\"%s\"; filename=\"%s\"\r\n"
                 "Content-Type: %s\r\n\r\n" % (boundary, name, filename, ctype)).encode()
        body += content + b"\r\n"
    body += ("--%s--\r\n" % boundary).encode()
    return boundary, body


def _post(url, boundary, body, ctx, timeout=60):
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "multipart/form-data; boundary=%s" % boundary,
                 "User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, context=ctx, timeout=timeout).read().decode("utf-8", "ignore").strip()


def _p_plain(r):
    return r if r.startswith("http") else None


def _p_uguu(r):
    try:
        j = json.loads(r)
        return j["files"][0]["url"]
    except Exception:
        return None


def _p_tmpfiles(r):
    try:
        j = json.loads(r)
        u = j["data"]["url"]
        # tmpfiles.org/123/x.jpg -> tmpfiles.org/dl/123/x.jpg (тікелей жүктеу)
        return u.replace("tmpfiles.org/", "tmpfiles.org/dl/", 1)
    except Exception:
        return None


# (атау, URL, өрістер, файл өрісі, парсер)
UPLOAD_HOSTS = [
    ("catbox",   "https://catbox.moe/user/api.php", {"reqtype": "fileupload", "userhash": ""}, "fileToUpload", _p_plain),
    ("0x0",      "https://0x0.st",                  {},                                        "file",         _p_plain),
    ("uguu",     "https://uguu.se/upload.php",      {},                                        "files[]",      _p_uguu),
    ("tmpfiles", "https://tmpfiles.org/api/v1/upload", {},                                     "file",         _p_tmpfiles),
]


def upload_image(raw, filename="photo.jpg"):
    contexts = [ssl.create_default_context(), _insecure_ctx()]
    last = "белгісіз қате"
    for name, url, fields, filefield, parser in UPLOAD_HOSTS:
        for _ in range(2):  # әр хостқа 2 рет тырысамыз
            for ctx in contexts:
                try:
                    boundary, body = _multipart(fields, {filefield: (filename, raw, "image/jpeg")})
                    r = _post(url, boundary, body, ctx)
                    got = parser(r)
                    if got and got.startswith("http"):
                        return got
                    last = (r or "")[:200]
                except Exception as e:
                    last = str(e)
            time.sleep(0.8)
    raise RuntimeError(last)


@app.route("/upload", methods=["POST"])
def upload():
    f = request.files.get("photo")
    if not f:
        return jsonify(error="no file"), 400
    try:
        url = upload_image(f.read(), f.filename or "photo.jpg")
        return jsonify(url=url)
    except Exception as e:
        return jsonify(error=str(e)), 500


# ─────────────────────────── PWA (телефонға орнату) ───────────────────────────
MANIFEST = {
    "name": "Суретті іздеу",
    "short_name": "Іздеу",
    "start_url": "/",
    "scope": "/",
    "display": "standalone",
    "background_color": "#0f172a",
    "theme_color": "#0f172a",
    "icons": [
        {"src": "/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any maskable"},
        {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
    ],
}

SW_JS = """
const CACHE='izde-v2';
self.addEventListener('install', e=>{ self.skipWaiting(); });
self.addEventListener('activate', e=>{ self.clients.claim(); });
self.addEventListener('fetch', e=>{
  e.respondWith(fetch(e.request).then(r=>{
    const c=r.clone();
    if(e.request.method==='GET'){ caches.open(CACHE).then(ch=>ch.put(e.request,c)); }
    return r;
  }).catch(()=>caches.match(e.request)));
});
"""


@app.route("/manifest.webmanifest")
def manifest():
    return Response(json.dumps(MANIFEST), mimetype="application/manifest+json")


@app.route("/sw.js")
def sw():
    return Response(SW_JS, mimetype="application/javascript")


@app.route("/icon-192.png")
def icon192():
    return send_file(os.path.join(BASE, "icon-192.png"), mimetype="image/png")


@app.route("/icon-512.png")
def icon512():
    return send_file(os.path.join(BASE, "icon-512.png"), mimetype="image/png")


@app.route("/")
def index():
    return Response(PAGE, mimetype="text/html")


# ─────────────────────────── мобильдік бет ───────────────────────────
PAGE = r"""<!DOCTYPE html>
<html lang="kk">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#0f172a">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Іздеу">
<link rel="manifest" href="/manifest.webmanifest">
<link rel="apple-touch-icon" href="/icon-192.png">
<title>Суретті іздеу</title>
<style>
  :root{
    --ink:#f1f5f9; --muted:#9fb0c7; --line:rgba(255,255,255,.12);
    --card:rgba(255,255,255,.07); --glass:rgba(255,255,255,.10);
    --grad:linear-gradient(135deg,#2563eb,#4f46e5);
    --gray:rgba(255,255,255,.14);
  }
  *{ box-sizing:border-box; -webkit-tap-highlight-color:transparent; }
  html,body{ margin:0; }
  body{
    font-family:-apple-system,"Segoe UI",Roboto,system-ui,sans-serif;
    color:var(--ink); background:#0f172a; min-height:100vh;
  }
  body::before{
    content:""; position:fixed; inset:0; z-index:-1;
    background:
      radial-gradient(42% 35% at 12% 8%, rgba(37,99,235,.55), transparent 60%),
      radial-gradient(45% 38% at 88% 12%, rgba(139,92,246,.45), transparent 60%),
      radial-gradient(55% 45% at 50% 105%, rgba(14,165,233,.40), transparent 60%),
      #0b1222;
  }
  header{ padding:18px 16px calc(14px + env(safe-area-inset-top)); }
  .bar{ display:flex; align-items:center; justify-content:space-between; gap:10px; flex-wrap:wrap; }
  .brand{ font-size:19px; font-weight:800; letter-spacing:-.3px; }
  .actions{ display:flex; align-items:center; gap:8px; }
  .pill{ border:0; border-radius:11px; padding:8px 12px; font-weight:700; font-size:12.5px;
         cursor:pointer; background:var(--gray); color:#fff; display:inline-flex; align-items:center; gap:5px;
         backdrop-filter:blur(8px); }
  .pill:active{ transform:scale(.96); }
  .lang{ display:flex; gap:4px; }
  .lang button{ border:0; border-radius:9px; padding:7px 9px; font-weight:800; font-size:12px;
                background:rgba(255,255,255,.10); color:#cbd5e1; cursor:pointer; }
  .lang button.active{ background:#fff; color:#0f172a; }
  .sub{ color:var(--muted); font-size:13px; margin-top:8px; }
  main{ padding:6px 14px calc(30px + env(safe-area-inset-bottom)); max-width:560px; margin:0 auto; }
  .card{ background:var(--card); border:1px solid var(--line); border-radius:18px; padding:16px;
         margin-bottom:14px; backdrop-filter:blur(16px); -webkit-backdrop-filter:blur(16px);
         box-shadow:0 10px 30px rgba(0,0,0,.25); }
  .card h2{ font-size:16px; margin:0 0 4px; font-weight:800; }
  .card p{ font-size:12.5px; color:var(--muted); margin:0 0 12px; }
  .row1{ display:flex; gap:12px; align-items:center; }
  .preview{ width:92px; height:92px; flex:none; border-radius:14px; border:1px solid var(--line);
            background:rgba(255,255,255,.06) url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="92" height="92"><rect x="20" y="20" width="52" height="52" rx="9" fill="none" stroke="%237c89a0" stroke-width="3"/><circle cx="36" cy="37" r="7" fill="%237c89a0"/><polygon points="24,72 43,49 62,72" fill="%237c89a0"/></svg>') center/cover no-repeat; }
  .preview img{ width:100%; height:100%; object-fit:cover; border-radius:14px; }
  .grow{ flex:1; min-width:0; }
  .btn{ display:flex; align-items:center; justify-content:center; gap:8px; width:100%;
        border:0; border-radius:13px; padding:14px; font-size:15px; font-weight:800;
        color:#fff; background:var(--grad); cursor:pointer; }
  .btn:active{ transform:scale(.985); }
  .btn.ghost{ background:rgba(255,255,255,.10); color:var(--ink); border:1px solid var(--line); }
  .btn.disabled{ background:rgba(255,255,255,.10); color:#64748b; pointer-events:none; }
  .hint{ font-size:11px; color:var(--muted); margin-top:7px; }
  .status{ font-size:12.5px; margin-top:10px; min-height:16px; line-height:1.4; }
  .status.ok{ color:#34d399; } .status.warn{ color:#fbbf24; } .status.err{ color:#f87171; }
  .nlabel{ display:block; font-size:12.5px; font-weight:700; color:var(--muted); margin:16px 0 7px; }
  .text{ width:100%; border:1px solid var(--line); border-radius:12px; padding:13px;
         font-size:15px; background:rgba(255,255,255,.08); color:var(--ink); }
  .text::placeholder{ color:#7c89a0; }
  .seg{ display:flex; gap:6px; background:rgba(255,255,255,.06); padding:5px; border-radius:14px; margin:4px 0 14px; }
  .seg button{ flex:1; border:0; background:transparent; color:var(--muted); padding:11px 4px;
               border-radius:10px; font-weight:800; font-size:13px; cursor:pointer; }
  .seg button.active{ background:var(--grad); color:#fff; box-shadow:0 4px 14px rgba(37,99,235,.4); }
  .label{ font-size:12px; font-weight:700; color:var(--muted); margin:14px 0 7px; }
  .gridb{ display:grid; grid-template-columns:repeat(2,1fr); gap:8px; }
  .gridb.three{ grid-template-columns:repeat(3,1fr); }
  .gridb .btn{ padding:13px 6px; font-size:13px; }
  .wide{ margin-top:10px; }
  footer{ text-align:center; color:var(--muted); font-size:11px; padding:6px 0 20px; }
  .modal{ position:fixed; inset:0; background:rgba(0,0,0,.6); display:none; align-items:center;
          justify-content:center; padding:24px; z-index:50; }
  .modal.show{ display:flex; }
  .sheet{ background:#111c33; border:1px solid var(--line); border-radius:18px; padding:20px; max-width:340px; }
  .sheet h3{ margin:0 0 10px; font-size:16px; }
  .sheet p{ color:var(--muted); font-size:13.5px; line-height:1.5; margin:0 0 16px; }
</style>
</head>
<body>
<header>
  <div class="bar">
    <div class="brand">🔎 <span data-t="title"></span></div>
    <div class="actions">
      <button id="install" class="pill" onclick="installApp()">⬇️ <span data-t="install"></span></button>
      <div class="lang">
        <button data-l="kz" class="active" onclick="setLang('kz')">KZ</button>
        <button data-l="ru" onclick="setLang('ru')">RU</button>
        <button data-l="en" onclick="setLang('en')">EN</button>
      </div>
    </div>
  </div>
  <div class="sub" data-t="subtitle"></div>
</header>

<main>
  <!-- Деректер -->
  <div class="card">
    <h2 data-t="data_title"></h2>
    <p data-t="data_desc"></p>
    <div class="row1">
      <div class="preview" id="prev"></div>
      <div class="grow">
        <button class="btn" onclick="document.getElementById('file').click()">📁 <span data-t="pick"></span></button>
        <div class="hint">JPG · PNG · WEBP · HEIC</div>
      </div>
    </div>
    <input type="file" id="file" accept="image/*" hidden onchange="onPick(event)">
    <div class="status" id="st1"></div>

    <label class="nlabel" data-t="name_label"></label>
    <input type="text" id="name" class="text">
  </div>

  <!-- Іздеу -->
  <div class="card">
    <h2 data-t="search_title"></h2>
    <p data-t="search_desc"></p>
    <div class="seg">
      <button data-m="image" class="active" onclick="setMode('image')" data-t="mode_image"></button>
      <button data-m="name" onclick="setMode('name')" data-t="mode_name"></button>
      <button data-m="both" onclick="setMode('both')" data-t="mode_both"></button>
    </div>

    <div id="imgBlock">
      <div class="label" data-t="auto_lbl"></div>
      <div class="gridb" id="autoRow"></div>
      <div class="label" data-t="face_lbl"></div>
      <div class="gridb" id="faceRow"></div>
    </div>

    <div id="nameBlock" style="display:none">
      <div class="gridb three" id="netRow"></div>
      <button class="btn wide" onclick="openAllNames()">🌐 <span data-t="all_names"></span></button>
    </div>

    <div id="comboBlock" style="display:none">
      <button class="btn wide" onclick="searchAll()">🔍 <span data-t="search_all"></span></button>
    </div>
  </div>

  <footer>© Suret Izde</footer>
</main>

<!-- Орнату нұсқаулығы (iOS) -->
<div class="modal" id="instModal" onclick="this.classList.remove('show')">
  <div class="sheet" onclick="event.stopPropagation()">
    <h3 data-t="install"></h3>
    <p data-t="install_help"></p>
    <button class="btn" onclick="document.getElementById('instModal').classList.remove('show')">OK</button>
  </div>
</div>

<!-- Бұғатталған сілтемелер -->
<div class="modal" id="linksModal" onclick="this.classList.remove('show')">
  <div class="sheet" onclick="event.stopPropagation()">
    <h3 data-t="blocked_title"></h3>
    <p data-t="blocked_msg"></p>
    <div id="linksBox" style="display:flex;flex-direction:column;gap:8px;max-height:50vh;overflow:auto"></div>
  </div>
</div>

<script>
const ENGINES = {
  yandex:"https://yandex.com/images/search?rpt=imageview&url={u}",
  google:"https://lens.google.com/uploadbyurl?url={u}",
  bing:"https://www.bing.com/images/search?view=detailv2&iss=sbi&q=imgurl:{u}",
  tineye:"https://tineye.com/search?url={u}"
};
const AUTO = [["Yandex","yandex"],["Google","google"],["Bing","bing"],["TinEye","tineye"]];
const FACE = [["PimEyes","https://pimeyes.com/en"],["FaceCheck.ID","https://facecheck.id/"],
              ["Lenso.ai","https://lenso.ai/"],["Search4faces","https://search4faces.com/en/"]];
const NETS = [["TikTok","https://www.tiktok.com/search?q={q}"],
  ["Instagram","https://www.instagram.com/explore/search/keyword/?q={q}"],
  ["Facebook","https://www.facebook.com/search/top?q={q}"],
  ["VK","https://vk.com/search?c%5Bq%5D={q}&c%5Bsection%5D=auto"],
  ["OK.ru","https://ok.ru/search?st.query={q}"],
  ["YouTube","https://www.youtube.com/results?search_query={q}"],
  ["X","https://twitter.com/search?q={q}&f=user"],
  ["Threads","https://www.threads.net/search?q={q}"],
  ["LinkedIn","https://www.linkedin.com/search/results/all/?keywords={q}"],
  ["Google","https://www.google.com/search?q={q}"]];

const T = {
 kz:{ title:"Суретті іздеу", subtitle:"Сурет, есім немесе екеуімен бірге адамды интернеттен табыңыз.",
  install:"Орнату", data_title:"Дерек", data_desc:"Фото таңдаңыз және/немесе аты-жөнін жазыңыз.",
  pick:"Фото таңдау", name_label:"Аты-жөні (міндетті емес)", name_ph:"Мысалы: Арман Серіков",
  search_title:"Іздеу", search_desc:"Қалай іздейтініңізді таңдаңыз.",
  mode_image:"🖼️ Суретпен", mode_name:"📝 Атымен", mode_both:"🔍 Екеуімен",
  auto_lbl:"Автоматты (фото жүктелген соң қосылады):", face_lbl:"Бет іздеу сайттары (фотоны өзіңіз жүктейсіз):",
  all_names:"Барлық желіден іздеу",
  uploading:"Фото жүктелуде...", done:"✅ Фото дайын! Енді суретпен іздеуге болады.",
  err:"Қате: ", need_photo:"Алдымен фото таңдап, жүктелуін күтіңіз.", need_name:"Алдымен аты-жөнін жазыңыз.",
  install_help:"Орнату үшін: браузердің «Бөлісу» (Share ⬆️) белгішесін басып, «Бастапқы экранға қосу» (Add to Home Screen) дегенді таңдаңыз. Сонда қолданба телефоныңызға орнатылады.",
  search_all:"Барлығынан іздеу (сурет + есім)", need_any:"Алдымен фото немесе аты-жөнін қосыңыз.",
  blocked_title:"Сілтемелерді ашу", blocked_msg:"Браузер бірнеше терезені бірден ашуды бұғаттады. Төмендегі сілтемелерді бір-бірлеп басыңыз:" },
 ru:{ title:"Поиск по фото", subtitle:"Найдите человека по фото, имени или по обоим сразу.",
  install:"Установить", data_title:"Данные", data_desc:"Выберите фото и/или введите имя.",
  pick:"Выбрать фото", name_label:"Имя и фамилия (необязательно)", name_ph:"Например: Иван Петров",
  search_title:"Поиск", search_desc:"Выберите способ поиска.",
  mode_image:"🖼️ По фото", mode_name:"📝 По имени", mode_both:"🔍 Оба",
  auto_lbl:"Автоматически (после загрузки фото):", face_lbl:"Сайты поиска по лицу (фото загружаете сами):",
  all_names:"Искать во всех сетях",
  uploading:"Загрузка фото...", done:"✅ Фото готово! Теперь можно искать по фото.",
  err:"Ошибка: ", need_photo:"Сначала выберите фото и дождитесь загрузки.", need_name:"Сначала введите имя.",
  install_help:"Чтобы установить: нажмите «Поделиться» (Share ⬆️) в браузере и выберите «На экран Домой» (Add to Home Screen). Приложение установится на телефон.",
  search_all:"Искать везде (фото + имя)", need_any:"Сначала добавьте фото или имя.",
  blocked_title:"Открыть ссылки", blocked_msg:"Браузер заблокировал открытие нескольких вкладок. Нажимайте ссылки ниже по одной:" },
 en:{ title:"Photo Search", subtitle:"Find a person by photo, name, or both at once.",
  install:"Install", data_title:"Data", data_desc:"Pick a photo and/or enter a name.",
  pick:"Choose photo", name_label:"Full name (optional)", name_ph:"e.g. John Smith",
  search_title:"Search", search_desc:"Choose how to search.",
  mode_image:"🖼️ By photo", mode_name:"📝 By name", mode_both:"🔍 Both",
  auto_lbl:"Automatic (enabled after upload):", face_lbl:"Face search sites (you upload the photo):",
  all_names:"Search all networks",
  uploading:"Uploading photo...", done:"✅ Photo ready! You can now search by photo.",
  err:"Error: ", need_photo:"Choose a photo first and wait for upload.", need_name:"Enter a name first.",
  install_help:"To install: tap the browser Share button (⬆️) and choose 'Add to Home Screen'. The app will be installed on your phone.",
  search_all:"Search everywhere (photo + name)", need_any:"Add a photo or a name first.",
  blocked_title:"Open links", blocked_msg:"Your browser blocked opening multiple tabs. Tap the links below one by one:" }
};

let lang="kz", mode="image", imageUrl=null, deferredPrompt=null;

function tr(){ const d=T[lang];
  document.querySelectorAll("[data-t]").forEach(el=>{ el.textContent=d[el.dataset.t]||""; });
  document.getElementById("name").placeholder=d.name_ph;
  document.documentElement.lang = lang==="kz"?"kk":lang;
}
function setLang(l){ lang=l;
  document.querySelectorAll(".lang button").forEach(b=>b.classList.toggle("active", b.dataset.l===l));
  tr();
}
function setMode(m){ mode=m;
  document.querySelectorAll(".seg button").forEach(b=>b.classList.toggle("active", b.dataset.m===m));
  document.getElementById("imgBlock").style.display = (m==="image"||m==="both")?"block":"none";
  document.getElementById("nameBlock").style.display = (m==="name"||m==="both")?"block":"none";
  document.getElementById("comboBlock").style.display = (m==="both")?"block":"none";
}

// Бірнеше сілтемені ашу; браузер бұғаттаса — тізім көрсетеді
function openMany(urls){
  if(!urls.length) return;
  const blocked=[];
  urls.forEach(u=>{ const w=window.open(u,"_blank"); if(!w) blocked.push(u); });
  if(blocked.length) showLinks(blocked);
}
function hostName(u){ try{ return new URL(u).hostname.replace("www.",""); }catch(e){ return u; } }
function showLinks(urls){
  const box=document.getElementById("linksBox"); box.innerHTML="";
  urls.forEach(u=>{ const a=document.createElement("a"); a.href=u; a.target="_blank"; a.rel="noopener";
    a.className="btn"; a.textContent="🔗 "+hostName(u); box.appendChild(a); });
  document.getElementById("linksModal").classList.add("show");
}

function buildButtons(){
  const auto=document.getElementById("autoRow");
  AUTO.forEach(([label,eng])=>{ const b=document.createElement("button");
    b.className="btn disabled"; b.textContent=label; b.dataset.eng=eng;
    b.onclick=()=>reverse(eng); auto.appendChild(b); });
  const face=document.getElementById("faceRow");
  FACE.forEach(([label,url])=>{ const b=document.createElement("button");
    b.className="btn"; b.textContent=label; b.onclick=()=>window.open(url,"_blank"); face.appendChild(b); });
  const net=document.getElementById("netRow");
  NETS.forEach(([label,tmpl])=>{ const b=document.createElement("button");
    b.className="btn ghost"; b.textContent=label; b.onclick=()=>openOne(tmpl); net.appendChild(b); });
}

function st(msg,cls){ const e=document.getElementById("st1"); e.innerHTML=msg; e.className="status "+(cls||""); }

function onPick(ev){
  const f=ev.target.files[0]; if(!f) return;
  const prev=document.getElementById("prev");
  const reader=new FileReader();
  reader.onload=e=>{ prev.innerHTML='<img src="'+e.target.result+'">'; };
  reader.readAsDataURL(f);
  imageUrl=null; setAuto(false);
  st('⏳ '+T[lang].uploading,"warn");
  const fd=new FormData(); fd.append("photo",f);
  fetch("/upload",{method:"POST",body:fd}).then(r=>r.json()).then(j=>{
    if(j.url){ imageUrl=j.url; setAuto(true); st(T[lang].done,"ok"); }
    else { st(T[lang].err+(j.error||"?"),"err"); }
  }).catch(e=>st(T[lang].err+e,"err"));
}
function setAuto(on){
  document.querySelectorAll("#autoRow .btn").forEach(b=>b.classList.toggle("disabled",!on));
}
function reverse(eng){
  if(!imageUrl){ alert(T[lang].need_photo); return; }
  window.open(ENGINES[eng].replace("{u}",encodeURIComponent(imageUrl)),"_blank");
}
function getName(){ const n=document.getElementById("name").value.trim();
  if(!n){ alert(T[lang].need_name); return null; } return encodeURIComponent(n); }
function openOne(tmpl){ const q=getName(); if(q) window.open(tmpl.replace("{q}",q),"_blank"); }
function openAllNames(){ const q=getName(); if(!q) return;
  openMany(NETS.map(([l,t])=>t.replace("{q}",q))); }

// Біріктіріп іздеу: сурет (Yandex/Google/Bing/TinEye) + барлық желі
function searchAll(){
  const urls=[];
  if(imageUrl){ for(const k in ENGINES){ urls.push(ENGINES[k].replace("{u}",encodeURIComponent(imageUrl))); } }
  const n=document.getElementById("name").value.trim();
  if(n){ const q=encodeURIComponent(n); NETS.forEach(([l,t])=>urls.push(t.replace("{q}",q))); }
  if(!urls.length){ alert(T[lang].need_any); return; }
  openMany(urls);
}

// ── PWA орнату ──
window.addEventListener("beforeinstallprompt", e=>{ e.preventDefault(); deferredPrompt=e; });
function installApp(){
  if(deferredPrompt){ deferredPrompt.prompt(); deferredPrompt=null; return; }
  document.getElementById("instModal").classList.add("show");  // iOS / қолдамаса — нұсқаулық
}
if("serviceWorker" in navigator){ navigator.serviceWorker.register("/sw.js").catch(()=>{}); }

buildButtons(); tr(); setMode("image");
</script>
</body>
</html>"""


if __name__ == "__main__":
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80)); ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    port = int(os.environ.get("PORT", 5000))
    print("=" * 48)
    print("  Телефоннан ашыңыз (бір Wi-Fi):")
    print("    http://%s:%d" % (ip, port))
    print("  Компьютерде:  http://127.0.0.1:%d" % port)
    print("=" * 48)
    app.run(host="0.0.0.0", port=port, debug=False)
