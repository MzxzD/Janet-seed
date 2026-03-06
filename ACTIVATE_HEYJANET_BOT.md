# Activate heyjanet.bot - Final Step

## Current Status ✅

Everything is configured correctly:

- ✅ **WebSocket server**: Running on port 8765
- ✅ **Cloudflare tunnel**: Connected and active
- ✅ **Cloudflare DNS record**: CNAME correctly pointing to tunnel
  - `heyjanet.bot.xn--yckwaps3i.com` → `69067bfd-f27c-4a86-a5f9-8c2bc839e952.cfargotunnel.com`
- ✅ **Proxy**: Enabled (orange cloud)

## The ONE Missing Step 🎯

The Cloudflare zone for `ジャネット.com` (xn--yckwaps3i.com) is in **"initializing"** status because the nameservers haven't been updated at Namecheap yet.

### What You Need to Do (5 minutes):

1. **Go to Namecheap**: https://ap.www.namecheap.com/domains/list/

2. **Find your domain**: `ジャネット.com` (or search for "xn--yckwaps3i.com")

3. **Click "Manage"**

4. **Go to "Nameservers" section**

5. **Change from "Namecheap BasicDNS" to "Custom DNS"**

6. **Enter Cloudflare nameservers**:
   ```
   frida.ns.cloudflare.com
   henry.ns.cloudflare.com
   ```

7. **Save changes**

8. **Wait 5-30 minutes** for DNS propagation

## Verification

After changing nameservers, wait a few minutes then run:

```bash
cd /Users/mzxzd/Documents/JanetOS/janet-seed
./verify-heyjanet-bot.sh
```

Or manually check:

```bash
# Check if nameservers updated
dig NS xn--yckwaps3i.com +short

# Should show:
# frida.ns.cloudflare.com
# henry.ns.cloudflare.com

# Test connectivity
curl -I https://heyjanet.bot
```

## Why This Is Needed

- **Current nameservers**: `dns1.registrar-servers.com`, `dns2.registrar-servers.com` (Namecheap)
- **Required nameservers**: `frida.ns.cloudflare.com`, `henry.ns.cloudflare.com` (Cloudflare)

Until the nameservers are changed, the world's DNS servers will ask Namecheap for `heyjanet.bot`, and Namecheap will return the old AWS IPs (34.216.117.25, 54.149.79.189).

Once nameservers are changed, DNS queries will go to Cloudflare, which has the correct CNAME record pointing to your tunnel!

## After Activation

Once the nameservers are updated and propagated:

- ✅ `wss://heyjanet.bot` will work from anywhere
- ✅ iOS/Watch apps will connect
- ✅ SSL/TLS automatically handled by Cloudflare
- ✅ DDoS protection included
- ✅ Global CDN for fast access

---

**TL;DR**: Go to Namecheap → Change nameservers to Cloudflare's → Wait 5-30 minutes → Done! 🚀
