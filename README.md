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

### Step 3: Create an .env file

make a copy of the example environment file, but change the name of the file:

make a copy of .env.example and rename it the shorter name of .env

You can choose to edit the `.env` file that was a copy of .env.example and paste in your API keys. Like this:

```bash
GROQ_API_KEY=your_groq_api_key #paste over
TODOIST_API_TOKEN=your_todoist_token #paste over

GROQ_MODEL_NAME=llama-3.3-70b-versatile 
BACKGROUND_IMAGE_PATH=graphics/background/mountain-surrounded-with-fog.jpg 
MINIMIZE_TEXT_COLOR=0.0,0.0,0.0,1
```


# On macOS

Set up the environment

```bash
python3 -m venv venv
```

To enter the environment run

```bash
source venv/bin/activate
```

On MacOS you can choose to edit the `.env` file and add your API keys. Use a text editor to open the .env file and paste your api keys... Like this:

```bash
GROQ_API_KEY=your_groq_api_key #paste over
TODOIST_API_TOKEN=your_todoist_token #paste over

GROQ_MODEL_NAME=llama-3.3-70b-versatile 
BACKGROUND_IMAGE_PATH=graphics/background/mountain-surrounded-with-fog.jpg 
MINIMIZE_TEXT_COLOR=0.0,0.0,0.0,1
```

# On Linux

Set up the environment
(Recomended: simply copy .env.example where you name the copy .env changing it from .env.example

```bash
cp .env.example ~/.env
```

Edit the file with nono or other text editor

```bash
nano ~/.env
```

Edit the File
```bash
GROQ_API_KEY=your_groq_api_key #enter your api key for Groq
TODOIST_API_TOKEN=your_todoist_token #enter your api key for TODOIST

GROQ_MODEL_NAME=llama-3.3-70b-versatile 
BACKGROUND_IMAGE_PATH=graphics/background/mountain-surrounded-with-fog.jpg 
MINIMIZE_TEXT_COLOR=0.0,0.0,0.0,1
```

Now create the environment in Linux with 

```bash
python3 -m venv venv
```

To enter the environment run

```bash
source venv/bin/activate
```

#Do not upload the .env file after you put the api keys in. The api keys may get deactivated or worse someone can charge up a bill on you.

If changing an api key is required after setup there are premade app fields you can click on, in the setup window, by using the setup page button on the lower right of the app and paste your api keys

### Running the Application
Again, make sure the environment is activated by

```bash
source venv/bin/activate
```

#The prompt will change to have (venv) at the beginning of the line, showing you entered the venv environment. Installing your dependencies this way with an environment prevents python libraries and dependencies from conflicting with eachother,

### Step 4: Install Dependencies within (venv). Run the command:

```bash
pip install -r requirements.txt
```

## Usage after Steps 1-4

run the python command to launch the application
**Command Line:** `python Productivity.py`

#Windows
Or, on a Windows PC, you can double click the exe file labeled Productivity_App_Start.exe, after environment configuration, but only if you set up venv using defaults and the method above using defaults. If the Productivity_App_Start.exe fails for any reason, again you can launch the application in Windows command line with..

**Command Line:** `python Productivity.py`
OR
> 🔘 **Launch:** `./Productivity_App_Start.exe`


### Basic Hot key shortcut Commands Support (Windows Only)

🆕  Ctrl + N  →  Create a new task  
🔍  Ctrl + F  →  Search tasks  
✏️  Ctrl + E  →  Edit selected task  
🗑️  Delete    →  Delete selected task  
❓  F1         →  Show keyboard shortcuts


## Directory Structure

```
TooDone/
├── .env.example          # Example environment configuration -> Change this to .env
├── .gitignore            # Git ignore rules -> this file is a settings file for if you want to upload into your own repository, it will ignore the venv environment folder and .env but will upload .env.example
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
