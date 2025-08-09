# Create a ready-to-install PWA package (index.html + manifest + service worker + icons) and zip it.
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os, json, zipfile, textwrap, pathlib

base_dir = "/mnt/data/keiko_pwa"
icons_dir = os.path.join(base_dir, "icons")
os.makedirs(icons_dir, exist_ok=True)

# Create simple dojo-style icons
def make_icon(size, filename, text="空手"):
    img = Image.new("RGBA", (size, size), (248, 245, 242, 255))  # washi-like background
    draw = ImageDraw.Draw(img)
    # red circle
    r = int(size * 0.36)
    center = (size//2, size//2)
    draw.ellipse([center[0]-r, center[1]-r, center[0]+r, center[1]+r], fill=(179,32,32,255))
    # attempt to draw text (fallback to no text if font not found)
    try:
        # Use a default font; PIL's default may not support Kanji, so just draw a simple white dot if not supported
        # We try to load a common sans font; if it fails, we skip drawing text.
        font_size = int(size * 0.26)
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
        # Draw text in white, centered
        w, h = draw.textsize(text, font=font)
        draw.text((center[0]-w/2, center[1]-h/2), text, font=font, fill=(255,255,255,255))
    except Exception:
        # draw small white highlight instead
        r2 = int(size * 0.08)
        draw.ellipse([center[0]-r2, center[1]-r2, center[0]+r2, center[1]+r2], fill=(255,255,255,220))
    img.save(os.path.join(icons_dir, filename))

# Generate required icons
make_icon(180, "apple-touch-icon-180.png")
make_icon(192, "icon-192.png")
make_icon(512, "icon-512.png")

# manifest.webmanifest
manifest = {
    "name": "Keiko Generator",
    "short_name": "Keiko",
    "description": "Zufällige Kihon-Kombinationen und Kata-Vorschläge – Für 3. Dan – DJKB (Stand: Juli 2013).",
    "start_url": "./",
    "scope": "./",
    "display": "standalone",
    "orientation": "portrait",
    "background_color": "#f8f5f2",
    "theme_color": "#111111",
    "icons": [
        {"src": "icons/icon-192.png", "sizes": "192x192", "type": "image/png"},
        {"src": "icons/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"}
    ]
}
with open(os.path.join(base_dir, "manifest.webmanifest"), "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)

# sw.js (simple cache-first with update)
sw_js = """
const CACHE = 'keiko-v1';
const ASSETS = [
  './',
  './index.html',
  './manifest.webmanifest',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/apple-touch-icon-180.png'
];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(ASSETS)));
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.map(k => (k === CACHE) ? null : caches.delete(k))))
  );
  self.clients.claim();
});

self.addEventListener('fetch', (e) => {
  const req = e.request;
  e.respondWith(
    caches.match(req).then(cached => cached || fetch(req))
  );
});
"""
with open(os.path.join(base_dir, "sw.js"), "w", encoding="utf-8") as f:
    f.write(sw_js.strip())

# index.html (using the latest HTML from the canvas, plus manifest & SW registration)
index_html = """<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
  <meta name="apple-mobile-web-app-capable" content="yes" />
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
  <meta name="apple-mobile-web-app-title" content="Keiko Generator" />
  <meta name="theme-color" content="#111111" />
  <link rel="manifest" href="manifest.webmanifest" />
  <link rel="apple-touch-icon" href="icons/apple-touch-icon-180.png" />
  <title>Karate Keiko Generator</title>
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Noto+Serif+JP:wght@400;600;700&family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
  <style>
    :root{
      --bg:#f8f5f2; --ink:#111; --crimson:#b32020; --crimson-dark:#7e1414;
      --line:#e8e3dd; --muted:#68615a; --radius:22px; --shadow:0 10px 18px rgba(0,0,0,.08), 0 3px 6px rgba(0,0,0,.06);
      --safe-top: env(safe-area-inset-top); --safe-bottom: env(safe-area-inset-bottom);
      --safe-left: env(safe-area-inset-left); --safe-right: env(safe-area-inset-right);
    }
    *{box-sizing:border-box} html,body{height:100%}
    body{margin:0; color:var(--ink); background:var(--bg);
      font-family:Inter, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, "Apple Color Emoji", "Segoe UI Emoji";
      -webkit-font-smoothing:antialiased; text-rendering:optimizeLegibility;
    }
    .app{min-height:100dvh; padding-top:calc(14px + var(--safe-top)); padding-bottom:calc(16px + var(--safe-bottom));
      padding-left:calc(12px + var(--safe-left)); padding-right:calc(12px + var(--safe-right));
      display:flex; flex-direction:column; align-items:stretch; gap:16px; position:relative;
      background:
        radial-gradient(1200px 600px at 110% -10%, rgba(179,32,32,.06), transparent 60%),
        radial-gradient(800px 500px at -10% -10%, rgba(0,0,0,.04), transparent 60%),
        var(--bg);
    }
    header{display:flex; align-items:center; gap:10px; padding:0 4px 6px 4px; position:relative; z-index:5;}
    .back{position:absolute; left:4px; top:0; transform:translateY(2px);
      appearance:none; border:0; background:transparent; padding:10px; margin:0; border-radius:14px;
      display:none; align-items:center; gap:8px; font-size:15px; color:var(--ink); z-index:10;}
    .back svg{width:18px;height:18px;display:block} .back:active{opacity:.7} .show-back .back{display:flex}
    .title-wrap{width:100%; display:flex; align-items:center; justify-content:center; position:relative;}
    .mon{font-family:"Noto Serif JP", serif; letter-spacing:2px; font-weight:700; font-size:22px;}
    .title{font-weight:700; font-size:18px; color:var(--muted);}
    .crest{position:absolute; inset:auto 0 auto auto; right:6px; top:-6px; opacity:.9; width:46px; height:46px; border-radius:50%;
      pointer-events:none; background:radial-gradient(circle at 50% 50%, rgba(179,32,32,.9) 0 48%, transparent 49% 100%),
      radial-gradient(circle at 50% 50%, rgba(0,0,0,.15) 0 55%, transparent 56% 100%); box-shadow:inset 0 0 0 2px rgba(0,0,0,.05);}
    main{flex:1; display:flex; flex-direction:column; gap:16px}
    .card{background:#fff; border-radius:var(--radius); box-shadow:var(--shadow); border:1px solid var(--line); overflow:hidden;}
    .card .inner{padding:16px}
    .hero{position:relative; overflow:hidden; max-width:520px; margin:0 auto;}
    .hero .inner{padding:18px 16px}
    .hero .brush{position:absolute; inset:0; pointer-events:none; opacity:.08;
      background:repeating-linear-gradient(105deg, transparent 0 18px, rgba(0,0,0,.6) 18px 19px, transparent 19px 40px); mix-blend-mode:multiply;}
    .h1{font-family:"Noto Serif JP", serif; font-weight:700; font-size:28px; line-height:1.15; margin:0 0 6px}
    .h2{font-family:"Noto Serif JP", serif; font-weight:600; font-size:18px; margin:0; color:var(--muted)}
    .meta{font-size:13px; color: var(--muted)}
    .grid{display:grid; grid-template-columns:1fr; gap:14px; padding:12px; max-width:520px; margin:0 auto;}
    .btn{appearance:none; border:0; width:100%; border-radius:18px; padding:16px 14px; text-align:left;
      background:linear-gradient(180deg, #fff 0%, #f7f4f1 100%); border:1px solid var(--line); box-shadow:var(--shadow); cursor:pointer;
      font-weight:700; font-size:18px; display:flex; align-items:center; gap:12px;}
    .btn:active{transform:translateY(1px)}
    .btn .icon{width:36px;height:36px;border-radius:12px;display:grid;place-items:center;
      background:radial-gradient(circle at 30% 30%, #fff, rgba(255,255,255,.8) 40%, rgba(255,255,255,.2) 100%), linear-gradient(180deg, var(--crimson), var(--crimson-dark));
      color:#fff; box-shadow:0 6px 12px rgba(179,32,32,.25), inset 0 0 0 1px rgba(255,255,255,.35);}
    .btn .caption{display:block; font-weight:600; font-size:12px; color:var(--muted)}
    .section-title{font-family:"Noto Serif JP", serif; font-size:16px; font-weight:700; letter-spacing:.6px;
      padding:10px 16px; border-bottom:1px solid var(--line); background:linear-gradient(180deg,#fff, #fbf9f7);}
    .list{list-style:none; padding:8px 12px 12px; margin:0; display:grid; gap:10px}
    .item{border:1px solid var(--line); border-radius:16px; overflow:hidden; background:#fff}
    .item .hdr{display:flex; align-items:center; gap:10px; padding:10px 12px; background:linear-gradient(180deg,#fff,#fbf9f7);}
    .item .num{width:28px;height:28px;border-radius:8px;display:grid;place-items:center;font-weight:700;font-size:14px;color:#fff;
      background:linear-gradient(180deg, var(--crimson), var(--crimson-dark)); box-shadow:inset 0 0 0 1px rgba(255,255,255,.35)}
    .item .ttl{font-weight:700}
    .item .steps{padding:8px 12px 12px; display:grid; gap:6px; font-size:15px; line-height:1.35; counter-reset: step;}
    .item .step{position:relative; padding-left:26px}
    .item .step:before{counter-increment: step; content: counter(step) '.'; position:absolute; left:4px; top:0; font-weight:700;}
    .toolbar{display:flex; align-items:center; justify-content:space-between; gap:8px; padding:12px 12px 0}
    .ghost{appearance:none; border:1px solid var(--line); background:#fff; border-radius:14px; padding:10px 12px; font-weight:600}
    .hidden{display:none !important}
    .screen{display:none} .screen.active{display:block}
    *{ -webkit-tap-highlight-color: rgba(0,0,0,0.05); } ::selection{ background: rgba(179,32,32,.18); }
    .tip{font-size:12px; color:var(--muted); text-align:center; padding:4px 8px} a{color:var(--crimson)}
  </style>
</head>
<body>
  <div id="app" class="app">
    <header id="appHeader">
      <button type="button" class="back" id="backBtn" aria-label="Zurück">
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
          <path d="M15 18l-6-6 6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <span>Zurück</span>
      </button>
      <div class="title-wrap">
        <div>
          <div class="mon" aria-label="Karate-do">空手道</div>
          <div class="title">Keiko Generator</div>
        </div>
        <div class="crest" aria-hidden="true"></div>
      </div>
    </header>

    <main>
      <section id="home" class="screen active">
        <div class="card hero">
          <div class="inner">
            <div class="h1">Wähle dein Training</div>
            <div class="h2">Zufällige Kihon‑Kombinationen oder Kata‑Vorschläge</div>
            <div class="meta">Für 3. Dan – DJKB (Stand: Juli 2013)</div>
          </div>
          <div class="brush" aria-hidden="true"></div>
        </div>

        <div class="grid">
          <button class="btn" id="btnKihon">
            <span class="icon" aria-hidden="true">型</span>
            <span class="label">Generate Kihon <span class="caption">5 zufällige Kombinationen</span></span>
          </button>

          <button class="btn" id="btnKata">
            <span class="icon" aria-hidden="true">拳</span>
            <span class="label">Generate Katas <span class="caption">Tokui + 3 Zufälle</span></span>
          </button>
        </div>

        <p class="tip">Tipp: In Safari öffnen → <em>Teilen → Zum Home‑Bildschirm</em> hinzufügen.</p>
      </section>

      <section id="kihon" class="screen">
        <div class="card">
          <div class="section-title">Kihon – 5 zufällige Kombinationen</div>
          <div class="toolbar">
            <button class="ghost" id="regenKihon">Neu würfeln</button>
            <div class="tip" aria-live="polite">Zufällig ausgewählt</div>
          </div>
          <div class="inner">
            <ol id="kihonList" class="list" aria-live="polite"></ol>
          </div>
        </div>
      </section>

      <section id="kata" class="screen">
        <div class="card">
          <div class="section-title">Kata – Vorschlag (4)</div>
          <div class="toolbar">
            <button class="ghost" id="regenKata">Neu würfeln</button>
            <div class="tip" aria-live="polite">Tokui + Zufallslisten</div>
          </div>
          <div class="inner">
            <ol id="kataList" class="list" aria-live="polite"></ol>
          </div>
        </div>
      </section>
    </main>
  </div>

  <script>
    const $ = (q)=>document.querySelector(q);
    const app = $('#app');
    const screens = { home: $('#home'), kihon: $('#kihon'), kata: $('#kata') };

    function showScreen(name){
      Object.values(screens).forEach(s=>s.classList.remove('active'));
      screens[name].classList.add('active');
      if(name === 'home') app.classList.remove('show-back'); else app.classList.add('show-back');
      try{window.scrollTo({top:0, behavior:'auto'});}catch(e){window.scrollTo(0,0);}
    }

    // Data
    const KIHON = [
      { id:1, lines:[
        'aus Gedan-Kamae links, vorwärts in Zk mit Sanbon-Zuki (Jodan/Chudan/Chudan)',
        'rückwärts in Zk mit Age-Uke/Mae-Geri/hinten absetzen mit Gyaku-Zuki in Zk'
      ]},
      { id:2, lines:[
        'vorwärts in Zk mit Soto-Uke/in Kb mit Yoko-Empi-Uchi/Tate-Uraken-Uchi/Gyaku-Zuki in Zk',
        'rückwärts in Zk mit Uchi-Uke/Kizami-Mae-Geri/Kizami-Zuki/Gyaku-Zuki in Zk'
      ]},
      { id:3, lines:[
        'vorwärts in Kk mit Shuto-Uke/Kizami-Mae-Geri/Nukite in Zk, Wendung mit Gedan-Barai in Zk',
        'aus Chudan-Kamae, vorwärts in Zk mit Mae-Geri/Kizami-Zuki/Gyaku-Zuki in Zk, Wendung mit Gedan-Barai in Zk'
      ]},
      { id:4, lines:[
        'aus Chudan-Kamae, vorwärts in Zk mit Mawashi-Geri, Wendung mit Gedan-Barai in Zk',
        'aus Chudan-Kamae, vorwärts in Zk mit Ren-Geri (Mawashi-Geri/mit gleichem Bein Yoko-Geri-Kekomi), Wendung mit Gedan-Barai in Zk'
      ]},
      { id:5, lines:[
        'aus Chudan-Kamae, vorwärts in Zk mit Ushiro-Geri, Wendung mit Gedan-Barai in Kb',
        'aus Chudan-Kamae, vorwärts in Kb mit Yoko-Geri-Keage/Drehung und mit hinterem Bein in Kb Yoko-Geri-Kekomi, mit gleichem Bein Yoko-Geri-Kekomi, Wendung mit Gedan-Barai in Zk'
      ]},
      { id:6, lines:[
        'Sonoba-Geri: (Standübung links und rechts) aus Zk und Chudan-Kamae: Mae-Geri nach vorne / mit gleichem Bein Yoko-Geri-Keage zur Seite / mit gleichem Bein Ushiro-Geri, nach hinten absetzen in Chudan-Kamae.'
      ]},
      { id:7, lines:[
        'aus Chudan-Kamae links, im Stand Jodan-Kizami-Zuki/vorwärts in Zk mit Sanbon-Zuki (Jodan/Chudan/Chudan) aus Chudan-Kamae rückwärts in Zk mit Uchi-Uke/Mae-Geri/hinten absetzen mit Kizami-Zuki/Gyaku-Zuki.'
      ]},
      { id:8, lines:[
        'aus Chudan-Kamae, einen Schritt zurück in Zk mit Age-Uke/vorwärts in Kb mit Mawashi-Geri/Tate-Uraken/vorwärts in Zk mit Oi-Zuki, Wendung mit Gedan-Barai in Zk',
        'aus Chudan-Kamae, vorwärts in Zk mit Jodan-Oi-Zuki/Gyaku-Zuki/rückwärts in Kk mit Shuto-Uke/vorwärts in Zk mit Ushiro-Geri/Gyaku-Zuki, Wendung mit Gedan-Barai in Kb'
      ]},
      { id:9, lines:[
        'aus Kb und Chudan-Kamae, vorwärts in Kb mit Yoko-Geri-Keage/Drehung und mit hinterem Bein Yoko-Geri-Kekomi in Kb',
        'Sonoba-Geri: (Standübung links und rechts) aus Zk und Chudan-Kamae: Mae-Geri nach vorne, mit gleichem Bein Yoko-Geri-Keage zur Seite, mit gleichem Bein Ushiro-Geri nach hinten, mit gleichem Bein Mawashi-Geri nach vorne, nach hinten absetzen in Chudan-Kamae'
      ]}
    ];
    const KATA2 = ['Bassai-Dai','Kanku-Dai','Jion','Enpi','Hangetsu'];
    const KATA3 = ['Heian Shodan','Heian Nidan','Heian Sandan','Heian Yondan','Heian Godan','Tekki Shodan','Tekki Nidan','Tekki Sandan'];
    const KATA4 = ['Bassai Sho','Kanku Sho','Nijushiho','Jitte','Chinte','Meikyo','Gangaku','Sochin'];

    // Helpers
    function shuffle(arr){ const a=arr.slice(); for(let i=a.length-1;i>0;i--){ const j=Math.floor(Math.random()*(i+1)); [a[i],a[j]]=[a[j],a[i]] } return a }
    function sample(arr, n){ return shuffle(arr).slice(0, n) }
    function pickOne(arr){ return arr[Math.floor(Math.random()*arr.length)] }
    function escapeHtml(str){ const d=document.createElement('div'); d.textContent = String(str); return d.innerHTML; }

    function renderKihon(){
      const list = document.getElementById('kihonList'); list.innerHTML='';
      const picks = sample(KIHON, 5);
      picks.forEach((k, idx)=>{
        const li = document.createElement('li'); li.className='item';
        li.innerHTML = `
          <div class="hdr"><div class="num">${k.id}</div><div class="ttl">Kombination ${idx+1}</div></div>
          <div class="steps">${k.lines.map(t=>`<div class="step">${escapeHtml(t)}</div>`).join('')}</div>
        `;
        list.appendChild(li);
      });
    }

    function renderKata(){
      const list = document.getElementById('kataList'); list.innerHTML='';
      const items = [
        { num:1, text:'Tokui Kata' },
        { num:2, text: pickOne(KATA2) },
        { num:3, text: pickOne(KATA3) },
        { num:4, text: pickOne(KATA4) },
      ];
      items.forEach(it=>{
        const li = document.createElement('li'); li.className='item';
        li.innerHTML = `
          <div class="hdr"><div class="num">${it.num}</div><div class="ttl">${escapeHtml(it.text)}</div></div>
        `;
        list.appendChild(li);
      });
    }

    function bindUI(){
      const btnKihon = document.getElementById('btnKihon');
      const btnKata = document.getElementById('btnKata');
      const regenKihon = document.getElementById('regenKihon');
      const regenKata = document.getElementById('regenKata');
      const back = document.getElementById('backBtn');

      const goKihon = ()=>{ showScreen('kihon'); renderKihon(); };
      const goKata = ()=>{ showScreen('kata'); renderKata(); };

      if (btnKihon){ btnKihon.addEventListener('click', goKihon); btnKihon.addEventListener('touchend', goKihon, {passive:true}); }
      if (btnKata){ btnKata.addEventListener('click', goKata); btnKata.addEventListener('touchend', goKata, {passive:true}); }
      if (regenKihon){ regenKihon.addEventListener('click', renderKihon); regenKihon.addEventListener('touchend', renderKihon, {passive:true}); }
      if (regenKata){ regenKata.addEventListener('click', renderKata); regenKata.addEventListener('touchend', renderKata, {passive:true}); }
      if (back){ back.addEventListener('click', ()=> showScreen('home')); back.addEventListener('touchend', ()=> showScreen('home'), {passive:true}); }
    }

    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', bindUI, { once: true });
    } else {
      bindUI();
    }

    // Register the service worker for PWA install/offline
    if ('serviceWorker' in navigator) {
      window.addEventListener('load', () => {
        navigator.serviceWorker.register('./sw.js').catch(()=>{});
      });
    }

    // Prevent rubber-band overscroll white flash inside PWA
    document.addEventListener('touchmove', function(e){
      if (typeof e.scale === 'number' && e.scale !== 1) e.preventDefault();
    }, { passive:false });
  </script>
</body>
</html>
"""
with open(os.path.join(base_dir, "index.html"), "w", encoding="utf-8") as f:
    f.write(index_html)

# Zip everything
zip_path = ".keiko-pwa.zip"
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
    for root, _, files in os.walk(base_dir):
        for name in files:
            full = os.path.join(root, name)
            z.write(full, arcname=os.path.relpath(full, base_dir))

zip_path