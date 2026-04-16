# Safe to re-render from anywhere — uses a mock script with no side effects.
# To re-render:
#   cd ~/code/ai-knowledge-base
#   vhs -o _branding/demo-installer-v3.gif _branding/demo-installer.tape

Set Theme {"background":"#0C1522","foreground":"#F6F1E9","cursor":"#7DD3FC","black":"#0C1522","red":"#ff6b6b","green":"#7dd3fc","yellow":"#ffd580","blue":"#7dd3fc","magenta":"#b48ead","cyan":"#87d7ff","white":"#F6F1E9","brightBlack":"#1e3050","brightRed":"#ff6b6b","brightGreen":"#7dd3fc","brightYellow":"#ffd580","brightBlue":"#7dd3fc","brightMagenta":"#b48ead","brightCyan":"#87d7ff","brightWhite":"#F6F1E9"}
Set FontFamily "Menlo"
Set FontSize 18
Set Width 860
Set Height 660
Set Padding 24
Set PlaybackSpeed 0.75
Set TypingSpeed 50ms

Hide
Type "ln -sf $PWD/_tools/demo/run-demo-install.sh /tmp/install.sh && chmod +x /tmp/install.sh"
Enter
Sleep 300ms
Type "cd /tmp && clear"
Enter
Sleep 300ms
Show

Type "./install.sh"
Enter
Sleep 42s
