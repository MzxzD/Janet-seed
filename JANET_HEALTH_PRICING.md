# Janet Health - Pricing & Deployment Options

**You own `janet.health` - here's what it will cost to run it**

---

## 🆓 Option 1: Self-Hosted (FREE)

**Cost: $0/month**

### What You Need

- Your own hardware (Mac, Linux server, Raspberry Pi, etc.)
- Internet connection
- Cloudflare account (free)

### Setup

1. Run heartbeat server on your hardware
2. Use Cloudflare Tunnel (free) for public access
3. Host dashboard on Cloudflare Pages (free)

### Pros

- ✅ Completely free
- ✅ Full control
- ✅ No monthly bills
- ✅ Privacy (your hardware)

### Cons

- ❌ Requires always-on hardware
- ❌ Your internet/power reliability
- ❌ You manage updates

### Best For

- Personal use
- Small deployments (< 10 instances)
- Testing and development

---

## 💰 Option 2: VPS Hosting ($5-10/month)

**Cost: $5-10/month**

### Recommended Providers

#### DigitalOcean ($6/month)
- **Plan**: Basic Droplet
- **Specs**: 1 vCPU, 1 GB RAM, 25 GB SSD
- **Bandwidth**: 1 TB transfer
- **Link**: https://www.digitalocean.com/pricing/droplets

#### Linode ($5/month)
- **Plan**: Nanode 1GB
- **Specs**: 1 vCPU, 1 GB RAM, 25 GB SSD
- **Bandwidth**: 1 TB transfer
- **Link**: https://www.linode.com/pricing/

#### Vultr ($6/month)
- **Plan**: Regular Performance
- **Specs**: 1 vCPU, 1 GB RAM, 25 GB SSD
- **Bandwidth**: 1 TB transfer
- **Link**: https://www.vultr.com/pricing/

#### Hetzner ($4.50/month - Europe)
- **Plan**: CX11
- **Specs**: 1 vCPU, 2 GB RAM, 20 GB SSD
- **Bandwidth**: 20 TB transfer
- **Link**: https://www.hetzner.com/cloud

### What You Get

- ✅ 99.9% uptime SLA
- ✅ Professional infrastructure
- ✅ Automatic backups (usually extra $1-2/month)
- ✅ DDoS protection
- ✅ Global locations

### Setup

1. Create VPS account
2. Deploy Ubuntu 22.04 LTS
3. Install Janet Health (5 minutes)
4. Configure Cloudflare Tunnel (free)
5. Deploy dashboard on Cloudflare Pages (free)

### Pros

- ✅ Professional reliability
- ✅ Always online
- ✅ Fast global access
- ✅ Easy scaling

### Cons

- ❌ Monthly cost ($5-10)
- ❌ Requires basic Linux knowledge

### Best For

- Production deployments
- Multiple users
- Business use
- 10-1000+ instances

---

## 🚀 Option 3: Managed Hosting ($15-25/month)

**Cost: $15-25/month**

### Providers

#### Heroku ($7/month + $5/month)
- **Dyno**: Eco ($7/month)
- **Postgres**: Mini ($5/month) - for persistent storage
- **Total**: $12/month
- **Link**: https://www.heroku.com/pricing

#### Railway ($5-20/month)
- **Pay-as-you-go**: Based on usage
- **Typical**: $10-15/month
- **Link**: https://railway.app/pricing

#### Render ($7-25/month)
- **Starter**: $7/month
- **Standard**: $25/month
- **Link**: https://render.com/pricing

### What You Get

- ✅ Zero DevOps
- ✅ Automatic scaling
- ✅ Built-in monitoring
- ✅ Easy deployments (git push)
- ✅ Free SSL

### Pros

- ✅ Easiest setup
- ✅ No server management
- ✅ Automatic updates
- ✅ Built-in monitoring

### Cons

- ❌ Higher cost
- ❌ Less control
- ❌ Vendor lock-in

### Best For

- Non-technical users
- Quick deployment
- Focus on product, not infrastructure

---

## 🎯 Recommended Setup (What I'd Choose)

### For You: **Option 2 - VPS Hosting**

**Recommendation: Hetzner CX11 ($4.50/month)**

### Why?

1. **Cheapest reliable option** - $4.50/month
2. **Great specs** - 2 GB RAM (double others)
3. **Excellent bandwidth** - 20 TB (way more than needed)
4. **European data center** - Good for privacy
5. **Easy setup** - Ubuntu + our scripts = 10 minutes

### Total Monthly Cost Breakdown

| Item | Cost |
|------|------|
| Hetzner VPS | $4.50 |
| Cloudflare Tunnel | $0 (free) |
| Cloudflare Pages | $0 (free) |
| Domain (janet.health) | $0 (you own it) |
| **Total** | **$4.50/month** |

**That's $54/year** - less than a Netflix subscription!

---

## 📦 What's Included (All Options)

### Server Features

- ✅ WebSocket server (heartbeat_server.py)
- ✅ Real-time monitoring
- ✅ State persistence
- ✅ History tracking
- ✅ Auto-cleanup
- ✅ Dashboard broadcasting

### Client Library

- ✅ Easy integration (3 lines of code)
- ✅ Automatic reconnection
- ✅ Metrics collection
- ✅ Privacy-focused

### Dashboard

- ✅ Beautiful real-time UI
- ✅ Responsive design
- ✅ Status monitoring
- ✅ Metrics display
- ✅ History view

### Documentation

- ✅ Complete setup guide
- ✅ User documentation
- ✅ Quick reference
- ✅ Troubleshooting guide

### Support

- ✅ Test suite
- ✅ Quick start scripts
- ✅ Example integrations

---

## 🚀 Quick Setup (Hetzner VPS)

### 1. Create Account

1. Go to https://www.hetzner.com/cloud
2. Create account
3. Add payment method

### 2. Create Server

1. Click "New Project"
2. Click "Add Server"
3. Select:
   - **Location**: Nuremberg (or nearest)
   - **Image**: Ubuntu 22.04
   - **Type**: CX11 (2 GB RAM)
   - **Networking**: IPv4 + IPv6
4. Click "Create & Buy Now"

**Cost: $4.50/month**

### 3. Deploy Janet Health

SSH into your server:

```bash
ssh root@YOUR_SERVER_IP
```

Install Janet Health:

```bash
# Update system
apt update && apt upgrade -y

# Install Python and dependencies
apt install -y python3 python3-pip python3-venv git

# Clone your Janet seed repo (or upload files)
git clone https://github.com/YOUR_USERNAME/Janet-seed.git
cd Janet-seed

# Create venv and install dependencies
python3 -m venv venv
./venv/bin/pip install websockets psutil

# Start server
./start_janet_health.sh --background
```

### 4. Configure Cloudflare Tunnel

On your local machine:

```bash
# Install cloudflared
brew install cloudflare/cloudflare/cloudflared

# Login
cloudflared tunnel login

# Create tunnel
cloudflared tunnel create janet-health

# Note the tunnel ID
```

Create `~/.cloudflared/config.yml`:

```yaml
tunnel: YOUR_TUNNEL_ID
credentials-file: ~/.cloudflared/YOUR_TUNNEL_ID.json

ingress:
  - hostname: janet.health
    service: ws://YOUR_SERVER_IP:8766
  - service: http_status:404
```

Route DNS:

```bash
cloudflared tunnel route dns janet-health janet.health
```

Start tunnel:

```bash
cloudflared tunnel run janet-health
```

### 5. Deploy Dashboard

1. Push `dashboard/` to GitHub
2. Go to Cloudflare Pages
3. Connect repository
4. Deploy
5. Add custom domain: `janet.health`

**Done!** Visit https://janet.health

---

## 💳 Payment Methods

All providers accept:

- ✅ Credit/Debit cards
- ✅ PayPal
- ✅ Bank transfer (some)
- ✅ Cryptocurrency (some)

---

## 📊 Cost Comparison

| Option | Monthly | Yearly | Setup Time | Difficulty |
|--------|---------|--------|------------|------------|
| **Self-Hosted** | $0 | $0 | 10 min | Easy |
| **Hetzner VPS** | $4.50 | $54 | 15 min | Easy |
| **DigitalOcean** | $6 | $72 | 15 min | Easy |
| **Linode** | $5 | $60 | 15 min | Easy |
| **Heroku** | $12 | $144 | 5 min | Very Easy |
| **Railway** | $10-15 | $120-180 | 5 min | Very Easy |

---

## 🎁 Free Credits

### DigitalOcean

- **New users**: $200 credit (60 days)
- **Link**: Use referral link for bonus credit

### Linode

- **New users**: $100 credit (60 days)
- **Link**: https://www.linode.com/lp/free-credit/

### Vultr

- **New users**: $100 credit (30 days)
- **Link**: https://www.vultr.com/promo/try100/

**Try for free first!** Use free credits to test before committing.

---

## 🔒 Additional Costs (Optional)

### Backups

- **Hetzner**: $0.90/month (20% of server cost)
- **DigitalOcean**: $1.20/month
- **Linode**: $1/month

### Monitoring

- **Cloudflare**: Free
- **UptimeRobot**: Free (50 monitors)
- **Grafana Cloud**: Free tier

### SSL Certificate

- **Cloudflare**: Free ✅
- **Let's Encrypt**: Free ✅

---

## 💰 My Recommendation

**Start with Hetzner CX11 ($4.50/month)**

### Why?

1. **Cheapest** - Only $4.50/month
2. **Best value** - 2 GB RAM vs 1 GB elsewhere
3. **Reliable** - German infrastructure
4. **Easy** - Ubuntu + our scripts
5. **Scalable** - Upgrade anytime

### Total Investment

- **Setup**: 15 minutes
- **Monthly**: $4.50
- **Yearly**: $54

**Less than $1.50 per week** for professional global monitoring!

---

## 📞 Need Help?

### Free Support Included

- ✅ Complete documentation
- ✅ Setup guides
- ✅ Test suite
- ✅ Troubleshooting guide

### Paid Support (Optional)

If you want hands-on help:

- **Setup service**: $50-100 one-time
- **Managed service**: $25-50/month

*(Not offered by me, but typical market rates)*

---

## ✅ Next Steps

### 1. Choose Your Option

- [ ] Self-hosted (free)
- [ ] VPS hosting ($5-10/month) ← **Recommended**
- [ ] Managed hosting ($15-25/month)

### 2. Get Started

- [ ] Create VPS account (if VPS)
- [ ] Follow [JANET_HEALTH_SETUP.md](JANET_HEALTH_SETUP.md)
- [ ] Deploy in 15 minutes

### 3. Enjoy!

- [ ] Monitor your Janet instances
- [ ] Share dashboard with team
- [ ] Scale as needed

---

## 🎉 Summary

**You can run Janet Health at `janet.health` for just $4.50/month!**

That includes:
- ✅ Professional VPS hosting
- ✅ Global monitoring
- ✅ Beautiful dashboard
- ✅ Unlimited Janet instances
- ✅ Real-time updates
- ✅ Complete documentation

**Ready to deploy?** Follow [JANET_HEALTH_SETUP.md](JANET_HEALTH_SETUP.md)

---

**Questions?** See [JANET_HEALTH_README.md](JANET_HEALTH_README.md) 💚
