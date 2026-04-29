# Teams Intelligence — Last 30 Days
**Generated:** 2026-04-29 16:40 UTC  **Period:** 2026-03-30 → today  **Source:** Local Teams cache

**Stats:** 2506 signal messages extracted from Teams local cache

## Channel Volume (Top 20)

| # | Channel | Msgs | Signal | Last Active |
|---|---------|------|--------|-------------|
| 1 | (Direct/Meeting) | 305 | 24 | 2026-04-24 |
| 2 | (Direct/Meeting) | 288 | 32 | 2026-04-29 |
| 3 | (Direct/Meeting) | 143 | 16 | 2026-04-28 |
| 4 | (Direct/Meeting) | 128 | 3 | 2026-04-27 |
| 5 | (Direct/Meeting) | 127 | 39 | 2026-04-21 |
| 6 | (Direct/Meeting) | 127 | 29 | 2026-04-28 |
| 7 | (Direct/Meeting) | 120 | 24 | 2026-04-24 |
| 8 | Claude POC Developer group | 118 | 19 | 2026-04-29 |
| 9 | Primary Major Incident Management Bridge | 110 | 21 | 2026-04-27 |
| 10 | (Direct/Meeting) | 110 | 4 | 2026-04-01 |
| 11 | (Direct/Meeting) | 83 | 19 | 2026-04-28 |
| 12 | Claude POC | 71 | 9 | 2026-04-29 |
| 13 | (Direct/Meeting) | 65 | 13 | 2026-04-24 |
| 14 | (Direct/Meeting) | 62 | 14 | 2026-04-27 |
| 15 | (Direct/Meeting) | 58 | 7 | 2026-04-27 |
| 16 | (Direct/Meeting) | 54 | 15 | 2026-04-23 |
| 17 | (Direct/Meeting) | 51 | 4 | 2026-04-29 |
| 18 | (Direct/Meeting) | 39 | 5 | 2026-04-23 |
| 19 | (Direct/Meeting) | 39 | 5 | 2026-04-22 |
| 20 | (Direct/Meeting) | 38 | 16 | 2026-04-22 |

## Infrastructure Channels

### Claude POC Developer group
**118 messages** · 2026-04-24 → 2026-04-29 · 19 signal msgs

**🔴 Incidents / Issues**
- `2026-04-24 13:56` **Mohamed Ali:** I'm on a mac, and just accepted the invite, and installed the app.� � Mine looks to have worked. Had an error with a prompt, but it worked afterwards.� �
- `2026-04-24 15:01` **Mohamed Ali:** Carl Hinsman There is no input to prompt, "New Conversation" results in same black screen. 📷 Mohamed, what did you do to invoke a prompt in the desktop app? Carl Hinsman For me it was just through gui, I did not see the …
- `2026-04-24 15:55` **Carl Hinsman:** Mohamed Ali Carl Hinsman For me it was just through gui, I did not see the black screen that you have. I'm curious if you invoke through claude code cli, if you have the same issue? A reinstall of the deskt… i do not hav…
- `2026-04-24 16:18` **Mohamed Ali:** Carl Hinsman i do not have the issue with CC cli. i have tried several different approaches now, I was unable to do a clean reinstall because I was blocked from removing the existing install, and tried to force… When app…
- `2026-04-24 17:04` **Chase Allen:** I've heard that the copilot version of claude models are watered down but cant confirm
- `2026-04-24 17:41` **Matthew Ruby:** The model is the brain. The tooling/harness around it is what turns that brain into useful action. Same model in Copilot vs Claude Code isn't apples to apples — the harness differs a lot. Claude Code's agentic loop (plan…
- `2026-04-27 14:39` **Jim Greene:** 2026-04-27 10:35:11 [warn] Blocked redirect to disallowed URL { href: ' https://gateway.zscalertwo.net/_sm_ccik?_sm_rid=RrjQDMHHTcT2q3SR7Q5W5FNRZ0FrbSnM13Wr2W6FrbSnM13Wr2W… } 2026-04-27 10:35:11 [warn] [growthbook] API r…
- `2026-04-27 16:32` **Chase Allen:** I found this to be handy as well https://dev.to/colocodes/claude-code-crash-course-m3o
- `2026-04-28 15:05` **Jim Greene:** We have (950+) repositories in Github (GH).�� � Variants of this command are useful for digging in:�� � # show me, with JSON output, all CTAgile repos whose name starts with "leep-", ends with "-serverless", and is not a…
- `2026-04-29 11:48` **Carl Hinsman:** i used the following to capture the Claude app startup: /Applications/Claude.app/Contents/MacOS/Claude --enable-logging --v=1 2>&1 | tee /tmp/claude_debug.log That log reflects that every API call — /api/desktop/features…
- `2026-04-29 16:27` **Jim Greene:** Carl Hinsman i used the following to capture the Claude app startup: /Applications/Claude.app/Contents/MacOS/Claude --enable-logging --v=1 2>&1 | tee /tmp/claude_debug.log That log reflects that every API cal… Great anal…

**✅ Resolved / Complete**
- `2026-04-24 12:53` **Andrew Skvorak:** As I said in my latest email, I messed up and forgot to get the proper AD group populated with your ID's so you should hit a roadblock when you try to login with SSO. I am working to get that resolved now.�
- `2026-04-24 18:52` **Mohamed Ali:** I'm noticing with Opus 4.7 it eats through the usage limit much faster than Opus 4.6, a couple prompts and it was done. �I don't know how useful the adaptive thinking toggle will be, but so far so good.�
- `2026-04-29 11:20` **Jim Greene:** So, when Claude app, which just updated itself on my Mac, starts, it attemps to retrieve account information. �Logging in the macOS "Console" app shows that it receives this response from an HTTP request:

**📋 Action Items**
- `2026-04-27 20:52` **Andrew Skvorak:** Welcome to the new folks I just added - please take a look through the chat history as people are already sharing learnings and other fun stuff. Welcome!
- `2026-04-29 12:05` **Bridge Schaad:** Carl Hinsman Bridge, have you been able to resolve the black screen (with Paul's help maybe)? I haven't but I'll follow up today and include some of the newer details

**💡 Knowledge / Findings**
- `2026-04-24 14:35` **Michael Hern�ndez:** and it turns out Claude thinks that is not cool
- `2026-04-24 15:55` **Carl Hinsman:** Mohamed Ali Carl Hinsman For me it was just through gui, I did not see the black screen that you have. I'm curious if you invoke through claude code cli, if you have the same issue? A reinstall of the deskt… i do not hav…
- `2026-04-24 16:18` **Mohamed Ali:** Carl Hinsman i do not have the issue with CC cli. i have tried several different approaches now, I was unable to do a clean reinstall because I was blocked from removing the existing install, and tried to force… When app…
- `2026-04-27 14:11` **Jim Greene:** After burning through my allocation with Opus 4.6 in March, I tried Sonnet 4.6 (actually, Auto in VSC, which selected Sonnet for me at a 0.1 discount) and found that it's pretty much (it feels ) just as capable, at least…
- `2026-04-28 15:05` **Jim Greene:** We have (950+) repositories in Github (GH).�� � Variants of this command are useful for digging in:�� � # show me, with JSON output, all CTAgile repos whose name starts with "leep-", ends with "-serverless", and is not a…
- `2026-04-29 11:22` **Jim Greene:** I think that because it doesn't or can't respond to that page (can't click Continue), the Claude app just sits there, waiting for more.
- `2026-04-29 11:48` **Carl Hinsman:** i used the following to capture the Claude app startup: /Applications/Claude.app/Contents/MacOS/Claude --enable-logging --v=1 2>&1 | tee /tmp/claude_debug.log That log reflects that every API call — /api/desktop/features…

**💬 Notable Exchanges**
- `2026-04-28 16:00` **Aaron Scifres:** i asked it a different way and it told me it did have one but i'd have to connect it via "cowork" as opposed to via the chat
- `2026-04-29 10:11` **Carl Hinsman:** Bridge Schaad I've been seeing the same thing -- reached out to Paul Lindahl end of Friday and waiting to hear back Bridge , have you been able to resolve the black screen (with Paul's help maybe)?
- `2026-04-29 10:18` **Chase Allen:** Claude Desktop is having a black screen on Windows now as well.�
- `2026-04-29 10:54` **Ben Hoisington:** If you go to claude.ai in a browser, do you get a zscaler message to about the site?
- `2026-04-29 11:07` **Andrew Skvorak:** I also experienced a black screen with Claude this morning. Rebooted and that works now. Went to claude.ai in browser as Ben asked and received no Zscaler popup message.�
- `2026-04-29 11:15` **Jim Greene:** Ben Hoisington If you go to claude.ai in a browser, do you get a zscaler message to about the site? Site works for me:�
- `2026-04-29 11:21` **Jim Greene:** (I saved the HTML in the log to a text file, then opened the file in Safari to get this screenshot)
- `2026-04-29 11:26` **Carl Hinsman:** Jim Greene Site works for me: 📷 Site works for me. Desktop Claude does not. Reboot has no effect.
- `2026-04-29 11:26` **Chase Allen:** Ah - you're all correct.� � Seems like Claude Desktop (for windows) is a PWA - so I had to do the "Are you sure you want to visit this site?" in Chrome and now the Desktop App is loading.�
- `2026-04-29 13:32` **Chase Allen:** Planning agent uses very few tokens for those who are hitting limits

### Primary Major Incident Management Bridge
**110 messages** · 2026-03-30 → 2026-04-27 · 21 signal msgs

**🔴 Incidents / Issues**
- `2026-03-30 16:41` **Jim Greene:** The deployed pods for app-ecom-pci-udal in prod GCP were missing some YAML updates. �After a GCP patch this morning, the pods were restarted. �When they came back up, we had removed secrets from the secrets vault, but th…
- `2026-04-09 15:55` **Missy Burke:** loyalty is the only thing that is not normal and started at 10:30am yesterday. �had a couple huge spikes on the 7th but came right back down then
- `2026-04-09 16:42` **Brian Antonelli:** Jesús Moreira https://llbean.atlassian.net/browse/ITS-9032 📄 Jesús Moreira Regarding this ticket -- For clarification, this incident did not affect an Ecom customer’s ability to view or apply Bean Bucks to an order, as n…
- `2026-04-09 17:09` **Jes�s Moreira:** Brian Antonelli Jesús Moreira Regarding this ticket -- For clarification, this incident did not affect an Ecom customer’s ability to view or apply Bean Bucks to an order, as noted in the ITS ticket. The issue speci… Than…
- `2026-04-09 17:25` **Sundar Sivashunmugam:** Jes�s Moreira Thank you for the details. I ensured the ticket reflects the correct context. Gonzalo � S�nchez �Can we send an updated ALL CLEAR email with the Ecom impact mentioned above also stating no order impact? �Al…
- `2026-04-09 22:52` **Curt Combar:** Actions taken earlier today on the MF for this issue: Actions Taken: The issue was resolved by terminating (purging/killing) a runaway KM12 transaction in the OLT1 CICS region that was consuming excessive CPU. A long‑run…
- `2026-04-09 22:54` **Curt Combar:** Issue was occurring from 6:09PM to about 6:43PM but has since subsided.
- `2026-04-09 23:02` **Raju Rai:** 11.57.53 STC14629� DSNB260I� -DBP1 DSNB1PCK WARNING - A READER HAS BEEN� 149���� �� 149������������ RUNNING FOR 1582 MINUTES������������������������������������� �� 149����������������������� CORRELATION NAME=POOLKM12000…
- `2026-04-10 14:11` **Curt Combar:** Still seeing occasional timeout spikes with rewards lookup this morning. � � Raju � Rai � Jay � Seiler �I see no one is assigned https://llbean.atlassian.net/browse/ITS-9032?assignee=557058%3A28bdf4be-c8c9-4bc2-b519-4535…
- `2026-04-10 14:17` **Jay Seiler:** Curt Combar Still seeing occasional timeout spikes with rewards lookup this morning. 📷 Raju Rai Jay Seiler I see no one is assigned https://llbean.atlassian.net/browse/ITS-9032?assignee=557058%3A28bdf4be-c8c9… This would…
- `2026-04-10 14:27` **Cliff Anderson:** Curt Combar Still seeing occasional timeout spikes with rewards lookup this morning. 📷 Raju Rai Jay Seiler I see no one is assigned https://llbean.atlassian.net/browse/ITS-9032?assignee=557058%3A28bdf4be-c8c9… Are you ge…
- `2026-04-10 14:30` **Curt Combar:** Not sustained, so not a major concern for this morning, but tells me there's still a problem?
- `2026-04-10 15:31` **Jay Seiler:** Is there currently an ongoing issue? My understanding was we just had a burp and things are operating within normal parameters.�
- `2026-04-10 15:33` **Gonzalo S�nchez:** Hello team, can we please create a separate chat to TS this issue?�
- `2026-04-22 13:27` **Fred O'Farrell:** What's the issue?
- `2026-04-22 13:29` **Alonso Bonilla:** Fred O'Farrell What's the issue? Sorry, that was a misclick

**✅ Resolved / Complete**
- `2026-03-30 16:41` **Jim Greene:** The deployed pods for app-ecom-pci-udal in prod GCP were missing some YAML updates. �After a GCP patch this morning, the pods were restarted. �When they came back up, we had removed secrets from the secrets vault, but th…
- `2026-04-09 17:25` **Sundar Sivashunmugam:** Jes�s Moreira Thank you for the details. I ensured the ticket reflects the correct context. Gonzalo � S�nchez �Can we send an updated ALL CLEAR email with the Ecom impact mentioned above also stating no order impact? �Al…
- `2026-04-09 17:54` **Pablo Rodr�guez:** Sundar Sivashunmugam Gonzalo Sánchez Can we send an updated ALL CLEAR email with the Ecom impact mentioned above also stating no order impact? Also any details on the Loyalty Membeship Lookup services degradation due… Wi…
- `2026-04-09 22:52` **Curt Combar:** Actions taken earlier today on the MF for this issue: Actions Taken: The issue was resolved by terminating (purging/killing) a runaway KM12 transaction in the OLT1 CICS region that was consuming excessive CPU. A long‑run…
- `2026-04-27 13:12` **Alonso Bonilla:** Daniel Coto Alonso Bonilla or Josu� Real Could you please run ECM00753 and INT00034 and INT00035 The jobs completed successfully�

**📋 Action Items**
- `2026-04-10 15:33` **Gonzalo S�nchez:** Hello team, can we please create a separate chat to TS this issue?�

**🏛 Decisions**
- `2026-04-10 14:17` **Cliff Anderson:** Jay Seiler Mainframe is not the bottleneck. It's just idling. Plenty of juice there. Agreed. Our max query response time has stayed ~100ms with the 99% percentile < 50ms
- `2026-04-10 14:23` **Curt Combar:** Cliff Anderson Agreed. Our max query response time has stayed ~100ms with the 99% percentile < 50ms "our" being the rewards service?

**💡 Knowledge / Findings**
- `2026-03-30 16:48` **Jim Greene Jr:** kubectl apply works by doing a 3‑way merge : Why? Because: This is a strategic merge patch Lists don’t imply “these are the only items” Kubernetes can’t safely assume deletion unless explicitly told This applies to: env …
- `2026-04-09 22:52` **Curt Combar:** Actions taken earlier today on the MF for this issue: Actions Taken: The issue was resolved by terminating (purging/killing) a runaway KM12 transaction in the OLT1 CICS region that was consuming excessive CPU. A long‑run…
- `2026-04-10 14:17` **Jay Seiler:** Curt Combar Still seeing occasional timeout spikes with rewards lookup this morning. 📷 Raju Rai Jay Seiler I see no one is assigned https://llbean.atlassian.net/browse/ITS-9032?assignee=557058%3A28bdf4be-c8c9… This would…

**💬 Notable Exchanges**
- `2026-04-27 12:28` **Josu� Real:** https://llbean.atlassian.net/browse/ITS-10860
- `2026-04-27 12:30` **Missy Burke:** Middleware has restarted some of our caches and we are reloading now..�
- `2026-04-27 12:33` **<Undefined> <Undefined>:** Primary Major Incident Management Bridge Play
- `2026-04-27 12:33` **<Undefined> <Undefined>:** Primary Major Incident Management Bridge Play
- `2026-04-27 12:37` **<Undefined> <Undefined>:** Primary Major Incident Management Bridge Play
- `2026-04-27 13:03` **<Undefined> <Undefined>:** Primary Major Incident Management Bridge Play
- `2026-04-27 13:03` **<Undefined> <Undefined>:** Primary Major Incident Management Bridge Play
- `2026-04-27 13:04` **Daniel Coto:** Alonso � Bonilla �or Josu� � Real Could you please run ECM00753 and INT00034 and INT00035 �
- `2026-04-27 13:06` **Bernal P�rez:** Hi team, was the bridge opened by mistake again a second ago? Just want to make sure, in case something is needed
- `2026-04-27 13:09` **Jim Greene:** Yes: mistake or accidental join. �I joined for a moment after someone else did. �Shiny. �Nothing of note going on at present.

### Claude POC
**71 messages** · 2026-04-24 → 2026-04-29 · 9 signal msgs

**🔴 Incidents / Issues**
- `2026-04-27 18:13` **Nick Mastors:** Hmmm. �I've been trying for a while now and have been unsuccessful. � Andrew � Skvorak , Claude seems convinced that it's an Access issue (though I'm not sure why it would work for Josh and not me). �Thoughts?
- `2026-04-27 20:02` **Nick Mastors:** Nick Mastors Hmmm. I've been trying for a while now and have been unsuccessful. Andrew Skvorak, Claude seems convinced that it's an Access issue (though I'm not sure why it would work for Josh and not me). Tho… Claude wa…
- `2026-04-29 12:19` **Marco Hern�ndez:** I had the same issue yesterday - I restarted my PC and it worked again
- `2026-04-29 12:21` **Stacy Owen:** I'll try restarting, I shut down my laptop last night. Maybe is off time was too much and wants to stay on holiday.

**✅ Resolved / Complete**
- `2026-04-24 11:33` **Andrew Skvorak:** I am almost done adding you all to our llbean account in Claude - just a few more to go. But wanted to get this group chat setup so we have a forum.�
- `2026-04-28 10:27` **Andrew Skvorak:** Good morning. Can someone who has done this recently answer Christy's email, please? I cannot recall the options or process for 2-factor auth at that step. Thank you.
- `2026-04-29 12:15` **Stacy Owen:** already done and still a blank Claude Claude.ai browser Claude desktop app after browser �log in�
- `2026-04-29 15:56` **Marco Hern�ndez:** Josh � McHenry �and Andrew � Skvorak �Hi - I haven't tested it personally, but Alex did. He mentioned that the final result isn't great, possibly because it's still a preview and it consumes too many tokens. I'm happy to…

**📋 Action Items**
- `2026-04-27 20:52` **Andrew Skvorak:** Welcome to the new folks I just added - please take a look through the chat history as people are already sharing learnings and other fun stuff. Welcome!

**💡 Knowledge / Findings**
- `2026-04-29 15:56` **Marco Hern�ndez:** Josh � McHenry �and Andrew � Skvorak �Hi - I haven't tested it personally, but Alex did. He mentioned that the final result isn't great, possibly because it's still a preview and it consumes too many tokens. I'm happy to…

**💬 Notable Exchanges**
- `2026-04-28 19:54` **Stacy Owen:** Has anyone setup a Routine?�
- `2026-04-28 20:36` **Nick Mastors:** Josh McHenry 100%, and good to note when you exhaust the credits. Opus uses tokens much faster than Sonnet - do you know which you were on? I was on Opus 4.7 thanks for the tips!
- `2026-04-28 23:25` **Christy van Voorhees:** Fingers crossed this is not my next dramatic moment: https://www.the-independent.com/tech/claude-ai-agent-deletes-startup-anthropic-b2966176.html
- `2026-04-29 12:13` **Stacy Owen:** Andrew � Skvorak �I'm having issues with Claude desktop app. It is just one big blank screen, yet the service is running.� � � it is working within Word and office file types once I re-logged in. Still nothing for the de…
- `2026-04-29 12:14` **Ben Hoisington:** Go to claude.ai in a browser, you will most likely get a captive portal about accepting the risk of going to an AI page. Accept and relaunch Claude.
- `2026-04-29 12:14` **Andrew Skvorak:** Ben beat me to it!!!
- `2026-04-29 12:28` **Stacy Owen:** Restarting, ensuring I login on the browser first then launch the desktop app worked.�
- `2026-04-29 14:22` **Josh McHenry:** Just ran into my token limit - the weekly one - about three hours before it resets. �
- `2026-04-29 14:25` **Josh McHenry:** Marco � Hern�ndez �- it took a little effort but I found a way to have Claude Code help with PowerApps. �It's a preview feature and getting the two things talking to one another wasn't trivial, but it seems to be working…
- `2026-04-29 14:27` **Andrew Skvorak:** Josh � McHenry �- I am interested to hear more about this. Can you, me and Marky meet to discuss?�

## Today (2026-04-29)

### Claude POC Developer group (14 msgs)
- `2026-04-29 10:11` **Carl Hinsman:** Bridge Schaad I've been seeing the same thing -- reached out to Paul Lindahl end of Friday and waiting to hear back Bridge , have you been able to resolve the black screen (with Pa…
- `2026-04-29 10:18` **Chase Allen:** Claude Desktop is having a black screen on Windows now as well.�
- `2026-04-29 10:54` **Ben Hoisington:** If you go to claude.ai in a browser, do you get a zscaler message to about the site?
- `2026-04-29 11:07` **Andrew Skvorak:** I also experienced a black screen with Claude this morning. Rebooted and that works now. Went to claude.ai in browser as Ben asked and received no Zscaler popup message.�
- `2026-04-29 11:15` **Jim Greene:** Ben Hoisington If you go to claude.ai in a browser, do you get a zscaler message to about the site? Site works for me:�
- `2026-04-29 11:20` **Jim Greene:** `[resolved]` So, when Claude app, which just updated itself on my Mac, starts, it attemps to retrieve account information. �Logging in the macOS "Console" app shows that it receives this respon…
- `2026-04-29 11:21` **Jim Greene:** (I saved the HTML in the log to a text file, then opened the file in Safari to get this screenshot)
- `2026-04-29 11:22` **Jim Greene:** `[knowledge]` I think that because it doesn't or can't respond to that page (can't click Continue), the Claude app just sits there, waiting for more.
- `2026-04-29 11:26` **Carl Hinsman:** Jim Greene Site works for me: 📷 Site works for me. Desktop Claude does not. Reboot has no effect.
- `2026-04-29 11:26` **Chase Allen:** Ah - you're all correct.� � Seems like Claude Desktop (for windows) is a PWA - so I had to do the "Are you sure you want to visit this site?" in Chrome and now the Desktop App is l…
- `2026-04-29 11:48` **Carl Hinsman:** `[incident,knowledge]` i used the following to capture the Claude app startup: /Applications/Claude.app/Contents/MacOS/Claude --enable-logging --v=1 2>&1 | tee /tmp/claude_debug.log That log reflects tha…
- `2026-04-29 12:05` **Bridge Schaad:** `[action]` Carl Hinsman Bridge, have you been able to resolve the black screen (with Paul's help maybe)? I haven't but I'll follow up today and include some of the newer details
- `2026-04-29 13:32` **Chase Allen:** Planning agent uses very few tokens for those who are hitting limits
- `2026-04-29 16:27` **Jim Greene:** `[incident]` Carl Hinsman i used the following to capture the Claude app startup: /Applications/Claude.app/Contents/MacOS/Claude --enable-logging --v=1 2>&1 | tee /tmp/claude_debug.log That log…

### (Direct/Meeting) (11 msgs)
- `2026-04-29 11:14` **Andrew Skvorak:** Morning gentlemen. I created a quick and dirty app with Claude on my laptop that requires a Claude API key to run it so that it can make API calls to one of the Claude models to pr…
- `2026-04-29 11:17` **Andrew Skvorak:** This feels like a line to cross, so I wanted to discuss with you guys. I don't mind the costs for the POC as we have the funding. I'm thinking about more long-term stuff - could we…
- `2026-04-29 11:41` **Tim McGlothin:** `[incident]` Go back to some other longer running chats you've had with claude and ask it to summerize what that conversation would have cost in Api credits. It can be a real eye opener. � One …
- `2026-04-29 11:43` **Josh Andrews:** I don't know a ton about the setup or management, but would want to make sure they are stored in a secure manner, permissions were appropriately limited, etc. Those are things that…
- `2026-04-29 11:46` **Tim McGlothin:** When I visited TI in TX a few weeks ago we weere talking about how they use Claude, they give each user a certain dollar amount per week.. General users get 10 bucks, devs get more…
- `2026-04-29 11:52` **Ben Hoisington:** `[decision]` It feels like most platforms are migrating to the pay by usage model. Looking forward it feels prudent to leverage a platform that allows us to use models from different vendors vs…
- `2026-04-29 11:54` **Tim McGlothin:** Also, a hybrid approach in the long term.. Leverage local models for day to day runtime work flows. Use the frontier model to design the solution that runs locally to keep recurrin…
- `2026-04-29 12:22` **Ben Hoisington:** `[incident]` I think we're seeing two different issues with the "black screens". One is the captive portal for AI from Zscaler, the other is not trusting the Zscaler certificate from ssl inspec…
- `2026-04-29 12:23` **Ben Hoisington:** That allows the app to trust the Zscaler cert.
- `2026-04-29 12:43` **Andrew Skvorak:** `[decision]` Ben Hoisington It feels like most platforms are migrating to the pay by usage model. Looking forward it feels prudent to leverage a platform that allows us to use models from diffe…
- `2026-04-29 12:44` **Andrew Skvorak:** I'm sure there's more, too.... I think we need to meet to discuss. Will try to find some time.

### Claude POC (11 msgs)
- `2026-04-29 12:13` **Stacy Owen:** Andrew � Skvorak �I'm having issues with Claude desktop app. It is just one big blank screen, yet the service is running.� � � it is working within Word and office file types once …
- `2026-04-29 12:14` **Ben Hoisington:** Go to claude.ai in a browser, you will most likely get a captive portal about accepting the risk of going to an AI page. Accept and relaunch Claude.
- `2026-04-29 12:14` **Andrew Skvorak:** Ben beat me to it!!!
- `2026-04-29 12:15` **Stacy Owen:** `[resolved]` already done and still a blank Claude Claude.ai browser Claude desktop app after browser �log in�
- `2026-04-29 12:19` **Marco Hern�ndez:** `[incident]` I had the same issue yesterday - I restarted my PC and it worked again
- `2026-04-29 12:21` **Stacy Owen:** `[incident]` I'll try restarting, I shut down my laptop last night. Maybe is off time was too much and wants to stay on holiday.
- `2026-04-29 12:28` **Stacy Owen:** Restarting, ensuring I login on the browser first then launch the desktop app worked.�
- `2026-04-29 14:22` **Josh McHenry:** Just ran into my token limit - the weekly one - about three hours before it resets. �
- `2026-04-29 14:25` **Josh McHenry:** Marco � Hern�ndez �- it took a little effort but I found a way to have Claude Code help with PowerApps. �It's a preview feature and getting the two things talking to one another wa…
- `2026-04-29 14:27` **Andrew Skvorak:** Josh � McHenry �- I am interested to hear more about this. Can you, me and Marky meet to discuss?�
- `2026-04-29 15:56` **Marco Hern�ndez:** `[resolved,knowledge]` Josh � McHenry �and Andrew � Skvorak �Hi - I haven't tested it personally, but Alex did. He mentioned that the final result isn't great, possibly because it's still a preview and i…

### (Direct/Meeting) (8 msgs)
- `2026-04-29 14:11` **Jason Mills:** `[knowledge]` He probably wont talk about it on this call because I said we would want to get the right audience for it, but David shared this offering that he found for AI/Nutanix (as well as o…
- `2026-04-29 14:13` **Tim McGlothin:** theyre claiming they have an official MCP connector from Nutanix
- `2026-04-29 14:14` **Tim McGlothin:** or I wonder if its their own mcp connector using Nutanix APIs
- `2026-04-29 14:14` **Jason Mills:** Thats what I saw just from a quick glance
- `2026-04-29 14:15` **Jason Mills:** They have like 150 solutions listed, basically just APIs that they have the understanding of
- `2026-04-29 14:15` **Jason Mills:** They claim 2 weeks to prod for any updates, or new products requested
- `2026-04-29 14:16` **Tim McGlothin:** yeah, that we can build ourselves .. there's other open source projects as well.. just worry about support�
- `2026-04-29 14:16` **Tim McGlothin:** the tech is so young I don't think trust anybody's claims around SLAs

### (Direct/Meeting) (7 msgs)
- `2026-04-29 14:19` **Ben Hoisington:** There is no official MCP server. He did find an MCP aggregator for Infrastructure teams. It appears they're probably building their own MCP servers based on published api docs.
- `2026-04-29 14:19` **Jason Mills:** I already told him, lol
- `2026-04-29 14:20` **Ben Hoisington:** An interesting concept we may bring to the broader AI enablement/infrastructure leadership group.
- `2026-04-29 14:20` **Tim McGlothin:** yeah, there's a lot of people racing to get something out... easy enough to roll our own too, but the support behind an official connector would provide the real value
- `2026-04-29 14:22` **Jason Mills:** That is a new lens I have been using for a lot of products, what is the company providing that we couldn't just build ourselves
- `2026-04-29 14:23` **Jason Mills:** Especially around new, niche offerings
- `2026-04-29 14:23` **Tim McGlothin:** back to the old build-vs-buy decisions ... selling products at those high saas costs gets harder and harder now

### LL Bean, CV Project - Touchpoint (4 msgs)
- `2026-04-29 15:05` **<Undefined> <Undefined>:** LL Bean, CV Project - Touchpoint Play
- `2026-04-29 15:05` **<Undefined> <Undefined>:** {\"scopeId\":\"9f0045c7-fd58-4f87-92a8-7055a8d8513a\",\"storageId\":\"ff955118-715e-4d71-a164-9a7eb84fa1b8@de9231de-45f4-4325-ae07-8ae72052517e\",\"callId\":\"9f0045c7-fd58-4f87-92…
- `2026-04-29 15:13` **<Undefined> <Undefined>:** LL Bean, CV Project - Touchpoint Play
- `2026-04-29 15:13` **<Undefined> <Undefined>:** LL Bean, CV Project - Touchpoint Play
