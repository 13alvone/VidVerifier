#	FactCheck Pipeline

A Dockerized pipeline that:
	•	Monitors a Gmail inbox for unseen emails containing YouTube, TikTok, or Instagram links
	•	Downloads videos in best MP4 quality using yt-dlp
	•	Transcribes audio with OpenAI Whisper if email subject contains "factcheck"
	•	Ensures deduplication, sender filtering, and robust file naming
	•	Intelligently supports YouTube playlists (default cap: 20)

##	🧱	Requirements

	•	Gmail address with App Password enabled
	•	YouTube, TikTok, or Instagram links sent from pre-approved senders
	•	Docker installed (for deployment)

##	🚀	Quick Start

###	1.	Create a `.env` file

Place in project root:

	GMAIL_ADDRESS=your_email@gmail.com
	GMAIL_APP_PASSWORD=your_app_password
	ALLOWED_SENDERS=friend@example.com,alerts@service.com
	MAX_PLAYLIST_VIDEOS=20

###	2.	Build and Run Docker

	docker build -t factcheck-pipeline .
	docker run -v "$(pwd)/app:/app/app" --env-file .env factcheck-pipeline

###	3.	Run Full Component Test (Optional)

	./test_all.sh

##	📂	Output

Videos and transcripts are saved in the `/app/app/` directory inside the container.
Each video is named after the cleaned email subject line, with incrementing suffixes if needed.
If the subject contains "factcheck", a `.txt` transcript is created with the same basename.

Example:

	Email Subject:	Breaking News 2025
	Files Created:
		Breaking_News_2025_1.mp4
		Breaking_News_2025_1.txt
		Breaking_News_2025_2.mp4
		Breaking_News_2025_2.txt

##	🔒	Security

	•	Only allowed senders are processed
	•	All URLs are validated via regex against known formats
	•	Subject and filenames are fully ASCII-cleaned
	•	Each URL/video is stored in SQLite and will never be reprocessed

##	⚙️	Configuration Options

Env Var				Description						Default
MAX_PLAYLIST_VIDEOS	Maximum videos to pull from a playlist		20
WHISPER_MODEL		Whisper model to use (base/medium/large)	base

##	🧪	Manual Component Testing

Run individual component tests:

	python3 app/test_pipeline.py --gmail
	python3 app/test_pipeline.py --regex
	python3 app/test_pipeline.py --download "https://youtu.be/dQw4w9WgXcQ"
	python3 app/test_pipeline.py --transcribe downloaded_file.mp4

##	📌	Tips

	•	Use Gmail's "App Passwords" (in Account > Security) — not your main password
	•	To download age-restricted/private videos, mount a cookies.txt and update yt-dlp call if needed
	•	Playlists are supported up to `MAX_PLAYLIST_VIDEOS`; each entry is deduped individually
	•	Random sleep between downloads (10–30s) avoids bot detection

##	✅	That's It!

FactCheck Pipeline will intelligently process video content from your inbox and turn it into verified audio+text packages, ready for downstream use.


