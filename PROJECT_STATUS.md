# AI Career Copilot — Project Status

## TARGET

MVP siap dipakai untuk mencari dan melamar pekerjaan remote.

## PHASE

1. Deployment
2. Deadline protection
3. Final end-to-end test
4. Remote application #1

## DONE

- AI matching
- Geo eligibility
- Opportunity scoring
- Job sources
- FastAPI local
- React frontend
- Apply Package
- Application Tracker
- n8n
- Telegram
- Supabase dedup

## CURRENT PHASE

2. Deadline protection

## CURRENT PROBLEM

Production FastAPI gagal start karena deployment memanggil FastAPI CLI dan menghasilkan:

RuntimeError: To use the fastapi command, please install "fastapi[standard]"

Repository seharusnya menjalankan aplikasi menggunakan Uvicorn.

## NEXT ACTION

Perbaiki deployment FastAPI Cloud agar menjalankan aplikasi dengan:

uvicorn backend.main:app --host 0.0.0.0 --port $PORT

## DO NOT TOUCH

- n8n
- Telegram
- Supabase
- frontend
- komponen yang sudah selesai

## LAST VERIFIED

2026-08-21

- FastAPI Cloud production deployment berhasil.
- Production URL: https://ai-job-matcher-agent.fastapicloud.dev
- Production /docs tersedia.
- Uvicorn berhasil start di production.
- Commit deployment: 0ffee1e

## WORKING RULES

1. Selesaikan satu phase sebelum pindah ke phase berikutnya.
2. Satu perubahan utama lalu test.
3. Setelah phase berhasil, update file ini dan buat Git commit.
4. Jangan mengulang pekerjaan yang sudah DONE.
5. Jangan menambah fitur baru sebelum empat phase utama selesai.
6. Jika pindah chat, lanjutkan dari CURRENT PHASE di file ini.
7. Jangan menebak konfigurasi atau error; periksa bukti/error terlebih dahulu.

## NEXT CHAT

Lanjut dari CURRENT PHASE, bukan mulai ulang.