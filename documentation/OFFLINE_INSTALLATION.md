# 📴 Offline Installation Guide — J.A.N.E.T. Seed

J.A.N.E.T. Seed is designed to work **offline-first**. This guide explains how to install models and dependencies when you don't have internet access.

> **New to J.A.N.E.T. Seed?** Start with the [User Guide](USER_GUIDE.md) for basic usage.

---

## 🌱 Philosophy

Janet never auto-downloads. She provides clear instructions for manual installation, whether you're online or offline.

---

## 🔧 Installing Ollama Models Offline

### Step 1: Download on a Connected Device

On a device with internet access, run:

```bash
ollama pull <model-name>
```

For example:
```bash
ollama pull tinyllama:1.1b
ollama pull deepseek-coder:6.7b
```

This downloads the model files to your Ollama models directory.

### Step 2: Find the Model Files

The model files are located at:

- **macOS/Linux**: `~/.ollama/models/`
- **Windows**: `C:\Users\YourName\.ollama\models\`

Look for directories or files related to your model name (e.g., `tinyllama`, `deepseek-coder`).

### Step 3: Transfer Files to Offline Device

Copy the model files to your offline device using one of these methods:

- **USB drive**: Copy files to USB, then copy to target location
- **Network share**: If devices are on same network, use file sharing
- **Local network**: Use `scp`, `rsync`, or file sharing protocol
- **External drive**: Copy via external storage device

### Step 4: Place Files in Correct Location

On your **offline device**, place the files at the same location:

- **macOS/Linux**: `~/.ollama/models/`
- **Windows**: `C:\Users\YourName\.ollama\models\`

Make sure the directory structure matches what Ollama expects.

### Step 5: Verify Installation

When ready, verify the installation:

```bash
ollama list
```

This should show your model in the list.

You can also ask Janet to verify:
```
what can you do?
```

Then use the expansion protocol to verify model installation.

---

## 🐍 Installing Python Dependencies Offline

### Method 1: Download Wheels on Connected Device

1. On a connected device, download the required packages:

```bash
pip download -r requirements.txt -d ./offline_packages
```

2. Transfer the `offline_packages` directory to your offline device.

3. On the offline device, install from local packages:

```bash
pip install --no-index --find-links ./offline_packages -r requirements.txt
```

### Method 2: Use pip with Local Index

1. Create a local package index on a connected device.
2. Transfer the index to your offline device.
3. Install using the local index.

---

## 🔍 Troubleshooting

### Model Doesn't Appear

- Check file permissions and directory structure
- Ensure files are in the correct location
- Verify Ollama can access the models directory

### Ollama Can't Find Model

- Ensure files are in the correct location
- Check directory structure matches expected format
- Try running `ollama list` to see what Ollama detects

### Verification Fails

- Run `ollama list` manually to check
- Verify file permissions
- Check that model files are complete (not corrupted during transfer)

---

## 💡 Tips

- **Test on connected device first**: Verify the model works before transferring
- **Keep backups**: Store model files in a safe location
- **Document your setup**: Note which models you've installed and where
- **Use expansion protocol**: Janet can guide you through offline installation interactively

---

## 🌱 Next Steps

After installing models offline, you can:

1. Ask Janet: `what can you do?` to see available expansions
2. Use the expansion protocol to enable new capabilities
3. Verify installations through Janet's expansion wizards

---

**Remember**: Janet never auto-downloads. All installations require your explicit consent and action.

