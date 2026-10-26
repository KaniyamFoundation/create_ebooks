# TODO: Configure Custom Domain `catalog.freetamilebooks.com`

This checklist details the steps to point `catalog.freetamilebooks.com` to the GitHub Pages OPDS catalog.

Currently, the catalog is live at:
👉 **https://kaniyamfoundation.github.io/FTE_opds_catalog/**

---

## 1. Cloudflare DNS Setup

Log in to the **Cloudflare Dashboard** managing DNS for `freetamilebooks.com`:

1. Select **`freetamilebooks.com`** &rarr; **DNS** &rarr; **Records**.
2. Click **Add record**:
   - **Type**: `CNAME`
   - **Name**: `catalog`
   - **Target**: `kaniyamfoundation.github.io`
   - **Proxy status**: **DNS only** (Grey cloud)  
     *(Important: Keep as DNS-only until Let's Encrypt SSL certificate is provisioned by GitHub)*
   - **TTL**: `Auto`
3. Click **Save**.

---

## 2. Enable Custom Domain in GitHub Pages

Once DNS has been saved:

### Option A: Via GitHub Web Interface
1. Go to repository settings: https://github.com/KaniyamFoundation/FTE_opds_catalog/settings/pages
2. Under **Custom domain**, enter: `catalog.freetamilebooks.com`
3. Click **Save**.
4. GitHub will verify the DNS record and automatically provision a TLS/SSL certificate (usually 2–5 minutes).
5. Check the box **Enforce HTTPS**.

### Option B: Via Terminal / Git
```bash
cd /home/shrini/dev/fte/FTE_opds_catalog
echo "catalog.freetamilebooks.com" > CNAME
git add CNAME
git commit -m "Enable custom domain catalog.freetamilebooks.com"
git push origin main
```

---

## 3. Verify Live Catalog

Test both in browser and in OPDS reader apps:
- **Landing Page**: https://catalog.freetamilebooks.com/
- **Categories Root Feed**: https://catalog.freetamilebooks.com/index.xml
- **All Books Feed**: https://catalog.freetamilebooks.com/books.opds.xml
- **JSON Metadata**: https://catalog.freetamilebooks.com/books.json

---

## 4. (Optional) Turn on Cloudflare Proxy

Once GitHub HTTPS is confirmed working:
- You may switch the Cloudflare DNS record proxy status from **DNS only** (Grey cloud) to **Proxied** (Orange cloud).
- Ensure Cloudflare SSL/TLS encryption mode is set to **Full** or **Full (strict)**.
