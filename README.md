#	Presenting
 _   ___    ___   __        _ ____        
| | / (_)__/ / | / /__ ____(_) _(_)__ ____
| |/ / / _  /| |/ / -_) __/ / _/ / -_) __/
|___/_/\_,_/ |___/\__/_/ /_/_//_/\__/_/   

	VidVerifier: Fetch, Filter, Fact-Check.


VidVerifier is a modern, Dockerized pipeline that monitors your Gmail inbox for video links from YouTube, TikTok, or Instagram, downloads them in the best possible quality, and transcribes them using Whisper AI if flagged for fact-checking. With robust support for playlist URLs, intelligent retries, deduplication, and URL variation coverage, VidVerifier ensures seamless and automated media analysis directly from your inbox.

##	🎯 Key Features

	•	Connects securely to Gmail via App Passwords (no OAuth needed)
	•	Detects all known YouTube, Instagram, and TikTok link formats
	•	Only processes messages from allowlisted senders
	•	Downloads videos as MP4 using best quality available
	•	Supports YouTube playlists with a configurable video limit
	•	Performs randomized delays + realistic User-Agent for stealth
	•	Retries failed downloads up to 2 additional times with backoff
	•	Transcribes videos with Whisper AI if subject contains “factcheck”
	•	Filenames are ASCII-cleaned from email subject line (+ suffixes if needed)
	•	SQLite-based deduplication to prevent reprocessing URLs
	•	Fully Dockerized with CLI test support and clear logging

##	🧠 How It Works

When a new email is received from a trusted sender, VidVerifier:
	1. Extracts all YouTube, TikTok, and Instagram video links
	2. Cleans subject line → safe filename
	3. Downloads each video (with retry + fallback logic)
	4. If "factcheck" is in subject → transcribes each MP4 to TXT
	5. Saves all files locally + logs metadata in `downloaded_links.db`

##	📂 Example Output

Subject:	Federal Hearing Evidence
Saved Files:
	Federal_Hearing_Evidence_1.mp4
	Federal_Hearing_Evidence_1.txt
	Federal_Hearing_Evidence_2.mp4
	Federal_Hearing_Evidence_2.txt

##	⚙️ Setup

###	1. Clone the Repo

	git clone https://github.com/yourname/VidVerifier.git
	cd VidVerifier

###	2. Create Config File

	cp .env.example .env
	nano .env

Required fields:
	GMAIL_ADDRESS=your_email@gmail.com
	GMAIL_APP_PASSWORD=your_generated_app_password
	ALLOWED_SENDERS=trusted1@domain.com,alerts@source.com
	MAX_PLAYLIST_VIDEOS=20
        WHISPER_MODEL=base
        LOG_LEVEL=INFO

##	🐳 Docker Usage

###	Build the Container

	docker build -t vidverifier .

###	Run It

	docker run --rm -v "$(pwd)/app:/app/app" --env-file .env vidverifier

###	Run Tests (Locally)

	./test_all.sh

##	🧪 Manual Tests

Run individual test components:

	python3 app/test_pipeline.py --gmail
	python3 app/test_pipeline.py --regex
	python3 app/test_pipeline.py --download https://youtu.be/dQw4w9WgXcQ
	python3 app/test_pipeline.py --transcribe ./test_subject_1.mp4

##	📦 Directory Layout

	app/
		downloader.py			# Download engine with retry + backoff
		gmail_watcher.py		# Gmail IMAP connector and URL extractor
		transcriber.py			# Whisper-based transcription logic
		utils.py				# Regex, delay, sanitizer, dedup DB
		main.py					# Orchestration
		test_pipeline.py		# CLI test harness
		downloaded_links.db		# SQLite DB for deduplication

##	🔐 Security Notes

	•	Only processes URLs from allowlisted senders
	•	All subject lines and URLs are ASCII-cleaned
	•	No OAuth/OIDC flows — app password is recommended
	•	Whisper model is run locally — no outbound API calls

##	📌 Tips

	•	Run as a cron job to check your inbox every 15 mins
	•	Configure playlists max count with `MAX_PLAYLIST_VIDEOS`
	•	Add your own cookie.txt to support private/age-restricted videos
	•	Use `WHISPER_MODEL=medium` for more accurate transcripts (if supported)

##	🧼 Maintenance

Clean up old Docker images:

	docker image prune -f


