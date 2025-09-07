# ⚡ 1-Day Intensive Study Plan for Chatroom Project

This plan condenses the 3-day roadmap into a single intensive day of
learning.\
Goal: **Understand all the essentials** for your chatroom project ---
networking, concurrency, encryption, GUI, file sharing, and polish
features.

------------------------------------------------------------------------

## 🌅 Morning (3--4 hours): Networking Basics + Client-Server

**Focus:** How two computers communicate.

-   Learn:
    -   **IP addresses** and **ports** --- identify computers and
        applications.
    -   **TCP vs UDP** --- why TCP is used for chat (reliable delivery).
    -   **Sockets** --- the doorway for communication.
    -   **Client-server model** --- server waits, clients connect.
-   Practice with AI:
    -   Explain what a socket is in your own words.
    -   Write pseudocode for a server that accepts 2 clients.
    -   Simulate: what happens when 2 clients send a message to the
        server?
-   Map to project:
    -   Your chatroom server opens a socket.
    -   Clients connect via IP+port.
    -   Messages (JSON) flow over TCP.

✅ Outcome: You can explain how your server and clients connect and
exchange data.

------------------------------------------------------------------------

## ☀️ Midday (3--4 hours): Concurrency + Encryption

**Focus:** How to support many users and keep chats private.

-   Learn:
    -   **Concurrency** with threads --- one thread per client.
    -   **Symmetric encryption (AES)** vs **Asymmetric encryption
        (RSA)**.
    -   **Handshake process**: Client generates AES key → encrypts with
        RSA → server decrypts → both sides share AES.
-   Practice with AI:
    -   Draw a flow of "Client sends AES key to server using RSA."
    -   Write pseudocode to encrypt/decrypt a message with AES.
    -   Explain why not all messages are sent with RSA.
-   Map to project:
    -   Threads handle multiple clients at once.
    -   AES encrypts all chat messages.
    -   RSA handshake secures the AES key.

✅ Outcome: You can explain how multiple users chat securely at the same
time.

------------------------------------------------------------------------

## 🌇 Afternoon (3--4 hours): GUI + File Sharing + Polish

**Focus:** How users interact with the chatroom.

-   Learn:
    -   **GUI event loops** --- keep app responsive.
    -   **File transfer with chunks** --- accept/reject, progress bar.
    -   **Polish features**: emojis, typing indicators, read receipts.
-   Practice with AI:
    -   Sketch a GUI layout with message window, input box, user list,
        emoji & file buttons.
    -   Simulate file transfer flow: init → accept → send chunks →
        complete.
    -   Role-play: You're the client, AI is the server. Exchange JSON
        messages.
-   Map to project:
    -   PyQt GUI for chatroom window.
    -   File sharing implemented with chunking and progress.
    -   Polish features make your app stand out.

✅ Outcome: You understand how the chatroom looks, feels, and works for
the user.

------------------------------------------------------------------------

## 🌙 Evening (2 hours): Review + Self-Explanation

**Focus:** Reinforce what you learned.

-   Summarize in your own words:
    1.  How messages travel between computers.
    2.  How multiple users chat at once.
    3.  How encryption keeps messages private.
    4.  How GUI and file sharing make the app user-friendly.
-   Teach it back to AI (if you can explain clearly, you've got it).

✅ Outcome: Solid big-picture understanding, ready to start building.

------------------------------------------------------------------------

# 🎯 Final Result

By the end of this 1-day intensive plan, you will: - Understand
**networking, concurrency, encryption, GUI, file sharing, and polish
features**.\
- Be able to explain each part of your project in simple terms.\
- Feel confident to begin coding without getting lost.
