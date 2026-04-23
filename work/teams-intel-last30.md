# Teams Intelligence Report — Last 30 Days
**Generated:** 2026-04-23  **Period:** 2026-03-24 → 2026-04-23  **Source:** Microsoft Teams local cache

**Stats:** 2879 messages · 55 conversations

## Channel Volume (Top 20)
| # | Channel | Msgs | Last Activity |
|---|---------|------|---------------|
| 1 | AI Nerds | 377 | 2026-04-22 |
| 2 | Claude initial setup | 243 | 2026-04-22 |
| 3 | 19:2f127f3c-3a92-4a63-b3be-c2e804519744_ | 204 | 2026-04-01 |
| 4 | GitHub Copilot Devs | 190 | 2026-04-23 |
| 5 | Nutanix Bi-Annual Cluster Upgrades | 163 | 2026-04-21 |
| 6 | Unix Server and Storage Team | 154 | 2026-04-23 |
| 7 | 19:meeting_ZjlmY2FiNmItNDI3NS00ZjdkLWI5Y | 143 | 2026-04-22 |
| 8 | 19:d60d29c1-76da-4ec7-806f-dcfd57597d1a_ | 134 | 2026-04-22 |
| 9 | 19:069489e1b6d741ac9f7151a322c46e5c@thre | 106 | 2026-04-03 |
| 10 | Server Engineering Team - ALL | 103 | 2026-04-22 |
| 11 | 19:wQX_vY6BHOfrbtFwmG6l1PhcJO8-U3dSSfPiZ | 95 | 2026-04-23 |
| 12 | IS Connect Hub | 93 | 2026-04-23 |
| 13 | Unix Server | TOC Team Chat | 89 | 2026-04-23 |
| 14 | 19:d60d29c1-76da-4ec7-806f-dcfd57597d1a_ | 65 | 2026-04-23 |
| 15 | 19:7aa2c1dd-7d68-47ed-b04e-6c45a257dcc0_ | 57 | 2026-04-22 |
| 16 | 19:656213c4-135f-42d8-9ec2-e98c8440fa72_ | 53 | 2026-04-01 |
| 17 | 19:a0e6998c-45fa-4005-9859-716783d76fa0_ | 53 | 2026-04-17 |
| 18 | 19:5d13cafe-0f97-4196-8858-d9451eb239de_ | 48 | 2026-04-22 |
| 19 | 19:6fa035f3-c521-41be-b080-d1f32df74a83_ | 45 | 2026-04-23 |
| 20 | 19:6ff12c6e-2665-418d-a60a-d5f848351980_ | 36 | 2026-04-16 |

## Infrastructure Channel Summaries

### Nutanix Bi-Annual Cluster Upgrades
**163 messages** · 2026-03-30 → 2026-04-21

- `2026-04-10 12:33` **Steven Foxe:** Ok. �Thanks again for that info Hank!
- `2026-04-10 12:33` **Hank Uhl:** np man!
- `2026-04-10 12:37` **Hank Uhl:** im going to ask the Nutanix rep to take one last look at the cluster, and if Temoc says things look good, have him close the case
- `2026-04-10 13:38` **Fabio Campos:** regarding the ntx-dc1-ahv02: �
- `2026-04-10 13:38` **Brooke Curtin-Johnson:** thats actually �not bad lol
- `2026-04-10 13:54` **Fabio Campos:** no right�
- `2026-04-10 13:54` **Fabio Campos:** good progress�
- `2026-04-10 13:55` **Brooke Curtin-Johnson:** Dont Jinx it!
- `2026-04-10 14:46` **Brooke Curtin-Johnson:** David Snyder just got back to me re: single node cluster firmware updates
- `2026-04-10 14:47` **Brooke Curtin-Johnson:** He basically said there is no documentation on it and sent me what we have already
- `2026-04-10 14:47` **Brooke Curtin-Johnson:** So I am not sure where we go from here
- `2026-04-10 14:48` **Brooke Curtin-Johnson:** Will do some more digging
- `2026-04-10 15:25` **Fabio Campos:** Fabio Campos regarding the ntx-dc1-ahv02: 📷 Finished! 🙂🙂
- `2026-04-10 15:44` **Steven Foxe:** Nicholas � Hopson �- When you have a minute, can you post a quick update on the status of the ntx-dc1-ahv03 upgrade? �Are you all set with support or need a hand with anything?
- `2026-04-10 15:49` **Nicholas Hopson:** Yeah we had to reinstall AHV on one of the hosts that crashed during firmware updates and now the cluster resilience is back to normal. there is an alert in PC for inconsistent vsw
- `2026-04-10 15:51` **Nicholas Hopson:** So long story short the updates are complete, I still need to do the networking vNIC component but am holding off now with the payment issues going on I don't want to cause anythin
- `2026-04-10 15:52` **Steven Foxe:** Ok, thank you! �
- `2026-04-10 16:13` **Steven Foxe:** I've uploaded a spreadsheet called Status and Issue Tracking to the Shared tab of this chat. �I took a stab at adding the actual start dates and duration to the Status sheet and th
- `2026-04-10 18:59` **Nicholas Hopson:** Update on the "Inconsistent Virtual Switch State Detected" error, the solution is the edit the vSwitch which will cause the rolling hypervisor restart so I'm going to make the chan
- `2026-04-21 16:50` **Brooke Curtin-Johnson:** Here is some documentation on single node cluster firmware updates- I still have a few questions out to David S. on process.

### Unix Server and Storage Team
**154 messages** · 2026-03-24 → 2026-04-23

- `2026-04-22 13:42` **Tim McGlothin:** ASM not starting ...�
- `2026-04-22 13:43` **Tim McGlothin:** disks are showing up at the OS level, we just rebooted and checking it again now
- `2026-04-22 14:55` **Hank Uhl:** Tim � McGlothin �any update on this? �looks like some oracle stuff is up, port 1521 is listening
- `2026-04-22 14:56` **Tim McGlothin:** Eric has a ticket open with oracle, he just pinged me but my worthless laptop has crashed on me twice today already.. Rebooting again
- `2026-04-22 14:56` **Hank Uhl:** does this mean that the databases that run on this server are currently down?
- `2026-04-22 14:57` **Tim McGlothin:** They were yes
- `2026-04-22 14:57` **Hank Uhl:** i'll let dave know
- `2026-04-22 15:05` **Hank Uhl:** LLORACP1 is the only business DB running on this, and eric is not sure if anyone uses it anymore. �no one has complained. �i have informed Dave, in case something comes his way
- `2026-04-22 15:07` **Tim McGlothin:** from Eric: Oracle gave us commands to start ASM one command at a time� � We usually use crsctl start has� � To fix the problem we ran� � [root]# /oracle/app/19.0.0/grid/bin/afdload
- `2026-04-22 16:38` **Hank Uhl:** fyi, im going to cancel tomorrow's meeting... steve and Javier are out
- `2026-04-22 16:48` **Javier Cede�o:** Tim McGlothin from Eric: Oracle gave us commands to start ASM one command at a time We usually use crsctl start has To fix the problem we ran [root]# /oracle/app/19.0.0/grid/bin/af
- `2026-04-22 16:48` **Javier Cede�o:** or not yet?
- `2026-04-22 16:48` **Tim McGlothin:** Eric says its good to go
- `2026-04-23 13:58` **Hank Uhl:** Tim � McGlothin �when you get online, can you please let me know the status of the 2 patch failures from last night? �i assume TOC contacted you since I see you logged into both se
- `2026-04-23 13:59` **Hank Uhl:** i see both were /boot again
- `2026-04-23 14:00` **Tim McGlothin:** theyre resolved... boot full
- `2026-04-23 14:00` **Hank Uhl:** im going to ask Berny to look at /boot on the rest of the Oracle servers
- `2026-04-23 14:01` **Tim McGlothin:** yeah, I'm going to take a fresh look and see if there is a work around that would allow us to extend it boot
- `2026-04-23 14:01` **Hank Uhl:** we should code an Ansible playbook that runs the 1st of every month to remove the old kernel and associated files from /boot... we've been kicking this can down the road too long
- `2026-04-23 14:01` **Hank Uhl:** oldest*

### Server Engineering Team - ALL
**103 messages** · 2026-03-24 → 2026-04-22

- `2026-04-13 13:26` **Joel Perez:** Nick is Patient Zero
- `2026-04-13 13:26` **David Bernier:** I think he is
- `2026-04-13 13:26` **Nicholas Hopson:** for sure haha!
- `2026-04-22 12:26` **Brooke Curtin-Johnson:** Hi guys, can you send any new servers you build over to Casey Bowser so he can set assignment groups in JSM? �Until we can come up with a better solution
- `2026-04-22 12:27` **Brooke Curtin-Johnson:** I was thinking about adding him to the email in the Ansible playbook but didn't do that yet
- `2026-04-22 12:28` **Tim McGlothin:** anybody having trouble logging into Ansible this morning? not getting the mfa prompt
- `2026-04-22 12:28` **Brooke Curtin-Johnson:** It just worked for me!
- `2026-04-22 12:29` **Tim McGlothin:** maybe my phone.. gonna reboot it
- `2026-04-22 12:29` **Brooke Curtin-Johnson:** That damn pixel�
- `2026-04-22 12:30` **Chris Montgomery:** no issues here
- `2026-04-22 12:30` **Tim McGlothin:** ive done un-pixely things to it and its protesting
- `2026-04-22 12:31` **Tim McGlothin:** that was it
- `2026-04-22 13:40` **Hank Uhl:** Stupid expensive AI foldable phone with 50x the horse power than what we sent to the moon and it still needs to be rebooted!
- `2026-04-22 13:43` **Tim McGlothin:** its probably mad because I have remote adb shell debugging on and let my AIs noodle around in there
- `2026-04-22 17:59` **Brooke Curtin-Johnson:** Anyone already looking at these?�
- `2026-04-22 18:04` **Steven Foxe:** I dealt with those same errors a couple days ago using the KB article. �Looks like they came back to probably need a ticket with Nutanix.
- `2026-04-22 18:04` **Brooke Curtin-Johnson:** On Prism Central as well?
- `2026-04-22 18:05` **Brooke Curtin-Johnson:** Was that Monday or last week?
- `2026-04-22 18:05` **Steven Foxe:** Monday I think
- `2026-04-22 18:05` **Brooke Curtin-Johnson:** Ya seems like Monday never cleared

### Unix Server | TOC Team Chat
**89 messages** · 2026-04-07 → 2026-04-23

- `2026-04-23 06:32` **Tim McGlothin:** Thanks... I'll take a look
- `2026-04-23 06:40` **Tim McGlothin:** I see the one for etl-pr-ora02, what's the other one?
- `2026-04-23 06:41` **Jonathan Jim�nez:** Patch DBA-SHD_PAIR2-PR (FULL REBOOT) �
- `2026-04-23 06:43` **Tim McGlothin:** Looks like shd-pr-ora07..had an issue with 01 this morning and the DBs didn't come up after.. I'll see what I can find
- `2026-04-23 06:44` **Jonathan Jim�nez:** Thanks !
- `2026-04-23 07:19` **Tim McGlothin:** shd-pr-ora07 and etl-pr-ora08 are patched and rebooted. �I did a check and I see grid11 up with ASM on both (these were a problem on shd-pr-ora01 earlier today but they seem ok her
- `2026-04-23 07:32` **Jonathan Jim�nez:** Perfect I can set the jobs to okay then right
- `2026-04-23 07:33` **Jonathan Jim�nez:** Perfect, thanks Tim for your help tonight
- `2026-04-23 07:35` **Tim McGlothin:** thanks! are there other patches running tonight? I'll check the boot FS on them so we dont hit that wall again
- `2026-04-23 07:36` **Jonathan Jim�nez:** This is what we got today
- `2026-04-23 07:36` **Tim McGlothin:** can you copy those host names? somce got cut off there
- `2026-04-23 07:39` **Tim McGlothin:** thanks.. checking these out
- `2026-04-23 07:41` **Jonathan Jim�nez:** Thanks
- `2026-04-23 07:41` **Tim McGlothin:** ok, should be safe till 10am as far as boot FS being full.. got the early morning ones cleaned up.. will address the others later�
- `2026-04-23 07:42` **Jonathan Jim�nez:** Great Tim I appreciate you checking on this�
- `2026-04-23 18:25` **Berny Vargas:** Hi Hank � Uhl , Tim � McGlothin �for the kernel clean up , would be better to add a step on the patching playbook , I think that's an option or do you prefer to do the clean up onc
- `2026-04-23 18:26` **Berny Vargas:** I think having a clean up step during patching sounds good ...
- `2026-04-23 18:27` **Tim McGlothin:** we were just talking about that... I think so but we may want to put some logic behind it so it only runs the cleanup if the boto fs is at a certain threshold...�
- `2026-04-23 18:29` **Berny Vargas:** Sounds good, I'll work on that an implement the logic during patching playbook
- `2026-04-23 18:47` **Tim McGlothin:** is there still an outlook calendar with the patching schedule? or has that moved?

## AI & Copilot Activity

### AI Nerds (377 msgs)
- `2026-04-21 17:38` **Aaron Smiley:** This is a new channel to me - thanks Zachary � MacDonald
- `2026-04-21 17:56` **Tim McGlothin:** well, I was writing that 'runway' tool to track token usage across agents and was fighting with gemini about how to track its usage (which is way more complicated than codex and cl
- `2026-04-22 13:34` **Aaron Smiley:** Anyone here using Hermes agent?
- `2026-04-22 13:40` **Tim McGlothin:** I am.. I have it running on the Mac and on my gb10 box... playing around with web UIs last night
- `2026-04-22 13:41` **Tim McGlothin:** got qwen 3.6 backing it, gonna side by side the other one with gemma4
- `2026-04-22 13:46` **Aaron Smiley:** Nice. Yeah I've tried both, seems like I had more luck with Gemma4 in my limited experience with it... but it's been a great harness. I would probably use it instead of Claude Code
- `2026-04-22 13:48` **Tim McGlothin:** gemma4 and qwen are both MoE, qwens got 3B active and Gemma 4B at a time.. I'm running Qwen at 35B A3b Q8, and Gemma 26B A4B Q8... eats about half the mem on both 128G boxes so ple
- `2026-04-22 13:52` **Aaron Smiley:** Do you like the a4b variant? I feel like there's no way you haven't done head to head with full-fat... I've just been using full fat because... it seemed too good to be true and I 
- `2026-04-22 13:53` **Tim McGlothin:** yeah I have the dense model in there too but kept running into a wall with it.. probably need to go back to that and re-download it ... seems everything is moving away from dense a
- `2026-04-22 13:54` **Tim McGlothin:** qwen doesn't even make a dense model anymore

### Claude initial setup (243 msgs)
- `2026-04-22 18:56` **Ben Hoisington:** https://support.claude.com/en/articles/12622703-deploy-claude-desktop-for-windows � It could potentially be packaged, depending on the audience. There is also a prerequisite that t
- `2026-04-22 18:56` **Andrew Skvorak:** I don't know who does and doesn't have admin privileges, but there are about 15 business folks on the list
- `2026-04-22 18:56` **Andrew Skvorak:** Right, the VMP requires admin to enable, too, right?
- `2026-04-22 18:56` **Ben Hoisington:** If it's not enabled by default. I can check on that.
- `2026-04-22 18:57` **Josh Andrews:** it's not
- `2026-04-22 18:58` **Andrew Skvorak:** Ben Hoisington https://support.claude.com/en/articles/12622703-deploy-claude-desktop-for-windows It could potentially be packaged, depending on the audience. There is also a prereq
- `2026-04-22 18:58` **Ben Hoisington:** We would probably put a wrapper around their installer, no different than we do for any other app.
- `2026-04-22 19:00` **Josh Andrews:** Let me send an e-mail about this to our Infra support teams and see if they have a preference. Packaging this wouldn't be a quick turnaround.�
- `2026-04-22 19:03` **Andrew Skvorak:** Yeah, I don't feel like we have time to package it if it takes more than a day or two, to be honest
- `2026-04-22 19:07` **Josh Andrews:** message sent

### GitHub Copilot Devs (190 msgs)
- `2026-04-23 14:31` **Joshua Jackson:** At least one other person asked that same question, though their status page has all green. Probably a brand new issue
- `2026-04-23 14:34` **Tim McGlothin:** big spike at downdetector.. not just us: https://downdetector.com/status/github/
- `2026-04-23 14:34` **Francisco Quarato:** Bobby Schleicher Jr is github down for anyone else? running into their error page when trying to create a PR +1 here
- `2026-04-23 14:34` **Carlos Alvarado:** Not able to log in
- `2026-04-23 14:35` **Tim McGlothin:** the angry unicorn of sadness
- `2026-04-23 14:35` **Bobby Schleicher Jr:** even their contact support page is down
- `2026-04-23 14:35` **Aaron Scifres:** looks like something just started
- `2026-04-23 14:35` **Tim McGlothin:** looks like they started playing around with Mythos at Microsoft
- `2026-04-23 14:42` **Mario Rodr�guez:** even the github status page is down
- `2026-04-23 14:55` **Carlos Alvarado:** seems to be back now

## Today's Activity (2026-04-23)

### 19:d60d29c1-76da-4ec7-806f-dcfd57597d1a_ (64 msgs)
- `2026-04-23 16:55` **Tim McGlothin:** ok... sanity check.. I may have a plan for /boot - add a new disk for boot, move the bootfs to it and point grub at it... When you get a sec, sanity check my pl
- `2026-04-23 17:18` **Hank Uhl:** conceptually, it seems sound, but honestly, i dont know that im onboard with modifying /boot on enterprise servers... we've had these discussions in the past an
- `2026-04-23 17:19` **Tim McGlothin:** it is a risk, but with a snapshot in place we can fail right back.. would have to be done during a maintenance window
- `2026-04-23 17:20` **Tim McGlothin:** plus the old sda1 partition we remain in tact so if it caused an issues down to road we could swap back to the old one
- `2026-04-23 17:20` **Hank Uhl:** i know... but the bigger picture is what i dont want to lose sight of... i dont want the servers to remain
- `2026-04-23 17:20` **Tim McGlothin:** true, but I also want to sleep through kernel updates
- `2026-04-23 17:20` **Hank Uhl:** and we can do that by cleaning up old kernels
- `2026-04-23 17:21` **Tim McGlothin:** maybe another approach. when we get these tickets we have management (David) approach the team that has that old server to schedule a rebuild... pressure from t
- `2026-04-23 17:21` **Tim McGlothin:** force the refresh on the problem children
- `2026-04-23 17:22` **Hank Uhl:** i'd be happier with that option... and one of the conditions when we upgraded to RHEL8 we had discussed... and Josh was onboard with this... is that we would up
- `2026-04-23 17:22` **Hank Uhl:** because i balked at the inplace upgrade to 8
- `2026-04-23 17:23` **Hank Uhl:** and we sold that messing with /boot was a technical limitation that was too risky to address with partitioning tools
- `2026-04-23 17:23` **Hank Uhl:** basically, what we sold is that we can do this stuff with home equipment, but did not want to risk the enterprise by trying it
- `2026-04-23 17:24` **Tim McGlothin:** right.. thats why I didn't approach it as 'move the partition with gpartd' which could work also.. this is cleaner, keep boot on its own drive and remaps grub
- `2026-04-23 17:25` **Tim McGlothin:** you could even have a second grub entry to points back to sda1�
- `2026-04-23 17:25` **Tim McGlothin:** for failback
- `2026-04-23 17:25` **Hank Uhl:** and i understand, but you know full well, that if we give the business an opening to workaround what we deemed to be too risky to keep going foward, they will t
- `2026-04-23 17:26` **Hank Uhl:** and we will be doing inplace upgrades to RHEL9
- `2026-04-23 17:26` **Hank Uhl:** the other concern i have with this, is i have to provide a ton of exceptions to CIS compliance because i dont know what i'll break
- `2026-04-23 17:26` **Tim McGlothin:** true. we'd have to preface the process - this is a problem server - emergency triage is to move boot but phase 2 must also be that the app owner prepares for a 
- `2026-04-23 17:28` **Tim McGlothin:** true. for now, maybe we stick to reducing # of kernels and collect data ... have mgmt. push on the app owners to prepare for new builds and not wait till 2029 w
- `2026-04-23 17:29` **Hank Uhl:** im fully onboard with pushing management to begin the process of working out how to get off RHEL8 into newer, probably RHEL10 by that time... so if you want to 
- `2026-04-23 17:29` **Tim McGlothin:** they've essentially moved the workload from the app owners re-deploying to waking us up in the middle of the night
- `2026-04-23 17:29` **Tim McGlothin:** about ready to
- `2026-04-23 17:29` **Hank Uhl:** you'll get no disagreement with me on that... which is partly why i resisted the RHEL8 inplace upgrade... but i couldn't get Josh or Carolyn to support me on th
- `2026-04-23 17:30` **Hank Uhl:** thankfully we only have to deal with this 4 times a year as opposed to 12
- `2026-04-23 17:30` **Tim McGlothin:** true that
- `2026-04-23 17:31` **Hank Uhl:** 4 weeks per year
- `2026-04-23 17:31` **Hank Uhl:** plus the occasional outlier i guess
- `2026-04-23 17:31` **Tim McGlothin:** some months get kernel updates on security months
- `2026-04-23 17:31` **Hank Uhl:** i think having berny put together an ansible playbook to clean this stuff up every month is a workable solution
- `2026-04-23 17:31` **Hank Uhl:** or whoever ends up doing it
- `2026-04-23 17:31` **Hank Uhl:** we jsut have to stop kicking the can down the road
- `2026-04-23 17:33` **Tim McGlothin:** we could lower the install limit in the configmgmt job also so it only keeps 1 old kernel instead�
- `2026-04-23 17:34` **Hank Uhl:** can we be sure that cleans up /boot too though? �it's really the ramdisk that hogs the space
- `2026-04-23 17:34` **Hank Uhl:** often there is a rescue version of it as well
- `2026-04-23 17:35` **Hank Uhl:** though maybe RPM cleans that up through upgrades
- `2026-04-23 17:35` **Hank Uhl:** guess i cant say ive watched it clsoely enough to know
- `2026-04-23 17:35` **Tim McGlothin:** I believe it does when it uninstalls the old one.. thats why the cleanup works�
- `2026-04-23 17:35` **Tim McGlothin:** /etc/dnf/dnf.conf under the [main] section: � � [main] � installonly_limit=2�
- `2026-04-23 17:36` **Tim McGlothin:** then once we clean them up dnf wont keep adding the 3rd one.. just like it doesn't add a 4th, 5th, etc now
- `2026-04-23 17:37` **Hank Uhl:** That makes sense
- `2026-04-23 17:42` **Tim McGlothin:** you know what.. I think we already have a playbook that sets the # of kernels.. probably just need to schedule it
- `2026-04-23 17:43` **Tim McGlothin:** UTILITY_Set_number_of_kernels.yml
- `2026-04-23 17:43` **Tim McGlothin:** � � ---� -� name: � Set � the � number � of � kernels � to � keep � and � clean � up � old � entries hosts: � all become: �true gather_facts: �true tasks: �� -�
- `2026-04-23 17:44` **Tim McGlothin:** need to put in the dnf file as well as yum
- `2026-04-23 17:44` **Tim McGlothin:** could break out the yum.conf/dnf.conf into a play that runs with nightly configmgmt
- `2026-04-23 17:45` **Hank Uhl:** im good with that
- `2026-04-23 17:46` **Hank Uhl:** install limit i assume means the current and 1 older one
- `2026-04-23 17:46` **Tim McGlothin:** right
- `2026-04-23 17:46` **Tim McGlothin:** I let berny know about that playbook and we may just need to schedule it
- `2026-04-23 17:47` **Hank Uhl:** i think the problem is 2 is still too many for the upgraded servers... once the upgrade is done, we will have to lower it to only the active kernel
- `2026-04-23 17:47` **Hank Uhl:** because temporarily there will be 3
- `2026-04-23 17:48` **Tim McGlothin:** hrm.. good point.. could roll some logic into the update playbook, detect size of bootfs, run cleanup prior to patch
- `2026-04-23 17:48` **Hank Uhl:** or just make it part of the daily, how often do we ever have to roll back
- `2026-04-23 17:48` **Hank Uhl:** really oracle servers are the only ones that have ever required it.. maybe MQ
- `2026-04-23 17:49` **Tim McGlothin:** we never do. if we did we could easily roll back the dnf transaction and exclude the kernel
- `2026-04-23 17:49` **Hank Uhl:** yup, agreed
- `2026-04-23 17:51` **Tim McGlothin:** or.. another patch pattern - first step - snapshot the server... if the patch fails, call a playbook that restores that VM to the snapshot and log the ticket fo
- `2026-04-23 17:51` **Tim McGlothin:** fix during business hours and reschedule the patch
- `2026-04-23 17:52` **Hank Uhl:** im good with that idea as well
- `2026-04-23 17:52` **Tim McGlothin:** patch succeds- remove the snapshot so we dont swamp the storage containers with them
- `2026-04-23 17:54` **Hank Uhl:** i canceled tomorrow's meeting, but we could always use the Monday meeting that i always cancel to have this discussion if you'd like... or it wait until our nex
- `2026-04-23 18:03` **Hank Uhl:** i meant i canceled today's meeting, of course

### Unix Server | TOC Team Chat (24 msgs)
- `2026-04-23 06:30` **Tim McGlothin:** Hi TOC, what's up
- `2026-04-23 06:31` **Jonathan Jim�nez:** Hello Tim, good morning, I got a patch in PROD
- `2026-04-23 06:31` **Jonathan Jim�nez:** https://llbean.atlassian.net/browse/ITS-10596
- `2026-04-23 06:32` **Jonathan Jim�nez:** There are 2 of them Im sending the information of the second one through email as well.
- `2026-04-23 06:32` **Tim McGlothin:** Thanks... I'll take a look
- `2026-04-23 06:40` **Tim McGlothin:** I see the one for etl-pr-ora02, what's the other one?
- `2026-04-23 06:41` **Jonathan Jim�nez:** Patch DBA-SHD_PAIR2-PR (FULL REBOOT) �
- `2026-04-23 06:43` **Tim McGlothin:** Looks like shd-pr-ora07..had an issue with 01 this morning and the DBs didn't come up after.. I'll see what I can find
- `2026-04-23 06:44` **Jonathan Jim�nez:** Thanks !
- `2026-04-23 07:19` **Tim McGlothin:** shd-pr-ora07 and etl-pr-ora08 are patched and rebooted. �I did a check and I see grid11 up with ASM on both (these were a problem on shd-pr-ora01 earlier today 
- `2026-04-23 07:32` **Jonathan Jim�nez:** Perfect I can set the jobs to okay then right
- `2026-04-23 07:33` **Jonathan Jim�nez:** Perfect, thanks Tim for your help tonight
- `2026-04-23 07:35` **Tim McGlothin:** thanks! are there other patches running tonight? I'll check the boot FS on them so we dont hit that wall again
- `2026-04-23 07:36` **Jonathan Jim�nez:** This is what we got today
- `2026-04-23 07:36` **Tim McGlothin:** can you copy those host names? somce got cut off there
- `2026-04-23 07:39` **Tim McGlothin:** thanks.. checking these out
- `2026-04-23 07:41` **Jonathan Jim�nez:** Thanks
- `2026-04-23 07:41` **Tim McGlothin:** ok, should be safe till 10am as far as boot FS being full.. got the early morning ones cleaned up.. will address the others later�
- `2026-04-23 07:42` **Jonathan Jim�nez:** Great Tim I appreciate you checking on this�
- `2026-04-23 18:25` **Berny Vargas:** Hi Hank � Uhl , Tim � McGlothin �for the kernel clean up , would be better to add a step on the patching playbook , I think that's an option or do you prefer to
- `2026-04-23 18:26` **Berny Vargas:** I think having a clean up step during patching sounds good ...
- `2026-04-23 18:27` **Tim McGlothin:** we were just talking about that... I think so but we may want to put some logic behind it so it only runs the cleanup if the boto fs is at a certain threshold..
- `2026-04-23 18:29` **Berny Vargas:** Sounds good, I'll work on that an implement the logic during patching playbook
- `2026-04-23 18:47` **Tim McGlothin:** is there still an outlook calendar with the patching schedule? or has that moved?

### GitHub Copilot Devs (11 msgs)
- `2026-04-23 14:31` **Bobby Schleicher Jr:** is github down for anyone else? running into their error page when trying to create a PR
- `2026-04-23 14:31` **Joshua Jackson:** At least one other person asked that same question, though their status page has all green. Probably a brand new issue
- `2026-04-23 14:34` **Tim McGlothin:** big spike at downdetector.. not just us: https://downdetector.com/status/github/
- `2026-04-23 14:34` **Francisco Quarato:** Bobby Schleicher Jr is github down for anyone else? running into their error page when trying to create a PR +1 here
- `2026-04-23 14:34` **Carlos Alvarado:** Not able to log in
- `2026-04-23 14:35` **Tim McGlothin:** the angry unicorn of sadness
- `2026-04-23 14:35` **Bobby Schleicher Jr:** even their contact support page is down
- `2026-04-23 14:35` **Aaron Scifres:** looks like something just started
- `2026-04-23 14:35` **Tim McGlothin:** looks like they started playing around with Mythos at Microsoft
- `2026-04-23 14:42` **Mario Rodr�guez:** even the github status page is down
- `2026-04-23 14:55` **Carlos Alvarado:** seems to be back now

### 19:6fa035f3-c521-41be-b080-d1f32df74a83_ (9 msgs)
- `2026-04-23 18:20` **Tim McGlothin:** some pre-llb history
- `2026-04-23 18:20` **Tim McGlothin:** some pre-llb history
- `2026-04-23 18:21` **David Bernier:** won another note - when you get a minute, please take the Annual Required Safety Training in Workday - I know I know.....
- `2026-04-23 18:21` **Tim McGlothin:** the AWS stack I built for APF
- `2026-04-23 18:22` **David Bernier:** thanks buddy
- `2026-04-23 18:22` **Tim McGlothin:** ahh, I'll do it now before change
- `2026-04-23 18:22` **David Bernier:** Tim McGlothin the AWS stack I built for APF 📄 I just fell off my chair trying to follow....LOL
- `2026-04-23 18:22` **Tim McGlothin:** thats the simplified version
- `2026-04-23 18:31` **Tim McGlothin:** David Bernier won another note - when you get a minute, please take the Annual Required Safety Training in Workday - I know I know..... done!

### IS Connect Hub (8 msgs)
- `2026-04-23 14:37` **Naga Pradeep Koganti:** anyone having issues with git ?
- `2026-04-23 14:37` **Jim Greene:** Github is down.
- `2026-04-23 14:37` **Naga Pradeep Koganti:** " No server is currently available to service your request. Sorry about that. Please try refreshing and contact us if the problem persists. "
- `2026-04-23 14:37` **Tim McGlothin:** Not just us https://downdetector.com/status/github/
- `2026-04-23 14:44` **Naga Pradeep Koganti:** looks like its up now�
- `2026-04-23 14:56` **Joshua Jackson:** Is it possible to get Confluence to not destroy my page titles with what their AI thinks I should use? It's pretty frustrating to have to retype them every time
- `2026-04-23 15:05` **Tatiana Gomez:** Joshua Jackson Is it possible to get Confluence to not destroy my page titles with what their AI thinks I should use? It's pretty frustrating to have to retype 
- `2026-04-23 15:49` **Joshua Jackson:** It only did it the first time - it changed the title when I clicked the Publish button, so while that modal was up it gave a little popup at the bottom left say

### Unix Server and Storage Team (7 msgs)
- `2026-04-23 13:58` **Hank Uhl:** Tim � McGlothin �when you get online, can you please let me know the status of the 2 patch failures from last night? �i assume TOC contacted you since I see you
- `2026-04-23 13:59` **Hank Uhl:** i see both were /boot again
- `2026-04-23 14:00` **Tim McGlothin:** theyre resolved... boot full
- `2026-04-23 14:00` **Hank Uhl:** im going to ask Berny to look at /boot on the rest of the Oracle servers
- `2026-04-23 14:01` **Tim McGlothin:** yeah, I'm going to take a fresh look and see if there is a work around that would allow us to extend it boot
- `2026-04-23 14:01` **Hank Uhl:** we should code an Ansible playbook that runs the 1st of every month to remove the old kernel and associated files from /boot... we've been kicking this can down
- `2026-04-23 14:01` **Hank Uhl:** oldest*

### 19:wQX_vY6BHOfrbtFwmG6l1PhcJO8-U3dSSfPiZ (5 msgs)
- `2026-04-23 14:25` **GitHub Enterprise:** Commit 51cf79d Commit 51cf79d
- `2026-04-23 14:45` **GitHub Enterprise:** Commit eba0239 Commit eba0239
- `2026-04-23 14:46` **GitHub Enterprise:** Pull request 721 Pull request 721
- `2026-04-23 15:13` **GitHub Enterprise:** Commit 45933e6 Commit 45933e6
- `2026-04-23 15:13` **GitHub Enterprise:** Pull request 721 Pull request 721

### 19:9f2de76c-9672-4459-ae63-ebecb5b90044_ (5 msgs)
- `2026-04-23 17:46` **Tim McGlothin:** Hey Berny! FYI - I think there is a playbook already ... looks like we might just need to schedule it
- `2026-04-23 17:46` **Tim McGlothin:** UTILITY_Set_number_of_kernels.yml
- `2026-04-23 17:48` **Berny Vargas:** Ohhh really, great Tim, that saves me some time, I'll take a look!!�
- `2026-04-23 17:49` **Tim McGlothin:** didn't want ya to have to re-invent the wheel
- `2026-04-23 17:50` **Berny Vargas:** Much appreciated

### 48:mentions (2 msgs)
- `2026-04-23 13:58` **<Undefined> <Undefined>:** Tim McGlothin when you get online, can you please let me know the status of the 2 patch failures from last night? i assume TOC contacted you since I see you log
- `2026-04-23 18:25` **<Undefined> <Undefined>:** Hi Hank Uhl, Tim McGlothin for the kernel clean up , would be better to add a step on the patching playbook , I think that's an option or do you prefer to do th

### 48:notifications (2 msgs)
- `2026-04-23 13:58` **<Undefined> <Undefined>:** Tim McGlothin when you get online, can you please let me know the status of the 2 patch failures from last night? i assume TOC contacted you since I see you log
- `2026-04-23 18:25` **<Undefined> <Undefined>:** Hi Hank Uhl, Tim McGlothin for the kernel clean up , would be better to add a step on the patching playbook , I think that's an option or do you prefer to do th

### 48:drafts (2 msgs)
- `2026-04-23 18:20` **<Undefined> <Undefined>:** some pre-llb history
- `2026-04-23 18:26` **<Undefined> <Undefined>:** we were just talking about that...�

### 19:013f4eb6-c04b-434c-a8f6-80462c3b2efe_ (1 msgs)
- `2026-04-23 08:22` **Tim McGlothin:** Here's the AWS architecture I put together for the APF site I mentioned
