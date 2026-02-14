# 🐷 HogglePrime Complete Setup Guide
## From Zero to Hoggle (Fresh Windows Install)

**Time Required:** ~75-90 minutes  
**Difficulty:** Beginner-friendly (GUI-focused)  
**Last Updated:** February 2026

---

# PHASE A: Install Foundation Software

---

## Step 1: Install Ollama (5 minutes)

Ollama runs the AI brain locally on your computer.

1. Open your browser
2. Go to: **https://ollama.com/download**
3. Click **"Download for Windows"**
4. Run the installer (`OllamaSetup.exe`)
5. Click through the installer (all defaults are fine)
6. When done, look for Ollama's **llama icon** in your system tray (bottom right of screen, near the clock)

### Verify Ollama Works:
1. Press `Win + R` on your keyboard
2. Type `cmd` and press Enter
3. In the black window, type:
```
ollama --version
```
4. You should see something like: `ollama version 0.15.4`

✅ **Checkpoint:** Ollama icon in system tray + version shows in cmd

---

## Step 2: Install Docker Desktop (15 minutes, includes restart)

Docker runs our services (Open WebUI, n8n) in containers.

1. Go to: **https://www.docker.com/products/docker-desktop/**
2. Click **"Download for Windows"**
3. Run the installer (`Docker Desktop Installer.exe`)
4. **Important:** When asked, make sure **"Use WSL 2 instead of Hyper-V"** is checked
5. Click through the rest of the installer
6. **Restart your computer when prompted**

### After Restart:
1. Docker Desktop should auto-launch (if not, search for it in Start menu)
2. You might see a message about WSL 2 kernel update - click **"Update"** if prompted
3. Wait for Docker to finish starting
4. Look for the **whale icon** in your system tray
5. Hover over it - should say **"Docker Desktop is running"**

⚠️ **If Docker won't start:** You may need to enable virtualization in your BIOS. Ask your IT person if you see errors about virtualization.

✅ **Checkpoint:** Docker whale icon in system tray shows "running"

---

## Step 3: Install GitHub Desktop (5 minutes)

GitHub Desktop syncs your project between home and school.

1. Go to: **https://desktop.github.com/**
2. Click **"Download for Windows (64bit)"**
3. Run the installer
4. When it opens, click **"Sign in to GitHub.com"**
5. Sign in with your GitHub account
6. Complete the setup (name/email for commits)

✅ **Checkpoint:** GitHub Desktop is open and signed in

---

## Step 4: Install Python (5 minutes)

Python runs our voice scripts and utilities.

1. Go to: **https://www.python.org/downloads/**
2. Click the big yellow **"Download Python 3.x.x"** button
3. Run the installer

4. **⚠️ CRITICAL:** On the first installer screen, CHECK THE BOX that says:
   **"Add python.exe to PATH"** (at the bottom!)

5. Click **"Install Now"**
6. Wait for installation to complete
7. Click "Close"

### Verify Python Works:
1. Open **cmd** (Win + R, type `cmd`, Enter)
2. Type:
```
python --version
```
3. Should show: `Python 3.12.x` or similar

4. Also verify pip:
```
pip --version
```

✅ **Checkpoint:** Both `python --version` and `pip --version` work

---

## Step 5: Download the Qwen Model (10-15 minutes)

This downloads Hoggle's 9GB brain.

1. Open **cmd**
2. Type:
```
ollama pull qwen2.5:14b-instruct
```
3. Wait for the download (shows a progress bar)
4. This takes 10-15 minutes depending on your internet

### Verify Model Downloaded:
```
ollama list
```

You should see:
```
NAME                        SIZE
qwen2.5:14b-instruct       9.0 GB
```

✅ **Checkpoint:** `qwen2.5:14b-instruct` appears in ollama list

---

## Step 6: Launch Open WebUI (5 minutes)

Open WebUI gives you a ChatGPT-like interface for Hoggle.

1. Make sure Docker Desktop is running (whale icon in system tray)
2. Open **cmd**
3. Copy and paste this ENTIRE command (it's one long line):

```
docker run -d -p 3000:8080 --add-host=host.docker.internal:host-gateway -v open-webui:/app/backend/data --name open-webui --restart always ghcr.io/open-webui/open-webui:main
```

4. Press Enter
5. Wait for it to download the image (first time takes 2-3 minutes)
6. When you see a long string of letters/numbers, it's done

### Access Open WebUI:
1. Open your browser
2. Go to: **http://localhost:3000**
3. Click **"Sign up"** to create your admin account
4. Use any email/password (this is local, just for you)
5. You're now in Open WebUI!

### Verify Ollama Connection:
1. Click your **profile icon** (bottom left corner)
2. Click **"Admin Panel"**
3. Click **"Settings"**
4. Click **"Connections"**
5. Under "Ollama API", you should see a **green checkmark** ✓

**If you see a red X instead:**
1. Click the pencil/edit icon
2. Change the URL to: `http://host.docker.internal:11434`
3. Click the refresh/check button
4. Should turn green now

✅ **Checkpoint:** Open WebUI loads at localhost:3000, Ollama shows connected (green)

---

## Step 7: Launch n8n (5 minutes)

n8n is the automation engine that connects everything together.

1. Open **cmd**
2. Copy and paste this command:

```
docker run -d --name n8n -p 5678:5678 -v n8n_data:/home/node/.n8n --restart always n8nio/n8n
```

3. Press Enter
4. Wait for download (1-2 minutes first time)

### Access n8n:
1. Open browser
2. Go to: **http://localhost:5678**
3. Create your admin account (local, just for you)
4. You'll see the n8n workflow editor

✅ **Checkpoint:** n8n loads at localhost:5678

---

## Step 8: Verify All Services Running

Open **cmd** and type:
```
docker ps
```

You should see TWO containers running:
```
NAMES        STATUS         PORTS
open-webui   Up X minutes   0.0.0.0:3000->8080/tcp
n8n          Up X minutes   0.0.0.0:5678->5678/tcp
```

**Or check visually:**
1. Open **Docker Desktop**
2. Click **"Containers"** tab on the left
3. You should see `open-webui` and `n8n` both with green "Running" status

✅ **Checkpoint:** Both containers running in Docker

---

# PHASE B: Set Up HogglePrime Project Files

---

## Step 9: Create the HogglePrime Folder

1. Press `Win + E` to open **File Explorer**
2. Click **"Documents"** in the left sidebar
3. Right-click in the empty space
4. Click **New** → **Folder**
5. Name it exactly: `HogglePrime`
6. Double-click to open it

### Find Your Path:
1. Click in the **address bar** at the top of File Explorer
2. It will change from "Documents > HogglePrime" to show the real path like:
```
C:\Users\YourUsername\Documents\HogglePrime
```
3. **Write this down or copy it** - you'll need it for the .env file!

✅ **Checkpoint:** Empty HogglePrime folder exists, you know the full path

---

## Step 10: Get the Starter Files

### If you have the zip file from Claude:

1. Download `HogglePrime-starter.zip` (from this chat or your Google Drive)
2. Find the zip in your Downloads folder
3. Right-click the zip → **"Extract All..."**
4. Extract it somewhere temporary (like Downloads)
5. Open the extracted folder
6. You'll see a `HogglePrime` folder and `setup-hoggle-folders.bat`
7. Open that `HogglePrime` folder
8. Select ALL files inside (Ctrl + A)
9. Copy them (Ctrl + C)
10. Navigate to `C:\Users\YourUsername\Documents\HogglePrime`
11. Paste (Ctrl + V)
12. Also copy `setup-hoggle-folders.bat` into the HogglePrime folder

### If you already have it on GitHub (from home):

1. Open **GitHub Desktop**
2. Click **File** → **Clone Repository**
3. Click the **"GitHub.com"** tab
4. Find `HogglePrime` in your repository list
5. For "Local Path", click **Choose...** and navigate to:
   `C:\Users\YourUsername\Documents` (NOT inside HogglePrime - it creates the folder)
6. Click **Clone**

✅ **Checkpoint:** HogglePrime folder contains files (README.md, MASTERPLAN-HOGGLE.md, etc.)

---

## Step 11: Create the Folder Structure

1. Open `C:\Users\YourUsername\Documents\HogglePrime` in File Explorer
2. Find `setup-hoggle-folders.bat`
3. **Double-click it**
4. A black window will appear and create all the folders
5. Press any key when it says "Press any key to continue"

### Verify Folders Created:
Your HogglePrime folder should now contain:
```
HogglePrime/
├── config/
│   └── ollama-modelfiles/
├── knowledge/
│   ├── classroom/
│   ├── construct3/
│   └── multimedia-heroes/
├── logs/
├── memories/
│   ├── daily/
│   ├── feedback/
│   └── people/
├── n8n-workflows/
├── prompts/
├── scripts/
├── webapp/
│   ├── public-display/
│   ├── siteground-terminal/
│   └── teacher-dashboard/
└── [all the files]
```

✅ **Checkpoint:** All subfolders exist

---

## Step 12: Create Your .env File

The .env file stores machine-specific settings (different on each computer).

1. In your HogglePrime folder, find `.env.example`
   
   **Can't see it?** In File Explorer, click **View** (top menu) → check **"Hidden items"**

2. Right-click `.env.example`
3. Click **Copy**
4. Right-click in empty space
5. Click **Paste**
6. You now have `.env.example - Copy`
7. Right-click it → **Rename**
8. Change the name to exactly: `.env` (remove everything else)
9. You might get a warning about changing extensions - click **Yes**

### Edit Your .env:
1. Right-click `.env` → **Open with** → **Notepad**
2. Find this line:
```
HOGGLE_HOME=C:\Users\YOUR_USERNAME\Documents\HogglePrime
```
3. Change `YOUR_USERNAME` to your actual Windows username for this computer
4. Example:
```
HOGGLE_HOME=C:\Users\mrb\Documents\HogglePrime
```
5. Press `Ctrl + S` to save
6. Close Notepad

✅ **Checkpoint:** `.env` file exists with your correct path

---

## Step 13: Create the Three Hoggle Models in Ollama

Now we create the three intelligence tiers for Hoggle.

1. Open **cmd**
2. Navigate to the modelfiles folder by typing:
```
cd C:\Users\YourUsername\Documents\HogglePrime\config\ollama-modelfiles
```
(Replace `YourUsername` with your actual username!)

3. Press Enter

4. Create **Hoggle Quick** (fast, simple responses):
```
ollama create hoggle-quick -f hoggle-quick.modelfile
```
Wait for "success"

5. Create **Hoggle Normal** (standard classroom use):
```
ollama create hoggle-normal -f hoggle-normal.modelfile
```
Wait for "success"

6. Create **Hoggle Deep** (document analysis):
```
ollama create hoggle-deep -f hoggle-deep.modelfile
```
Wait for "success"

### Verify All Models:
```
ollama list
```

You should see:
```
NAME                        SIZE
hoggle-quick               9.0 GB
hoggle-normal              9.0 GB
hoggle-deep                9.0 GB
qwen2.5:14b-instruct       9.0 GB
```

(They're all the same base model, just different configurations)

✅ **Checkpoint:** All four models appear in ollama list

---

# PHASE C: Bring Hoggle to Life!

---

## Step 14: Create Hoggle Persona in Open WebUI

1. Open browser: **http://localhost:3000**
2. Click **"Workspace"** in the left sidebar
3. Click **"Models"**
4. Click the **"+"** button or **"Create a Model"**

### Fill in the form:

| Field | What to Enter |
|-------|---------------|
| **Name** | `Hoggle` |
| **Model ID** | `hoggle` |
| **Base Model (LLM)** | Select `hoggle-normal` from dropdown |
| **Description** | `MTM's resident pig ghost classroom assistant` |

### Add the System Prompt:

1. Open File Explorer
2. Navigate to `HogglePrime\prompts\`
3. Right-click `hoggle-personality.md` → **Open with** → **Notepad**
4. Select ALL the text (Ctrl + A) - everything from "You are Hoggle..." to the end
5. Copy it (Ctrl + C)
6. Go back to Open WebUI
7. Find the **"System Prompt"** text box
8. Paste (Ctrl + V)

### Save:
1. Scroll down
2. Click **"Save"** or **"Create Model"**

✅ **Checkpoint:** Hoggle appears in your Models list

---

## Step 15: Configure Context Length (Important!)

1. Still in **Workspace** → **Models**
2. Find **Hoggle** in the list
3. Click the **pencil icon** (edit) next to it
4. Look for **"Advanced Settings"** or scroll down
5. Find **"Context Length"** or a gear/settings icon near the model dropdown
6. Set context length to: **16384**
7. Save

**Alternative method if you can't find it there:**
1. Start a new chat
2. Look for a **gear/sliders icon** in the top-right of the chat area
3. Click it
4. Find "Context Length" or "num_ctx"
5. Set to 16384

✅ **Checkpoint:** Context length is set to 16384

---

## Step 16: Test Hoggle! 🐷🎉

The moment of truth!

1. Click **"New Chat"** (top left, or the + icon)
2. At the top of the chat, click the **model dropdown**
3. Select **"Hoggle"**
4. Type your first message:

```
Hey Hoggle! Tell me about yourself - how did you end up at MTM?
```

5. Press Enter and wait...

### If Hoggle Responds In Character:
🎉 **CONGRATULATIONS! Phase 1 is COMPLETE!** 🎉

You should see Hoggle tell you about being a pig ghost from the Backrooms who got trapped when Mr. B downloaded a virus looking at cat pictures.

### Test a Few More Things:

**Test his personality:**
```
This class is kinda boring today
```

**Test his limitations:**
```
Can you debug this complex JavaScript async/await error for me?
```
(He should admit it's above his paygrade)

**Test his enthusiasm:**
```
I just finished my first game level in Construct 3!
```

✅ **Checkpoint:** Hoggle responds in character, has personality, knows his limitations

---

# PHASE D: Git Setup (Sync Between Computers)

---

## Step 17: Initialize Git Repository (If Not Cloned)

**Skip this if you already cloned from GitHub in Step 10.**

1. Open **GitHub Desktop**
2. Click **File** → **Add Local Repository...**
3. Browse to: `C:\Users\YourUsername\Documents\HogglePrime`
4. Click **"Select Folder"**
5. It will say "This directory does not appear to be a Git repository"
6. Click **"create a repository"**
7. Fill in:
   - **Name:** HogglePrime
   - **Description:** Hoggle AI Classroom Assistant
   - **Local Path:** Should already be correct
   - **Initialize with README:** Leave UNCHECKED (we have one)
   - **Git Ignore:** None
   - **License:** None
8. Click **"Create Repository"**

### Make Your First Commit:
1. You'll see a list of files on the left
2. Make sure all files are checked
3. At the bottom, type a commit message: `Initial HogglePrime setup on school PC`
4. Click **"Commit to main"**

### Push to GitHub:
1. Click **"Publish repository"** (top bar)
2. **Uncheck** "Keep this code private" if you want (or keep it private)
3. Click **"Publish Repository"**

✅ **Checkpoint:** Repository exists on GitHub, synced with school PC

---

---

# BONUS: Access Hoggle From Your Mac Laptop

Once everything is running on the school PC, you can access Hoggle from any device on the school network!

## On Your Mac (for the Big Screen):
1. Connect Mac to the same school network
2. Open Safari or Chrome
3. Go to: **http://10.81.20.224:3000**
4. Log in with the same account you created
5. Now Hoggle can display on the big screen! 🎉

## On Your Phone (Teacher Dashboard):
1. Connect to school WiFi
2. Open browser
3. Go to: **http://10.81.20.224:3000**
4. You can chat with Hoggle from anywhere in the room!

## Troubleshooting Network Access:
- Make sure both devices are on the same network
- School firewall might block ports - ask IT to allow 3000, 5678, 11434 for internal traffic
- If it doesn't work, you can always use the PC directly

---

# 🎉 SETUP COMPLETE!

---

## School PC Network Info

| Setting | Value |
|---------|-------|
| **Static IP** | 10.81.20.224 |
| **Gateway** | 10.81.20.1 |

This means you can access Hoggle from OTHER devices on the school network!

---

## Your Services

| Service | From School PC | From Other Devices (Mac laptop, phone) |
|---------|----------------|---------------------------------------|
| **Open WebUI** | http://localhost:3000 | http://10.81.20.224:3000 |
| **n8n** | http://localhost:5678 | http://10.81.20.224:5678 |
| **Ollama API** | http://localhost:11434 | http://10.81.20.224:11434 |

💡 **This is how your Mac teacher laptop will display Hoggle on the big screen!**
Just open `http://10.81.20.224:3000` in Safari/Chrome on your Mac.

---

## Quick Reference: Common Commands

### Check if everything is running:
```
docker ps
```

### Restart a container:
```
docker restart open-webui
docker restart n8n
```

### Stop everything:
```
docker stop open-webui n8n
```

### Start everything:
```
docker start open-webui n8n
```

### See Ollama models:
```
ollama list
```

### Chat with Hoggle directly in terminal (no GUI):
```
ollama run hoggle-normal
```
(Type `/bye` to exit)

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "ollama not found" | Restart computer, check system tray for Ollama icon |
| Docker won't start | Enable virtualization in BIOS (ask IT) |
| "Cannot connect to Ollama" in Open WebUI | Set URL to `http://host.docker.internal:11434` in Connections |
| Model dropdown empty | Wait 30 sec and refresh, or restart docker containers |
| Hoggle responds slowly | Make sure you're using `hoggle-normal` not `hoggle-deep` |
| Can't see .env file | Enable "View → Hidden items" in File Explorer |
| Git push fails | Make sure you're signed into GitHub Desktop |

---

## Next Steps (Phase 2: Voice)

Once you've confirmed Hoggle works:

1. Install voice dependencies:
```
pip install faster-whisper piper-tts
```

2. Test speech-to-text
3. Test text-to-speech
4. Create n8n workflow to chain them together

**Let Claude know when you're ready for Phase 2!**

---

## Files to Sync Between Computers

| Syncs via Git | Stays Local (per-machine) |
|---------------|---------------------------|
| prompts/ | .env |
| knowledge/ | memories/people/ (student data) |
| config/ | logs/ |
| n8n-workflows/ | |
| scripts/ | |
| webapp/ | |
| MASTERPLAN-HOGGLE.md | |
| CLAUDE.md | |

For shared memories between home/school, we'll set up Google Drive sync later!

---

*Welcome to MTM, Hoggle.* 🐷👻
