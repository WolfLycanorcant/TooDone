# TooDone - Productivity Application

![TooDone Logo](graphics/icon/app_icon/produce.png)

## Overview

TooDone is a comprehensive productivity application designed to help you manage tasks, track time, and boost your efficiency. Built with Python and featuring a user-friendly interface, TooDone combines task management with time tracking to help you stay organized and productive.

## Features

- 🎯 **Task Management**: Create, organize, and prioritize your tasks
- ⏱️ **Time Tracking**: Track time spent on tasks and projects
- 📅 **Calendar Integration**: Sync with your calendar for better scheduling
- 🎨 **Customizable Interface**: Choose from different themes and layouts
- 📊 **Productivity Analytics**: Get insights into your work patterns
- 🛎️ **Reminders & Notifications**: Never miss important deadlines
- 🔄 **Cross-Platform**: Works on Windows, macOS, and Linux

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git (for cloning the repository)

### Step 1: Clone the Repository

```bash
git clone https://github.com/WolfLycanorcant/TooDone.git
cd TooDone
```

### Step 2: Set Up Virtual Environment (Recommended)

```bash
# On Windows
python -m venv venv
.\venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

!. Copy the example environment file:
   ```bash
   copy .env.example and rename it the shorter name of .env
   ```
1. Edit the `.env` file and add your API keys and configuration. Like this:
# API Keys
GROQ_API_KEY=your_groq_api_key
TODOIST_API_TOKEN=your_todoist_token

# Application Settings
GROQ_MODEL_NAME=llama-3.3-70b-versatile
BACKGROUND_IMAGE_PATH=graphics/background/mountain-surrounded-with-fog.jpg
MINIMIZE_TEXT_COLOR=0.0,0.0,0.0,1
      or
2. click on the setup button in the app to add the api keys

## Usage

### Running the Application

```bash
#Make sure the environment is activated by 
source venv/bin/activate
#The prompt will change to have (venv) at the beginning of the line. Then run
python Productivity.py
```

Or you can double click the exe file labeled Productivity_App_Start.exe

```bash
.\Productivity_App_Start.exe
```

### Basic Commands

- `Ctrl+N`: Create a new task
- `Ctrl+F`: Search tasks
- `Ctrl+E`: Edit selected task
- `Delete`: Delete selected task
- `F1`: Show keyboard shortcuts

## Configuration

### Environment Variables

Edit the `.env` file to configure application settings:

```ini
# API Keys
GROQ_API_KEY=your_groq_api_key
TODOIST_API_TOKEN=your_todoist_token

# Application Settings
GROQ_MODEL_NAME=llama-3.3-70b-versatile
BACKGROUND_IMAGE_PATH=graphics/background/mountain-surrounded-with-fog.jpg
MINIMIZE_TEXT_COLOR=0.0,0.0,0.0,1
```

## Directory Structure

```
TooDone/
├── .env.example           # Example environment configuration
├── .gitignore            # Git ignore rules
├── LICENSE               # License file
├── Productivity.py       # Main application file
├── Productivity_App_Start.exe  # Windows executable
├── README.md             # This file
├── alarm/                # Alarm functionality
├── broadcasts/           # System broadcasts and notifications
├── Calendar Converter/   # Calendar integration tools
├── graphics/             # Application assets and icons
```

## Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Support

For support, please open an issue in the GitHub repository.

## Acknowledgements

- Built with Python and various open-source libraries
- Icons from [Font Awesome](https://fontawesome.com/)
- Background images from various free sources

---

<div align="center">
  Made with ❤️ by Your Name
</div>
