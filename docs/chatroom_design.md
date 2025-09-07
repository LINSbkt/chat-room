# Chatroom Project Roadmap & Tech Stack

## 📌 Tech Stack Recommendation

Since you want both **fast prototyping** and a **user-friendly GUI**, I
recommend **Python + PyQt6**:

-   **Language**: Python 3.10+ (simple networking, threading, crypto
    libraries).
-   **Networking**: `socket` (TCP), `threading` or `asyncio` (but
    threading is easier).
-   **Crypto**: `cryptography` (`Fernet` is AES-based, or AES-GCM with
    `hazmat` APIs).
-   **GUI**: PyQt6 (modern, polished, cross-platform; Tkinter looks
    old-school).
-   **File Handling**: Python built-ins (`open`, `os`, `pathlib`) with
    chunked reads/writes.
-   **Data Format**: JSON for messages (easy to debug & serialize).
-   **Testing**: `pytest` for unit tests; manual stress testing with
    multiple clients.
-   **Packaging**: `requirements.txt` + GitHub repo.

📌 Why not Java or Node?\
- **Java**: good for concurrency, but GUI (Swing/JavaFX) is clunky and
dev speed is slower.\
- **Node.js/Electron**: flashy GUI, but heavy, and crypto+socket work is
trickier.\
- **Python + PyQt** hits the sweet spot: simple sockets, strong crypto
library, polished UI in 1 month.

------------------------------------------------------------------------

## 📅 Project Timeline (1 month plan)

### **Week 1: Foundations (Server, Client, Basic Messaging)**

🎯 Goal: working encrypted multi-client chat with text messages.\
- Day 1--2: Set up GitHub repo, implement multi-client server\
- Day 3--4: Implement client with console-based chat\
- Day 5--6: Add AES encryption (RSA/DH handshake)\
- Day 7: Add timestamps & message routing

✅ Deliverable: Console-based encrypted chatroom with auth, messaging,
timestamps

------------------------------------------------------------------------

### **Week 2: GUI + User Management**

🎯 Goal: replace console with polished GUI.\
- Day 8--9: Design PyQt6 GUI layout\
- Day 10--11: Integrate GUI with networking thread\
- Day 12: Add active user list auto-refresh\
- Day 13--14: Add emoji picker (shortcodes + Unicode)

✅ Deliverable: GUI client with global/private messaging, emoji, user
list

------------------------------------------------------------------------

### **Week 3: File Sharing + Concurrency Hardening**

🎯 Goal: robust file transfer system with encryption.\
- Day 15--16: Implement file transfer protocol (init, chunks,
accept/reject)\
- Day 17--18: Add GUI dialogs for file transfers + progress bar\
- Day 19: Test large files & concurrent transfers\
- Day 20--21: Improve server concurrency handling

✅ Deliverable: Chat with GUI + reliable file transfer + stable
concurrency

------------------------------------------------------------------------

### **Week 4: Polish, Testing, and Report**

🎯 Goal: add polish features + finalize documentation & demo.\
- Day 22--23: Add typing indicators\
- Day 24--25: Add read receipts (sent/delivered/seen)\
- Day 26: Implement optional message persistence\
- Day 27: Comprehensive testing\
- Day 28: Write project report\
- Day 29: Record demo video\
- Day 30: Polish README, finalize GitHub submission

✅ Deliverable: Encrypted chat app with all rubric features + extras

------------------------------------------------------------------------

## 🏆 Final Feature Prioritization

**Must-Have (graded heavily):** - ✅ Authentication & username
uniqueness\
- ✅ Global & private messages\
- ✅ GUI (PyQt6)\
- ✅ Active user list\
- ✅ File transfer with accept/reject\
- ✅ Emoji picker & shortcodes\
- ✅ Timestamps\
- ✅ AES encryption with RSA handshake\
- ✅ Graceful exit & error handling\
- ✅ Concurrency (multi-clients)

**Nice-to-Have (to stand out):** - ✨ Typing indicators\
- ✨ Read receipts\
- ✨ File transfer progress bar\
- ✨ Message history\
- ✨ Theme settings

------------------------------------------------------------------------

⚡ With this roadmap:\
- By **end of Week 2**, you'll already have a strong submission-ready
chat app.\
- By **Week 4**, you'll have the *best chatroom in the class* --- full
features + polish.
