# Deploy on Vultr (about 15 minutes)

You do NOT need a huge server. 2 vCPU / 4 GB RAM is plenty and costs a few dollars of your $200 credit.

1. Log in at https://my.vultr.com and apply your gift code credits (Billing).
2. **Deploy +** > **Cloud Compute** (Shared CPU) > location near you > image **Ubuntu 24.04** >
   plan **2 vCPU / 4 GB** > add your SSH key (or use the root password shown) > **Deploy Now**.
3. Wait until the server is Running and copy its **IP address**.
4. Connect: `ssh root@YOUR_SERVER_IP`
5. Install Docker:
   ```bash
   apt-get update && curl -fsSL https://get.docker.com | sh
   ```
6. Get the code and configure:
   ```bash
   git clone https://github.com/astrax-gif/review_dojo.git && cd review_dojo
   cp .env.example .env && nano .env     # set POSTGRES_PASSWORD and SECRET_KEY (optional ANTHROPIC_API_KEY)
   ```
7. Start everything:
   ```bash
   docker compose up -d --build
   docker compose ps
   ```
8. Open `http://YOUR_SERVER_IP` in a browser. Check `http://YOUR_SERVER_IP/api/health` shows `{"status":"ok"}`.
9. Update later: `git pull && docker compose up -d --build`
