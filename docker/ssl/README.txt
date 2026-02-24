Place your SSL certificates here:

  fullchain.pem  — Full certificate chain (from Let's Encrypt or your CA)
  privkey.pem    — Private key

For Let's Encrypt (free), run on your EC2 instance:

  sudo certbot certonly --standalone -d your-domain.com
  sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ./
  sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ./

deploy.sh auto-generates a self-signed cert here for testing.

⚠️  NEVER commit .pem files to git — they are in .dockerignore and .gitignore
