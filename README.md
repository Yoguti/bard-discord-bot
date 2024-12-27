# Bumbling Bard 🎶

A musical companion for Discord, bringing the spirit of a tavern bard to your voice channels!

## Overview

Bumbling Bard is a Discord bot designed to enhance your server with a variety of entertainment and utility features. It allows users to:

*   **Play music:** Search for and play songs from YouTube and Spotify directly into voice channels.
*   **Manage Playlists:** Create, save, and manage song queues.
*   **Dice Rolling:** Roll various types of dice for tabletop-style games or random outcomes.
*   **NPC Generation:** Generate random non-player characters with names, races, and basic traits.
*   **Loot Tables:** Generate loot based on specified rarity or a general table.
*   **Interactive Menus:** Use engaging interactive menus for certain commands, enhancing the user experience.

## Features

Here's a taste of what Bumbling Bard can do:

*   **Music Magic:**
    *   Use `b!sing <song name/URL>` to play songs from YouTube or Spotify.
    *   Manage playback using queueing, pausing, and skipping commands.
      
    ![image](https://github.com/user-attachments/assets/35e6d51e-293d-46c0-a514-29b62a380b64)

*   **Tavern Time:**
    *   Use `b!tavern` to access an interactive menu for exploring taverns, getting drinks, and interacting with your surroundings.
      
     ![image](https://github.com/user-attachments/assets/b19b176c-68c1-4cd0-a400-8d1adc3b8250)


*   **Dice Rolls:**
    *   Use `b!roll <dice notation>` (e.g., `b!roll 1d20`, `b!roll 2d6+2`) to roll various dice combinations.
      
    ![image](https://github.com/user-attachments/assets/bec1e5c4-0e47-4f56-acf5-825a2c1b9bff)


*   **NPC Generator:**
    *   Use `b!npc` to generate a random non-player character.
      
    ![image](https://github.com/user-attachments/assets/9533c783-4057-4c63-9d50-7630129072b5)


*   **Loot Generation:**
    *   Use `b!loot` to generate a random loot table.
      
     ![image](https://github.com/user-attachments/assets/691ee4a9-42bb-4408-aba2-86e582417910)


## Getting Started

Follow these instructions to get Bumbling Bard running on your Discord server:

### Prerequisites

*   **Python 3.7 or higher:** Make sure you have a compatible version of Python installed.
*   **Discord Bot Token:** Create a Discord bot application on the Discord Developer Portal and obtain its bot token.
*  **Spotify API Credentials:** Create a Spotify developer application and obtain its Client ID and Client Secret.

### Cloning the Repository

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Yoguti/hosting-bardbot.git
    ```
2.  **Navigate to the project directory:**
    ```bash
    cd hosting-bardbot
    ```

### Installation

1.  **Create a virtual environment (optional, but recommended):**
    ```bash
    python3 -m venv venv
    ```
2.  **Activate the virtual environment:**
    *   **On Linux/macOS:**
        ```bash
        source venv/bin/activate
        ```
    *   **On Windows:**
        ```bash
        venv\Scripts\activate
        ```
3.  **Install the requirements:**
    ```bash
    pip install -r requirements.txt
    ```

### Configuration

1.  **Create a `.env` file:** Create a `.env` file in the project root.
2.  **Add your secrets:** Add the following content to the `.env` file, replacing the placeholders with your actual tokens and credentials:

    ```env
    DISCORD_TOKEN=YOUR_DISCORD_BOT_TOKEN
    SPOTIFY_CLIENT_ID=YOUR_SPOTIFY_CLIENT_ID
    SPOTIFY_CLIENT_SECRET=YOUR_SPOTIFY_CLIENT_SECRET
    ```

### Running the Bot

1.  **Run the bot:**
    ```bash
    python bard.py
    ```

    The bot should now be online and ready to receive commands in your Discord server.

## Contributing

Contributions to this project are welcome! If you have any feature requests or bug reports, please submit them as issues or pull requests.

## License

This project is licensed under the MIT License. You are free to use, copy, modify, and distribute this software as long as you include the original copyright notice and license in any copies. For more details, see the [LICENSE](LICENSE) file.


