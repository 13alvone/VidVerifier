# Vid Verifier

	_____    _       _         _____ _ _ _             
	|  ___|__| |_ ___| |__     |  ___(_) | |_ ___ _ __  
	| |_ / _ \ __/ __| '_ \    | |_  | | | __/ _ \ '__| 
	|  _|  __/ || (__| | | |_  |  _| | | | ||  __/ |_   
	|_|  \___|\__\___|_| |_( ) |_|   |_|_|\__\___|_( )  
	 _____          _      |/ ____ _               |/   
	|  ___|_ _  ___| |_      / ___| |__   ___  ___| | __
	| |_ / _` |/ __| __|____| |   | '_ \ / _ \/ __| |/ /
	|  _| (_| | (__| ||_____| |___| | | |  __/ (__|   < 
	|_|  \__,_|\___|\__|     \____|_| |_|\___|\___|_|\_\


## What is Vid Verifier?  
*An inbox robot for videos.*   
It watches your Gmail, finds **YouTube / TikTok / Instagram** links, downloads the videos in the best quality and—when the subject line contains **factcheck**—creates Whisper transcripts. Everything runs in one Docker image—no Python installs, no system dependencies.

---

## 🚀 5‑Minute Install (Really)

> **TL;DR** Copy‑paste each block; edit **one** file; done.

### 1 ▪ Grab the code
	cd ~
	git clone https://github.com/yourname/VidVerifier.git
	cd VidVerifier

### 2 ▪ Create a Google *App Password*
	# 1) Enable 2‑Step Verification → https://myaccount.google.com/security
	# 2) Open  https://myaccount.google.com/apppasswords
	#    Select app → Other → VidVerifier → Generate
	# 3) Copy the 16‑digit string

### 3 ▪ Fill in `.env`
	cp .env.example .env
	nano .env    # or any editor
	# ───────────────────────────────────
	GMAIL_ADDRESS       = you@gmail.com
	GMAIL_APP_PASSWORD  = 16‑digit‑string‑here
	ALLOWED_SENDERS     = you@gmail.com, alerts@example.com
	MAX_PLAYLIST_VIDEOS = 20
	WHISPER_MODEL       = base
	LOG_LEVEL           = INFO
	# ───────────────────────────────────

### 4 ▪ Build and run
	docker build -t vidverifier .
	docker run -d --name vidverifier --restart unless-stopped \
	  -v "$(pwd)/output":/downloads \
	  --env-file .env \
	  -e GMAIL_SEARCH=ALL \
	  vidverifier

	Logs  →  docker logs -f vidverifier  
	Stop  →  docker stop vidverifier

---

## 🎯 Why you’ll like it

* Gmail **App Password**—no OAuth fuss  
* Handles every common YT / IG / TikTok link style  
* Random delays + desktop **User‑Agent** ⇒ stealthier  
* 3 auto‑retries with exponential back‑off  
* ASCII‑safe filenames, playlist support, SHA‑256 deduplication  
* On‑demand Whisper transcription  
* One self‑contained image (FFmpeg + yt‑dlp + Whisper)

---

## 🧠 How it works (internally)

	graph TD
	  A(Gmail IMAP) -->|unseen mails| B{Allowed sender?}
	  B -->|no| Z[Skip]
	  B -->|yes| C[Extract links]
	  C --> D[Download MP4(s)]
	  D --> E{subject contains “factcheck”?}
	  E -->|yes| F[Whisper transcribe → TXT]
	  E -->|no| G[Done]
	  F --> G
	  G --> H[Log to SQLite & keep file]

---

## 📂 What lands in **output/**  
	Federal_Hearing_Evidence_bb92f1c3.mp4
	Federal_Hearing_Evidence_bb92f1c3.txt  # when transcribed

---

## 💡 Handy commands
| Task | Command |
| --- | --- |
| Test suite |	./test_all.sh |
| Follow logs |	docker logs -f vidverifier |
| Update image |	git pull && docker build -t vidverifier . |
| Prune images |	docker image prune -f |

---

## 🔐 Security
* Only allow‑listed senders are processed.  
* Filenames fully sanitised.  
* Whisper runs **locally**—no cloud calls.

---

## Need help?  
Open an issue—bug reports, ideas and PRs are welcome!
