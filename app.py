import speech_recognition as sr
import pyttsx3
import webbrowser
import os
import datetime
import subprocess
import wikipedia
import wolframalpha
import requests
import json
import time
import threading
import psutil
import pygame
import math
import sys
import google.generativeai as genai
from pygame.locals import *

# Configuration - replace with your actual API keys
API_KEYS = {
    'wolframalpha': '',
    'openweathermap': '',
    'gemini': ''  # Add your Gemini API key here
}

class JARVIS:
    def __init__(self):
        # Initialize speech engine
        self.engine = pyttsx3.init()
        voices = self.engine.getProperty('voices')
        self.engine.setProperty('voice', voices[1].id)  # Change index for different voice
        self.engine.setProperty('rate', 150)  # Speaking rate (words per minute)
        
        # Initialize recognizer with better settings
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 3000  # Adjust based on your microphone
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        
        # Microphone configuration
        self.microphone = sr.Microphone(device_index=None)
        
        # Wolfram Alpha client (for computational questions)
        self.wolfram_client = wolframalpha.Client(API_KEYS['wolframalpha'])
        
        # Gemini AI configuration
        genai.configure(api_key=API_KEYS['gemini'])
        self.gemini_model = genai.GenerativeModel('gemini-pro')
        
        # Set wake word
        self.wake_word = "jarvis"
        
        # App paths (customize these for your system)
        self.app_paths = {
            'chrome': 'C:/Program Files/Google/Chrome/Application/chrome.exe',
            'notepad': 'notepad.exe',
            'calculator': 'calc.exe',
            'spotify': 'C:/Users/Username/AppData/Roaming/Spotify/Spotify.exe',
            'word': 'WINWORD.EXE',
            'excel': 'EXCEL.exe',
            'powerpoint': 'POWERPNT.exe'
        }
        
        # Track running applications
        self.running_apps = {}
        
        # Pygame visualization setup
        self.pygame_running = True
        self.visualization_thread = threading.Thread(target=self.run_visualization)
        self.visualization_thread.daemon = True
        
        # Common responses
        self.common_responses = {
            'hi': ["Hello! How can I assist you today?", "Hi there!", "Greetings!"],
            'hello': ["Hello! How can I help you?", "Hi! What can I do for you?", "Hey there!"],
            'how are you': ["I'm functioning optimally, thank you for asking!", 
                           "I'm doing well, how about you?", 
                           "All systems are operational!"],
            'thank you': ["You're welcome!", "My pleasure!", "Always happy to help!"],
            'good morning': ["Good morning! How can I assist you today?", 
                            "Morning! Ready for a productive day?", 
                            "Top of the morning to you!"]
        }

    def run_visualization(self):
        """Run the Pygame visualization in a separate thread"""
        pygame.init()
        WIDTH, HEIGHT = 800, 800
        CENTER = (WIDTH // 2, HEIGHT // 2)
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("JARVIS Interface")
        
        # Colors
        BLACK = (0, 0, 0)
        CYAN = (0, 255, 255)
        GREEN = (0, 255, 0)
        BLUE = (0, 100, 255)
        
        # Clock
        clock = pygame.time.Clock()
        angle = 0
        pulse_alpha = 0
        pulse_direction = 1
        
        def draw_rotating_elements(surface, center, base_radius, angle):
            # Draw base circle with pulsing effect
            pulse_color = (0, int(255 * (0.7 + 0.3 * math.sin(time.time() * 3))), 255)

            pygame.draw.circle(surface, pulse_color, center, base_radius, 2)
            
            # Rotating lines with fading effect
            for i in range(0, 360, 45):
                rad = math.radians(i + angle)
                x = center[0] + base_radius * math.cos(rad)
                y = center[1] + base_radius * math.sin(rad)
                alpha = int(128 + 127 * math.sin(rad + time.time() * 2))
                color = (0, alpha, alpha)
                pygame.draw.line(surface, color, center, (x, y), 1)
            
            # Inner rotating elements
            inner_radius = base_radius // 2
            for i in range(0, 360, 90):
                rad = math.radians(i - angle * 1.5)
                x = center[0] + inner_radius * math.cos(rad)
                y = center[1] + inner_radius * math.sin(rad)
                size = 5 + int(3 * math.sin(time.time() * 4))
                pygame.draw.circle(surface, CYAN, (int(x), int(y)), size, 1)
        
        def draw_hex_grid(surface, start_x, start_y, radius, rows, cols):
            dx = radius * 1.5
            dy = math.sqrt(3) * radius

            for row in range(rows):
                for col in range(cols):
                    x = start_x + col * dx
                    y = start_y + row * dy + (col % 2) * dy / 2
                    draw_hexagon(surface, x, y, radius)
        
        def draw_hexagon(surface, x, y, radius):
            points = []
            for i in range(6):
                angle = math.radians(60 * i + time.time() * 10)
                px = x + radius * math.cos(angle)
                py = y + radius * math.sin(angle)
                points.append((px, py))
            alpha = int(50 + 50 * math.sin(time.time() * 2 + x/100 + y/100))
            color = (0, alpha, alpha)
            pygame.draw.polygon(surface, color, points, 1)
        
        def draw_status_text(surface, text, position, color=GREEN):
            font = pygame.font.SysFont('Courier New', 24)
            text_surface = font.render(text, True, color)
            
            # Add pulsing background
            s = pygame.Surface((text_surface.get_width() + 20, text_surface.get_height() + 10))
            s.set_alpha(30 + int(30 * math.sin(time.time() * 3)))
            s.fill(BLUE)
            surface.blit(s, (position[0] - 10, position[1] - 5))
            
            surface.blit(text_surface, position)
        
        def draw_system_info(surface):
            # CPU usage
            cpu_percent = psutil.cpu_percent()
            # Memory usage
            mem = psutil.virtual_memory()
            mem_percent = mem.percent
            
            info_text = [
                f"CPU: {cpu_percent}%",
                f"MEM: {mem_percent}%",
                f"TIME: {datetime.datetime.now().strftime('%H:%M:%S')}"
            ]
            
            for i, text in enumerate(info_text):
                draw_status_text(surface, text, (WIDTH - 200, 50 + i * 30))
        
        while self.pygame_running:
            clock.tick(60)
            screen.fill(BLACK)
            
            # Event check
            for event in pygame.event.get():
                if event.type == QUIT:
                    self.pygame_running = False
                    pygame.quit()
                    return
            
            # Draw elements
            draw_rotating_elements(screen, CENTER, 200, angle)
            draw_hex_grid(screen, 50, 50, 15, 15, 15)
            
            # Draw status text
            draw_status_text(screen, "JARVIS: ONLINE", (50, 50))
            draw_status_text(screen, "STATUS: LISTENING...", (50, 90))
            draw_status_text(screen, f"WAKE WORD: '{self.wake_word}'", (50, 130))
            
            # Draw system info
            draw_system_info(screen)
            
            # Update display
            pygame.display.flip()
            
            # Increment angle
            angle += 0.5
        
        pygame.quit()

    def speak(self, text, wait=True):
        """Convert text to speech"""
        print(f"JARVIS: {text}")
        self.engine.say(text)
        if wait:
            self.engine.runAndWait()

    def listen(self):
        """Listen for audio input and convert to text with error handling"""
        with self.microphone as source:
            print("\nAdjusting for ambient noise...")
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            print("Listening...")
            
            try:
                audio = self.recognizer.listen(
                    source, 
                    timeout=5,          # Wait max 5 seconds for speech to start
                    phrase_time_limit=8  # Max 8 seconds per phrase
                )
                print("Processing...")
                
                # Try multiple recognition services
                try:
                    query = self.recognizer.recognize_google(audio, language='en-in')
                    print(f"User said: {query}")
                    return query.lower()
                except sr.UnknownValueError:
                    self.speak("Sorry, I didn't catch that. Could you repeat?", wait=False)
                    return ""
                except sr.RequestError:
                    self.speak("My speech service is unavailable. Trying offline...", wait=False)
                    return self.recognizer.recognize_sphinx(audio).lower()
                    
            except sr.WaitTimeoutError:
                print("No speech detected within timeout period")
                return ""
            except Exception as e:
                print(f"Listening error: {str(e)}")
                return ""

    def process_command(self, command):
        """Process the command and execute appropriate action with better matching"""
        if not command:
            return
            
        command_lower = command.lower()
        
        # Check for common greetings first
        for phrase in self.common_responses:
            if phrase in command_lower:
                response = self.common_responses[phrase][int(time.time()) % len(self.common_responses[phrase])]
                self.speak(response)
                return
        
        # Open applications
        if any(word in command_lower for word in ['open', 'launch', 'start']):
            self.open_app(command_lower)
        
        # Close applications
        elif any(word in command_lower for word in ['close', 'exit', 'quit', 'shut down']):
            self.close_app(command_lower)
        
        # Web search
        elif any(word in command_lower for word in ['search', 'look up', 'google']):
            self.search_web(command_lower)
        
        # Time and date
        elif 'time' in command_lower and 'date' not in command_lower:
            self.get_time()
        elif 'date' in command_lower:
            self.get_date()
        
        # Notes and writing
        elif any(word in command_lower for word in ['write', 'note', 'remember']):
            self.take_note(command_lower)
        
        # File manipulation
        elif any(word in command_lower for word in ['create file', 'delete file', 'rename file', 'edit file']):
            self.manage_files(command_lower)
        
        # Calculations
        elif any(word in command_lower for word in ['calculate', 'what is', 'math']):
            self.calculate(command_lower)
        
        # Code generation
        elif any(word in command_lower for word in ['generate code', 'write code', 'create program']):
            self.generate_code(command_lower)
        
        # Weather
        elif 'weather' in command_lower:
            self.get_weather(command_lower)
        
        # Wikipedia
        elif any(word in command_lower for word in ['wikipedia', 'who is', 'what is']):
            self.search_wikipedia(command_lower)
        
        # System commands
        elif any(word in command_lower for word in ['exit jarvis', 'quit jarvis', 'goodbye', 'shut down jarvis']):
            self.speak("Goodbye! Have a great day.")
            self.pygame_running = False
            self.visualization_thread.join()
            exit()
        
        # Default response
        else:
            self.speak("I'm not sure how to handle that command. Can you try something else?")

    def open_app(self, command):
        """Open an application based on command with fuzzy matching"""
        app = None
        
        # Find which app was mentioned
        for app_name in self.app_paths:
            if app_name in command:
                app = app_name
                break
        
        if app:
            try:
                # Check if app is already running
                for proc in psutil.process_iter(['name']):
                    if proc.info['name'].lower() == os.path.basename(self.app_paths[app]).lower():
                        self.speak(f"{app} is already running")
                        return
                
                process = subprocess.Popen(self.app_paths[app])
                self.running_apps[app] = process.pid
                self.speak(f"Opening {app}")
            except Exception as e:
                self.speak(f"Sorry, I couldn't open {app}")
                print(f"Error opening app: {e}")
        else:
            mentioned_app = command.replace('open', '').replace('launch', '').replace('start', '').strip()
            self.speak(f"I don't know how to open {mentioned_app}. You can teach me by adding it to my configuration.")

    def close_app(self, command):
        """Close an application based on command"""
        app = None
        
        # Find which app was mentioned
        for app_name in self.app_paths:
            if app_name in command:
                app = app_name
                break
        
        if app:
            try:
                app_exe = os.path.basename(self.app_paths[app]).lower()
                closed = False
                
                for proc in psutil.process_iter(['name', 'pid']):
                    if proc.info['name'].lower() == app_exe:
                        proc.kill()
                        closed = True
                
                if closed:
                    if app in self.running_apps:
                        del self.running_apps[app]
                    self.speak(f"Closed {app}")
                else:
                    self.speak(f"{app} is not currently running")
            except Exception as e:
                self.speak(f"Sorry, I couldn't close {app}")
                print(f"Error closing app: {e}")
        else:
            mentioned_app = command.replace('close', '').replace('exit', '').replace('quit', '').replace('shut down', '').strip()
            self.speak(f"I don't know how to close {mentioned_app}")

    def search_web(self, command):
        """Search the web for information"""
        query = command.replace('search', '').replace('look up', '').replace('google', '').strip()
        if query:
            webbrowser.open(f"https://www.google.com/search?q={query}")
            self.speak(f"Here's what I found for {query}")
        else:
            self.speak("What would you like me to search for?")
            new_query = self.listen()
            if new_query:
                webbrowser.open(f"https://www.google.com/search?q={new_query}")

    def get_time(self):
        """Get current time"""
        now = datetime.datetime.now().strftime("%I:%M %p")
        self.speak(f"The current time is {now}")

    def get_date(self):
        """Get current date"""
        today = datetime.date.today().strftime("%A, %B %d, %Y")
        self.speak(f"Today is {today}")

    def take_note(self, command):
        """Take a note based on user input"""
        note = command.replace('write', '').replace('note', '').replace('take', '').replace('remember', '').strip()
        if note:
            with open("notes.txt", "a") as f:
                f.write(f"{datetime.datetime.now()}: {note}\n")
            self.speak("I've made a note of that")
        else:
            self.speak("What would you like me to write down?")
            new_note = self.listen()
            if new_note:
                with open("notes.txt", "a") as f:
                    f.write(f"{datetime.datetime.now()}: {new_note}\n")
                self.speak("Note saved")

    def manage_files(self, command):
        """Handle file operations like create, delete, rename"""
        if 'create file' in command:
            filename = command.replace('create file', '').strip()
            if not filename:
                self.speak("What should I name the file?")
                filename = self.listen()
                if not filename:
                    return
            
            try:
                with open(filename, 'w') as f:
                    f.write("")
                self.speak(f"Created file {filename}")
            except Exception as e:
                self.speak(f"Could not create file {filename}")
                print(f"File creation error: {e}")
        
        elif 'delete file' in command:
            filename = command.replace('delete file', '').strip()
            if not filename:
                self.speak("Which file should I delete?")
                filename = self.listen()
                if not filename:
                    return
            
            try:
                if os.path.exists(filename):
                    os.remove(filename)
                    self.speak(f"Deleted file {filename}")
                else:
                    self.speak(f"File {filename} does not exist")
            except Exception as e:
                self.speak(f"Could not delete file {filename}")
                print(f"File deletion error: {e}")
        
        elif 'rename file' in command:
            parts = command.replace('rename file', '').strip().split(' to ')
            if len(parts) < 2:
                self.speak("Please specify the current name and new name")
                return
            
            old_name = parts[0].strip()
            new_name = parts[1].strip()
            
            try:
                if os.path.exists(old_name):
                    os.rename(old_name, new_name)
                    self.speak(f"Renamed {old_name} to {new_name}")
                else:
                    self.speak(f"File {old_name} does not exist")
            except Exception as e:
                self.speak(f"Could not rename {old_name} to {new_name}")
                print(f"File rename error: {e}")
        
        elif 'edit file' in command:
            filename = command.replace('edit file', '').strip()
            if not filename:
                self.speak("Which file should I edit?")
                filename = self.listen()
                if not filename:
                    return
            
            if os.path.exists(filename):
                try:
                    subprocess.Popen(['notepad.exe', filename])
                    self.speak(f"Opening {filename} for editing")
                except Exception as e:
                    self.speak(f"Could not open {filename} for editing")
                    print(f"File edit error: {e}")
            else:
                self.speak(f"File {filename} does not exist")

    def calculate(self, command):
        """Perform calculations using Wolfram Alpha"""
        try:
            query = command.replace('calculate', '').replace('what is', '').strip()
            res = self.wolfram_client.query(query)
            answer = next(res.results).text
            self.speak(f"The answer is {answer}")
        except Exception as e:
            print(f"Calculation error: {e}")
            self.speak("I couldn't calculate that. Please try another question or check my configuration.")

    def generate_code(self, command):
        """Generate code using Gemini API"""
        try:
            prompt = command.replace('generate code', '').replace('write code', '').replace('create program', '').strip()
            if not prompt:
                self.speak("What code would you like me to generate?")
                prompt = self.listen()
                if not prompt:
                    return
            
            self.speak("Generating code, please wait...")
            
            # Use Gemini API to generate code
            response = self.gemini_model.generate_content(
                f"Generate Python code for: {prompt}. Provide only the code with no additional explanation."
            )
            
            code = response.text
            
            # Save to a file
            filename = f"generated_code_{int(time.time())}.py"
            with open(filename, 'w') as f:
                f.write(code)
            
            self.speak(f"I've generated the code and saved it as {filename}")
            self.speak("Would you like me to open the file?", wait=False)
            answer = self.listen()
            
            if answer and 'yes' in answer.lower():
                try:
                    subprocess.Popen(['notepad.exe', filename])
                    self.speak("Opening the generated code file")
                except Exception as e:
                    print(f"Error opening file: {e}")
                    self.speak("Could not open the file, but it has been saved")
        except Exception as e:
            print(f"Code generation error: {e}")
            self.speak("Sorry, I couldn't generate the code. Please try again.")

    def get_weather(self, command):
        """Get weather information"""
        location = command.replace('weather', '').replace('in', '').replace('for', '').strip()
        if not location:
            self.speak("For which location?")
            location = self.listen()
            if not location:
                return
                
        try:
            api_key = API_KEYS['openweathermap']
            base_url = "http://api.openweathermap.org/data/2.5/weather?"
            complete_url = f"{base_url}appid={api_key}&q={location}"
            response = requests.get(complete_url)
            data = response.json()
            
            if data["cod"] != "404":
                main = data["main"]
                temperature = main["temp"] - 273.15  # Convert from Kelvin to Celsius
                humidity = main["humidity"]
                weather_desc = data["weather"][0]["description"]
                
                response = (f"Weather in {location}: {weather_desc}. "
                          f"Temperature: {temperature:.1f}°C. "
                          f"Humidity: {humidity}%.")
                self.speak(response)
            else:
                self.speak("Location not found.")
        except Exception as e:
            print(f"Weather API error: {e}")
            self.speak("Sorry, I couldn't fetch the weather information.")

    def search_wikipedia(self, command):
        """Search Wikipedia for information"""
        query = command.replace('wikipedia', '').replace('who is', '').replace('what is', '').strip()
        if query:
            try:
                summary = wikipedia.summary(query, sentences=2)
                self.speak(f"According to Wikipedia: {summary}")
            except wikipedia.exceptions.DisambiguationError as e:
                self.speak(f"There are multiple options for {query}. Please be more specific.")
            except wikipedia.exceptions.PageError:
                self.speak(f"I couldn't find information about {query} on Wikipedia.")
            except Exception as e:
                print(f"Wikipedia error: {e}")
                self.speak("Sorry, I couldn't access Wikipedia right now.")
        else:
            self.speak("What would you like me to look up on Wikipedia?")

    def run(self):
        """Main loop for the assistant with better wake word handling"""
        self.speak("JARVIS initialized and ready. You can say 'JARVIS' followed by your command.")
        
        # Start the visualization thread
        self.visualization_thread.start()
        
        while True:
            try:
                command = self.listen()
                
                # Check for wake word or direct command
                if self.wake_word in command.lower():
                    processed_cmd = command.lower().replace(self.wake_word, '').strip()
                    if processed_cmd:
                        self.process_command(processed_cmd)
                elif command.strip():  # If there's any command without wake word
                    self.process_command(command)
                else:
                    time.sleep(1)  # Prevent CPU overuse when idle
                    
            except KeyboardInterrupt:
                self.speak("Shutting down by user request.")
                self.pygame_running = False
                self.visualization_thread.join()
                exit()
            except Exception as e:
                print(f"Main loop error: {e}")
                self.speak("Sorry, I encountered an error. Please try again.")
                time.sleep(1)

if __name__ == "__main__":
    assistant = JARVIS()
    assistant.run()