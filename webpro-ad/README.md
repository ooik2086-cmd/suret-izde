# webpro.kz жарнама роликтері

- `poster.png`, `logo.png` — бренд суреттері (референс).
- `out/webpro_qr_menu.mp4` — QR-мәзір жарнамасы (постер стилі, 31 с).
- `out/webpro_qr_vs_paper.mp4` + `out/caption.txt` — «Қағаз мәзір vs QR-мәзір» (3D, 33 с), ботқа жіберілген 2026-11-06.
- `src/qr-vs-paper-3d/` — three.js сахнасы `scene.html`, рендер `render3.py` (кадрма-кадр, Playwright; `npm i three@0.169.0`, poster.png/logo.png/bg.jpg қасында болуы керек), дауыс `voice.mp3` (ElevenLabs, «жігіт» EH6axdGJCki2MKcoMcaI, eleven_v3), сегмент уақыттары `times.json`.
- `src/qr-menu-poster/ad.html` — постер стиліндегі 2D анимация.
Дыбыс: webpro-reels `episode/audio/` (theme.mp3, whoosh, phone_ping, idea_ding, cafe_amb).
