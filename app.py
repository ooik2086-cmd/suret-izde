# -*- coding: utf-8 -*-
"""
Суретті интернеттен іздеу — МОБИЛЬДІК веб-нұсқа (қазақша / орысша).

Телефонда:
  • Компьютерде іске қосыңыз:   python app.py
  • Телефонды компьютермен бір Wi-Fi-ға қосыңыз
  • Браузерде ашыңыз:  http://<КОМПЬЮТЕР_IP>:5000
    (IP-ді көру: терезеде басталғанда жазылады)

Немесе Render-ге жайғастырып, кез келген жерден ашуға болады.
"""

import os
import sys
import ssl
import uuid
import urllib.request

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from flask import Flask, request, jsonify, Response

app = Flask(__name__)


# ─────────────────── фотоны ашық хостқа жүктеу (сервер жағында) ───────────────────
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


def _post(url, boundary, body, ctx):
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "multipart/form-data; boundary=%s" % boundary,
                 "User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, context=ctx, timeout=90).read().decode().strip()


def upload_image(raw):
    contexts = [ssl.create_default_context(), _insecure_ctx()]
    last = ""
    hosts = [
        ("https://catbox.moe/user/api.php",
         {"reqtype": "fileupload", "userhash": ""},
         {"fileToUpload": ("face.jpg", raw, "image/jpeg")}),
        ("https://0x0.st",
         {},
         {"file": ("face.jpg", raw, "image/jpeg")}),
    ]
    for url, fields, files in hosts:
        boundary, body = _multipart(fields, files)
        for ctx in contexts:
            try:
                r = _post(url, boundary, body, ctx)
                if r.startswith("http"):
                    return r
                last = r
            except Exception as e:
                last = str(e)
    raise RuntimeError(last or "upload failed")


@app.route("/upload", methods=["POST"])
def upload():
    f = request.files.get("photo")
    if not f:
        return jsonify(error="no file"), 400
    try:
        url = upload_image(f.read())
        return jsonify(url=url)
    except Exception as e:
        return jsonify(error=str(e)), 500


@app.route("/")
def index():
    return Response(PAGE, mimetype="text/html")


# ─────────────────────────── мобильдік бет ───────────────────────────
PAGE = r"""<!DOCTYPE html>
<html lang="kk">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
<meta name="theme-color" content="#111827">
<title>Суретті іздеу</title>
<style>
  :root{ --bg:#f4f5f7; --card:#fff; --ink:#1f2937; --muted:#6b7280;
         --line:#e5e7eb; --header:#111827; --blue:#2563eb; --blue2:#1d4ed8;
         --gray:#cbd5e1; --ghost:#eef1f5; }
  *{ box-sizing:border-box; -webkit-tap-highlight-color:transparent; }
  body{ margin:0; background:var(--bg); color:var(--ink);
        font-family:-apple-system,"Segoe UI",Roboto,system-ui,sans-serif; }
  header{ background:var(--header); color:#fff; padding:18px 16px;
          position:sticky; top:0; z-index:10; }
  .htop{ display:flex; align-items:center; justify-content:space-between; gap:10px; }
  .htop h1{ font-size:18px; margin:0; font-weight:700; }
  .sub{ color:#9ca3af; font-size:12.5px; margin-top:6px; }
  .lang{ display:flex; gap:6px; flex:none; }
  .lang button{ border:0; border-radius:8px; padding:6px 12px; font-weight:700;
                font-size:13px; cursor:pointer; background:#374151; color:#d1d5db; }
  .lang button.active{ background:#fff; color:var(--header); }
  main{ padding:14px; max-width:560px; margin:0 auto; }
  .card{ background:var(--card); border:1px solid var(--line); border-radius:14px;
         padding:16px; margin-bottom:14px; }
  .card h2{ font-size:15.5px; margin:0 0 4px; }
  .card p{ font-size:12.5px; color:var(--muted); margin:0 0 12px; }
  .row1{ display:flex; gap:12px; align-items:center; }
  .preview{ width:96px; height:96px; flex:none; border-radius:12px; border:1px solid var(--line);
            background:#e9ebef url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="96" height="96"><rect x="22" y="22" width="52" height="52" rx="8" fill="none" stroke="%23b6bcc6" stroke-width="3"/><circle cx="38" cy="38" r="7" fill="%23b6bcc6"/><polygon points="26,72 44,50 62,72" fill="%23b6bcc6"/></svg>') center/cover no-repeat; }
  .preview img{ width:100%; height:100%; object-fit:cover; border-radius:12px; }
  .grow{ flex:1; }
  .btn{ display:flex; align-items:center; justify-content:center; gap:8px; width:100%;
        border:0; border-radius:12px; padding:14px; font-size:15px; font-weight:700;
        color:#fff; background:var(--blue); cursor:pointer; }
  .btn:active{ background:var(--blue2); }
  .btn.ghost{ background:var(--ghost); color:var(--ink); }
  .btn.disabled{ background:var(--gray); pointer-events:none; }
  .hint{ font-size:11px; color:var(--muted); margin-top:6px; }
  .status{ font-size:12.5px; margin-top:10px; min-height:16px; }
  .status.ok{ color:#16a34a; } .status.warn{ color:#a16207; } .status.err{ color:#dc2626; }
  .label{ font-size:12px; font-weight:700; color:var(--muted); margin:12px 0 6px; }
  .gridb{ display:grid; grid-template-columns:repeat(2,1fr); gap:8px; }
  .gridb.three{ grid-template-columns:repeat(3,1fr); }
  .gridb .btn{ padding:13px 6px; font-size:13.5px; }
  input[type=text]{ width:100%; border:1px solid var(--line); border-radius:10px;
                    padding:13px; font-size:15px; margin-bottom:10px; }
  .file{ display:none; }
  .spin{ display:inline-block; width:14px; height:14px; border:2px solid #fff;
         border-top-color:transparent; border-radius:50%; animation:s .8s linear infinite;
         vertical-align:-2px; margin-right:6px; }
  @keyframes s{ to{ transform:rotate(360deg); } }
  footer{ text-align:center; color:var(--muted); font-size:11px; padding:8px 0 24px; }
</style>
</head>
<body>
<header>
  <div class="htop">
    <h1>🔎 <span data-t="title"></span></h1>
    <div class="lang">
      <button id="kz" class="active" onclick="setLang('kz')">KZ</button>
      <button id="ru" onclick="setLang('ru')">RU</button>
    </div>
  </div>
  <div class="sub" data-t="subtitle"></div>
</header>

<main>
  <!-- 1-қадам -->
  <div class="card">
    <h2 data-t="s1_title"></h2>
    <p data-t="s1_desc"></p>
    <div class="row1">
      <div class="preview" id="prev"></div>
      <div class="grow">
        <button class="btn" onclick="document.getElementById('file').click()">
          📁 <span data-t="pick"></span>
        </button>
        <div class="hint">JPG · PNG · WEBP</div>
      </div>
    </div>
    <input type="file" id="file" class="file" accept="image/*" onchange="onPick(event)">
    <div class="status" id="st1"></div>
  </div>

  <!-- 2-қадам -->
  <div class="card">
    <h2 data-t="s2_title"></h2>
    <p data-t="s2_desc"></p>
    <div class="label" data-t="auto_lbl"></div>
    <div class="gridb" id="autoRow"></div>
    <div class="label" data-t="face_lbl"></div>
    <div class="gridb" id="faceRow"></div>
  </div>

  <!-- 3-қадам -->
  <div class="card">
    <h2 data-t="s3_title"></h2>
    <p data-t="s3_desc"></p>
    <input type="text" id="name" />
    <div class="gridb three" id="netRow"></div>
    <button class="btn" onclick="openAll()">🌐 <span data-t="all"></span></button>
  </div>

  <footer>© Search Helper</footer>
</main>

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
 kz:{ title:"Суретті интернеттен іздеу", subtitle:"Фотоңызды таңдап, бір рет басып, желіден іздеңіз.",
  s1_title:"1-қадам — фотоны дайындау", s1_desc:"Іздегіңіз келетін фотоны таңдаңыз — ол серверге жүктеледі.",
  pick:"Фото таңдау", s2_title:"2-қадам — суретпен іздеу", s2_desc:"Бір адамды бірнеше жүйеден қатар іздеуге болады.",
  auto_lbl:"🤖 Автоматты (фото жүктелген соң қосылады):", face_lbl:"👤 Бет іздеу сайттары (фотоны өзіңіз жүктейсіз):",
  s3_title:"3-қадам — есіммен іздеу", s3_desc:"Аты-жөнін жазып, бір желіні немесе «барлығын» басыңыз.",
  name_ph:"Аты-жөні...", all:"Барлық желіден іздеу",
  uploading:"Фото жүктелуде...", done:"✅ Дайын! Енді 2-қадамдағы түймелерді басыңыз.",
  err:"Қате: ", need_prep:"Алдымен фотоны дайындаңыз.", need_name:"Алдымен аты-жөнін жазыңыз." },
 ru:{ title:"Поиск по фото в интернете", subtitle:"Выберите фото, нажмите один раз — и ищите в сети.",
  s1_title:"Шаг 1 — подготовка фото", s1_desc:"Выберите фото для поиска — оно загрузится на сервер.",
  pick:"Выбрать фото", s2_title:"Шаг 2 — поиск по фото", s2_desc:"Одного человека можно искать сразу в нескольких системах.",
  auto_lbl:"🤖 Автоматически (после загрузки фото):", face_lbl:"👤 Сайты поиска по лицу (фото загружаете сами):",
  s3_title:"Шаг 3 — поиск по имени", s3_desc:"Введите имя и нажмите одну сеть или «все».",
  name_ph:"Имя и фамилия...", all:"Искать во всех сетях",
  uploading:"Загрузка фото...", done:"✅ Готово! Теперь нажмите кнопки шага 2.",
  err:"Ошибка: ", need_prep:"Сначала подготовьте фото.", need_name:"Сначала введите имя." }
};

let lang="kz", imageUrl=null;

function tr(){ const d=T[lang];
  document.querySelectorAll("[data-t]").forEach(el=>{ el.textContent=d[el.dataset.t]||""; });
  document.getElementById("name").placeholder=d.name_ph;
  document.documentElement.lang = (lang==="kz")?"kk":"ru";
}
function setLang(l){ lang=l;
  document.getElementById("kz").classList.toggle("active", l==="kz");
  document.getElementById("ru").classList.toggle("active", l==="ru");
  tr();
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

function st(msg,cls){ const e=document.getElementById("st1"); e.textContent=msg; e.className="status "+(cls||""); }

function onPick(ev){
  const f=ev.target.files[0]; if(!f) return;
  // превью
  const prev=document.getElementById("prev");
  const reader=new FileReader();
  reader.onload=e=>{ prev.innerHTML='<img src="'+e.target.result+'">'; };
  reader.readAsDataURL(f);
  // жүктеу
  imageUrl=null; setAuto(false);
  st('<span class="spin"></span>'+T[lang].uploading,"warn");
  document.getElementById("st1").innerHTML='<span class="spin"></span>'+T[lang].uploading;
  const fd=new FormData(); fd.append("photo",f);
  fetch("/upload",{method:"POST",body:fd}).then(r=>r.json()).then(j=>{
    if(j.url){ imageUrl=j.url; setAuto(true); st(T[lang].done,"ok"); }
    else { st(T[lang].err+(j.error||"?"),"err"); }
  }).catch(e=>st(T[lang].err+e,"err"));
}

function setAuto(on){
  document.querySelectorAll("#autoRow .btn").forEach(b=>{
    b.classList.toggle("disabled",!on);
  });
}

function reverse(eng){
  if(!imageUrl){ alert(T[lang].need_prep); return; }
  const u=encodeURIComponent(imageUrl);
  window.open(ENGINES[eng].replace("{u}",u),"_blank");
}
function getName(){ const n=document.getElementById("name").value.trim();
  if(!n){ alert(T[lang].need_name); return null; } return encodeURIComponent(n); }
function openOne(tmpl){ const q=getName(); if(q) window.open(tmpl.replace("{q}",q),"_blank"); }
function openAll(){ const q=getName(); if(!q) return;
  // синхронды ашамыз — мобиль браузерлердің popup-бұғаттауын азайтады
  NETS.forEach(([l,t])=>{ window.open(t.replace("{q}",q),"_blank"); }); }

buildButtons(); tr();
</script>
</body>
</html>"""


if __name__ == "__main__":
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
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
