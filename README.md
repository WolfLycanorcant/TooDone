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

# On Windows
#To set up the environment run

```bash
python -m venv venv
```

#To enter the environment run

```bash
.\venv\Scripts\activate
```

### Step 3: Create a .env file

make a copy of the example environment file, but change the name of the file:

copy .env.example and rename it the shorter name of .env


You can choose to edit the `.env` file and add your API keys and configuration. Like this:

```bash
GROQ_API_KEY=your_groq_api_key #paste over
TODOIST_API_TOKEN=your_todoist_token #paste over

GROQ_MODEL_NAME=llama-3.3-70b-versatile 
BACKGROUND_IMAGE_PATH=graphics/background/mountain-surrounded-with-fog.jpg 
MINIMIZE_TEXT_COLOR=0.0,0.0,0.0,1
```


# On macOS/Linux

Set up the environment

```bash
python3 -m venv venv
```

To enter the environment run

```bash
source venv/bin/activate
```

If changing an api key is required after setup there are premade app fields you can click in the setup page by using the setup page button on the lower right in the app and paste your api keys

### Running the Application
Again, make sure the environment is activated by

```bash
source venv/bin/activate
```

#The prompt will change to have (venv) at the beginning of the line. Then run

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

## Usage

**Command Line:** `python Productivity.py`

Or you can double click the exe file labeled Productivity_App_Start.exe, after environment confiuration using defaults. If it doesnt work

**Command Line:** `python Productivity.py`

> 🔘 **Launch:** `./Productivity_App_Start.exe`


### Basic Hot key shortcut Commands

🆕  Ctrl + N  →  Create a new task  
🔍  Ctrl + F  →  Search tasks  
✏️  Ctrl + E  →  Edit selected task  
🗑️  Delete    →  Delete selected task  
❓  F1         →  Show keyboard shortcuts


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
  Made with 🔥 by WolfLycanorcant
</div>
