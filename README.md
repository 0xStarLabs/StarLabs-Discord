# Discord Automation Bot 2.0 🤖

A powerful and flexible Discord automation tool with multiple features and parallel processing capabilities.

## 🌟 Features
- ✨ Multi-threaded processing
- 🔄 Automatic retries with configurable attempts
- 🔐 Proxy support
- 📝 Excel-based account management
- 🎭 AI Chat integration with GPT-4
- 🔒 Secure file handling with thread-safe operations
- 📊 Detailed logging system

### 🎯 Available Actions:
- AI Chatter
- Server Inviter
- Button Interaction
- Reaction Management
- Profile Customization:
  - Name Change
  - Username Update
  - Password Update
  - Profile Picture Change
- Message Management (Chat + insta deleting)
- Token Verification
- Server Management:
  - Leave Guild
  - Server List
  - Guild Presence Check

## 📋 Requirements
- Python 3.11.6 or higher
- Excel file with Discord accounts
- Valid Discord tokens
- (Optional) Proxies
- OpenAI API key for AI Chat features

## 🚀 Installation

1. Clone the repository:
```bash
git clone https://github.com/0xStarLabs/StarLabs-Discord.git
cd StarLabs-Discord
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure your settings in `config.yaml`

## 📁 Project Structure
```
StarLabs-Discord/
├── data/
│   ├── accounts.xlsx     # Discord accounts data
│   ├── messages/         # Message templates
│   └── pictures/         # Profile pictures
├── src/
│   └── utils/
│       ├── constants.py  # Configuration constants
│       ├── reader.py     # File handling utilities
│       └── ...
└── config.yaml          # Main configuration file
```


## 📝 Configuration

### 1. accounts.xlsx Structure
| Column         | Example   | Description |
|---------------|-----------|-------------|
| DISCORD_TOKEN | token1    | Discord account token |
| PROXY         | proxy1    | Proxy address (optional) |
| USERNAME      | user1     | Account username |
| STATUS        | VALID     | Account status |
| PASSWORD      | pass1     | Current password |
| NEW_PASSWORD  | newpass1  | New password for update |
| NEW_NAME      | name1     | New display name |
| NEW_USERNAME  | username1 | New username |
| MESSAGES_FILE | messages1 | Custom messages file |


### 2. config.yaml Settings
```yaml
SETTINGS:
  THREADS: 1                      # Number of parallel threads
  ATTEMPTS: 5                     # Retry attempts for failed actions
  SHUFFLE_ACCOUNTS: true          # Randomize account processing order
  PAUSE_BETWEEN_ATTEMPTS: [1, 2]  # Random pause between retries
  PAUSE_BETWEEN_ACCOUNTS: [1, 2]  # Random pause between accounts
```

### 3. AI Chatter Configuration
```yaml
AI_CHATTER:
  ANSWER_PERCENTAGE: 50           # Probability of responding to messages
  REPLY_PERCENTAGE: 50           # Percentage of replies vs new messages
  MESSAGES_TO_SEND_PER_ACCOUNT: [3, 5]
```

## 🎮 Usage
1. Prepare your files:
   - Fill `accounts.xlsx` with tokens and account data
   - Configure `config.yaml` with desired settings
   - Add message templates to `data/messages/`
   - Add profile pictures to `data/pictures/`

2. Run the bot:
```bash
python main.py
```

## 🤝 Support
- Create an issue for bug reports or feature requests
- Join our community for discussions and updates

## 📜 License

MIT License

Copyright (c) 2024 [Your Name]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

⚠️ Disclaimer
This tool is for educational purposes only. Use at your own risk and in accordance with Discord's Terms of Service.