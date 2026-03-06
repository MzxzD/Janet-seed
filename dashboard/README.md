# Janet Health Dashboard

Beautiful real-time monitoring dashboard for Janet seed instances.

## Quick Start

### Local Development

```bash
cd dashboard

# Simple HTTP server
python3 -m http.server 8767

# Or with Node.js
npx http-server -p 8767
```

Visit: `http://localhost:8767`

### Deploy to Cloudflare Pages

1. Create a GitHub repository with the `dashboard/` contents
2. Go to [Cloudflare Pages](https://pages.cloudflare.com)
3. Click "Create a project"
4. Connect your GitHub repository
5. Configure build:
   - Build command: (leave empty)
   - Build output directory: `/`
6. Click "Save and Deploy"

Your dashboard will be live at `https://your-project.pages.dev`

### Custom Domain

1. In Cloudflare Pages, go to your project
2. Click "Custom domains"
3. Add `janet.health`
4. Cloudflare will automatically configure DNS

## Files

- `index.html` - Main dashboard page (single file, no build needed)

## Configuration

Edit `index.html` to change WebSocket URL:

```javascript
// For production
const wsUrl = 'wss://janet.health';

// For local testing
const wsUrl = 'ws://localhost:8766';

// Auto-detect (current setup)
const wsUrl = window.location.protocol === 'https:' 
    ? 'wss://janet.health'
    : 'ws://localhost:8766';
```

## Features

- Real-time updates via WebSocket
- Responsive design (mobile-friendly)
- Auto-reconnect on disconnect
- Beautiful gradient UI
- Status badges and indicators
- Capability tags
- Last seen timestamps

## Browser Support

- Chrome/Edge: ✅
- Firefox: ✅
- Safari: ✅
- Mobile browsers: ✅

## Customization

### Colors

Edit CSS variables in `index.html`:

```css
:root {
    --primary-color: #667eea;
    --secondary-color: #764ba2;
    --success-color: #10b981;
    --error-color: #ef4444;
}
```

### Branding

Change header text:

```html
<h1>💚 Your Custom Title</h1>
<p class="subtitle">Your custom subtitle</p>
```

## Performance

- Single HTML file (~15 KB)
- No external dependencies
- Fast load time (<100ms)
- Efficient WebSocket updates

## License

MIT License - Part of Janet Seed project
