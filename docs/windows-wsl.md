# AIKB on Windows — WSL Setup

AIKB uses standard Unix tooling (bash, git, python3). On Windows, these run inside
WSL (Windows Subsystem for Linux) — a full Linux environment built into Windows 10/11.

---

## Step 1: Install WSL

Open PowerShell as Administrator and run:

    wsl --install

This installs WSL 2 and Ubuntu. Reboot when prompted.

---

## Step 2: Open Ubuntu

After rebooting, open the "Ubuntu" app from the Start menu. Create a Linux
username and password (can be different from your Windows credentials).

---

## Step 3: Install Git

    sudo apt update && sudo apt install git -y

---

## Step 4: Clone your AIKB repo *inside WSL*

⚠ Important: Clone inside WSL's own filesystem, not the Windows filesystem.

Do this:
    cd ~
    git clone https://github.com/YOUR_USERNAME/AIKB.git ~/code/AIKB
    cd ~/code/AIKB

Not this (slow and may cause permission issues):
    cd /mnt/c/Users/you/
    git clone ...

---

## Step 5: Run the installer

    chmod +x install.sh
    ./install.sh

---

## Troubleshooting

**"git: command not found"**
→ Run: sudo apt install git -y

**"python3: command not found"**
→ Run: sudo apt install python3 python3-pip -y

**Slow Git performance**
→ You're likely on the Windows filesystem (/mnt/c/...). Move to ~/code/ inside WSL.

**Claude Code / Gemini CLI not found in WSL**
→ Install them inside WSL: see their respective install docs.
   Note: tools installed in Windows are not automatically available in WSL.

**Accessing Windows files from WSL**
→ Your Windows C: drive is at /mnt/c/ — you can read/write files there,
   but keep code repos in WSL's own filesystem for best performance.
