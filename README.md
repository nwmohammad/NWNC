# NWNC

NWNC (NW Network Chat) is a Python-based local network messaging tool that allows users to chat over a TCP socket server through a desktop interface. It supports client/server communication, message handling, and a simple GUI for managing connections.

## Overview

NWNC is designed for local network communication in environments where users need quick and reliable messaging between machines on the same network. The application combines a lightweight socket-based backend with a desktop frontend to provide a practical chat experience without requiring external cloud services.

## Features

- Real-time local network messaging
- TCP socket-based client/server communication
- Desktop GUI for connection management
- Simple and lightweight architecture
- Suitable for internal or LAN-based communication
- Easy to extend for custom messaging features

## How it Works

The project uses a Python server to listen for incoming connections and a client application to communicate with that server. Messages are exchanged over the local network, and the desktop interface helps users manage connections and conversations in a user-friendly way.

## Project Goals

NWNC aims to provide a minimal but useful messaging solution for local-area communication, especially in scenarios where users want fast collaboration without relying on internet-based chat platforms.

## Requirements

- Python 3.x
- TCP networking support
- Desktop environment compatible with Python GUI libraries

## Getting Started

1. Clone the repository:
   ```bash
   git clone https://github.com/nwmohammad/NWNC.git
   cd NWNC
   ```
2. Install the required dependencies if needed.
3. Run the application from the project entry points.
4. Connect the client to the local server and start messaging.

## Usage

- Start the server and make it available on your local network.
- Launch the desktop client.
- Connect to the server using the appropriate address and port.
- Send and receive messages in the chat interface.

## Architecture

NWNC is structured as a lightweight local messaging application with:

- A server component for handling inbound connections and message routing
- A client component for sending and receiving messages
- A GUI layer for user interaction and connection control

## Contact & Community

You can connect with the project community and stay updated through the following channels:

- Discord: https://discord.gg/YOUR_DISCORD_INVITE
- Telegram: https://t.me/YOUR_TELEGRAM_USERNAME
- Bale: https://ble.ir/YOUR_BALE_ID

## License

This project is licensed under the MIT License. See the LICENSE file for more information.

## Contributing

Contributions are welcome. If you would like to improve the project, feel free to open an issue or submit a pull request.

## Disclaimer

NWNC is intended for local network communication and should be used responsibly within trusted environments.
